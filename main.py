import concurrent.futures
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from json import JSONDecoder, JSONEncoder
from multiprocessing import Pool
from typing import Generator

import markdown
import openai
from alive_progress import alive_it

"""
Need to be able to keep the database in memory and apply operations to it
"""

from old.so_gpt4 import Pair


@dataclass
class Post:
    id: str
    post_type_id: int
    score: int
    accepted_answer_id: str
    parent_id: str
    creation_date: datetime
    view_count: int
    body: str
    title: str
    tags: list[str]
    answer_count: int
    comment_count: int
    favorite_count: int


@dataclass
class Pair:
    question: Post
    answers: list[Post]
    gpt_answer: str

    def has_tags(self, tags: list[str]):
        for tag in tags:
            if tag.lower() not in self.question.tags:
                return False
        return True


class DatabaseEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return o.__dict__


class DatabaseDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.dict_to_object, *args, **kwargs)

    def dict_to_object(self, d):
        if "question" in d:
            return Pair(
                question=Post(**d["question"]),
                answers=[Post(**answer) for answer in d["answers"]],
                gpt_answer=d["gpt_answer"],
            )
        return d


def read_posts(posts_path: str, total: int) -> Generator[Post, None, None]:
    for _, post in alive_it(
        ET.iterparse(posts_path),
        title=f"Reading posts from {posts_path}...",
        total=total,
    ):
        # monad moment
        def bind(val, f):
            if val != None:
                return f(val)

        if post.tag == "row":
            post_type_id = int(post.attrib.get("PostTypeId"))
            if post_type_id == 1 or post_type_id == 2:
                yield Post(
                    id=post.attrib.get("Id"),
                    post_type_id=post_type_id,
                    score=bind(post.attrib.get("Score"), int),
                    accepted_answer_id=post.attrib.get("AcceptedAnswerId"),
                    parent_id=post.attrib.get("ParentId"),
                    creation_date=bind(
                        post.attrib.get("CreationDate"), datetime.fromisoformat
                    ),
                    view_count=bind(post.attrib.get("ViewCount"), int),
                    body=post.attrib.get("Body"),
                    title=post.attrib.get("Title"),
                    tags=bind(
                        post.attrib.get("Tags"),
                        lambda t: t.replace(">", " ").replace("<", " ").split(),
                    ),
                    answer_count=bind(post.attrib.get("AnswerCount"), int),
                    comment_count=bind(post.attrib.get("CommentCount"), int),
                    favorite_count=bind(post.attrib.get("FavoriteCount"), int),
                )

        post.clear()  # must clear to avoid memory leak


def answer_with_gpt(model_name: str, prompt: str, pair: Pair) -> Pair:
    gpt_answer = ""
    question = f"{pair.question.title}\n{pair.question.body}"
    try:
        for chunk in openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            stream=True,
        ):
            chunk = chunk["choices"][0]["delta"]
            if "content" in chunk:
                gpt_answer += chunk["content"]
                # print(chunk["content"], end="", flush=True)
    except openai.InvalidRequestError as e:
        quit(f"oh no! something bad happened: {e}, {question}")

    return Pair(pair.question, pair.answers, markdown.markdown(gpt_answer))


class Database:
    def __init__(self, pairs=None) -> None:
        if pairs is None:
            pairs = {}
        self.pairs: dict[str, Pair] = pairs

    @classmethod
    def load_from_json(self, path: str) -> "Database":
        db = self()
        if os.path.exists(path):
            with open(path, "r") as f:
                db.pairs = json.load(f, cls=DatabaseDecoder)
        return db

    @classmethod
    def load_from_posts(
        self,
        posts_path: str,
        total: int,
        cutoff_date: datetime,
    ) -> "Database":
        db = self()

        cached_posts = []

        for post in read_posts(posts_path, total):
            cached_posts.append(post)
            if (
                post.creation_date > cutoff_date
                and post.post_type_id == 1
                and post.answer_count > 0
                and "<a" not in post.body
                and "</a>" not in post.body
                and "<img" not in post.body
            ):
                db.pairs[post.id] = Pair(question=post, answers=[], gpt_answer="")

        for post in alive_it(cached_posts, title="Reading answers..."):
            if (
                post.creation_date > cutoff_date
                and post.post_type_id == 2
                and "<a" not in post.body
                and "</a>" not in post.body
                and "<img" not in post.body
                and post.parent_id in db.pairs
            ):
                db.pairs[post.parent_id].answers.append(post)

        return db.filter(
            lambda pair: len(pair.answers) > 0,
            title="Filtering questions with at least 1 answer...",
        )

    def add_pair(self, pair: Pair) -> "Database":
        if pair.question.id in self.pairs:
            raise KeyError(f"Pair {pair.question.id} already exists")
        self.pairs[pair.question.id] = pair
        return self

    def pfilter(
        self, fn: callable, num_threads: int = 1, title: str = "Filtering database..."
    ) -> "Database":
        new_db = Database()
        args_list = [pair for pair in self.pairs.values()]

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(fn, pair): pair for pair in args_list}

            for future in alive_it(
                concurrent.futures.as_completed(futures),
                total=len(self.pairs),
                title=title,
            ):
                if future.result():  # Check if the future's result is True
                    original_pair = futures[
                        future
                    ]  # Get the original pair using the future as the key
                    new_db.add_pair(
                        original_pair
                    )  # Add the original pair to the new database

        print("Filtered database to", len(new_db.pairs), "pairs")
        return new_db

    def filter(self, fn: callable, title: str = "Filtering database...") -> "Database":
        new_db = Database()
        for pair in alive_it(self.pairs.values(), title=title):
            if fn(pair):
                new_db.add_pair(pair)
        return new_db

    def filter_by_tags(self, tags: list[str]) -> "Database":
        return self.filter(
            lambda pair: pair.has_tags(tags),
            title=f"Filtering by tags {tags}",
        )

    def pmap(
        self, fn: callable, num_threads: int = 1, title: str = "Mapping database..."
    ) -> "Database":
        new_db = Database()
        args_list = [pair for pair in self.pairs.values()]

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(fn, args) for args in args_list]

            for future in alive_it(
                concurrent.futures.as_completed(futures),
                total=len(self.pairs),
                title=title,
            ):
                pair = future.result()
                new_db.add_pair(pair)

        return new_db

    def map(
        self,
        fn: callable,
        title: str = "Mapping database...",
    ) -> "Database":
        new_db = Database()
        args_list = [pair for pair in self.pairs.values()]

        for pair in alive_it(args_list, title=title):
            new_db.add_pair(fn(pair))

        return new_db

    def save(self, path: str, overwrite=False) -> "Database":
        if not overwrite and os.path.exists(path):
            with open(path, "r") as f:
                if f.read() != "":
                    raise ValueError(f"File {path} is not empty")
                    # path = path.replace(".json", "_new.json")
        print("Saving pairs to", path)
        with open(path, "w") as f:
            json.dump(self.pairs, f, cls=DatabaseEncoder)
        return self

    def make_gpt_answers(self, model_name: str, num_threads: int) -> "Database":
        return self.pmap(
            lambda pair: answer_with_gpt(
                model_name=model_name,
                prompt="you are a helpful AI assistant who helps to answer Stack Overflow questions on the Stack Overflow website. You are given a question and you must answer it.",
                pair=pair,
            ),
            num_threads=num_threads,
            title="Making GPT answers...",
        )


db = (
    Database.load_from_posts(
        posts_path="data/cooking/Posts.xml",
        total=88706,
        cutoff_date=datetime(2021, 9, 30),
    )
    .filter_by_tags(["bread"])
    .make_gpt_answers(model_name="gpt-3.5-turbo", num_threads=16)
    .save("pairs.json", overwrite=True)
)
