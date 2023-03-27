import json
import os
import random
import xml.etree.ElementTree as ET
from datetime import datetime
from multiprocessing import Pool

import markdown
import openai
from alive_progress import alive_it

from .config import Config
from .pair import Pair
from .post import Post


class StackOveflowDatabase:
    def __init__(self, config: Config):
        self.config = config
        self.pairs: dict[str, Pair] = {}

        if os.path.exists(self.config.raw_pairs_path):
            with open(self.config.raw_pairs_path, "r") as f:
                content = f.read()
                if content != "":
                    print("Found existing raw_pairs.json, loading...")
                    data = json.loads(content)

                    for key, value in data.items():
                        self.pairs[key] = Pair(
                            question=None, answers=[], gpt_answer=None
                        ).from_json(config=self.config, json=value)

    def read_posts(self):
        for _, post in alive_it(
            ET.iterparse(self.config.posts_path),
            title=f"Reading posts from {self.config.posts_path}...",
            total=self.config.total,
        ):

            def bind(val, f):
                if val != None:
                    return f(val)

            format_date = lambda t: datetime.strptime(t, self.config.time_format)

            if post.tag == "row":
                yield Post(
                    id=post.attrib.get("Id"),
                    post_type_id=bind(post.attrib.get("PostTypeId"), int),
                    score=bind(post.attrib.get("Score"), int),
                    accepted_answer_id=post.attrib.get("AcceptedAnswerId"),
                    parent_id=post.attrib.get("ParentId"),
                    creation_date=bind(post.attrib.get("CreationDate"), format_date),
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

    def get_pairs(self):
        if len(self.pairs) > 0:
            print("Found existing pairs, skipping...")
            return self

        for post in self.read_posts():
            if (
                post.creation_date > self.config.cutoff_date
                and post.post_type_id == 1
                and post.answer_count > 0
                and "<a" not in post.body
                and "</a>" not in post.body
                and "<img" not in post.body
            ):
                self.pairs[post.id] = Pair(question=post, answers=[], gpt_answer="")

        for post in self.read_posts():
            if (
                post.creation_date > self.config.cutoff_date
                and post.post_type_id == 2
                and "<a" not in post.body
                and "</a>" not in post.body
                and "<img" not in post.body
                and post.parent_id in self.pairs
            ):
                self.pairs[post.parent_id].answers.append(post)

        filtered_pairs = {}

        for pair in alive_it(self.pairs, title="Pruning questions with no answers..."):
            if len(self.pairs[pair].answers) > 0:
                filtered_pairs[pair] = self.pairs[pair]

        self.pairs = filtered_pairs

        with open(self.config.raw_pairs_path, "w") as f:
            formatted_pars = {}
            for pair in self.pairs:
                formatted_pars[pair] = self.pairs[pair].to_json(self.config)
            json.dump(formatted_pars, f)

        return self

    def write_json(self, path=""):
        formatted_pairs = []

        for pair in alive_it(self.pairs.values(), title="Formatting pairs..."):
            formatted_pairs.append(pair.to_json(self.config))

        print("Writing pairs...")

        with open(self.config.pairs_path if path == "" else path, "w") as f:
            json.dump(formatted_pairs, f)

    def filter_by_tags_mut(self, tags):
        filtered_pairs = {}
        for pair in alive_it(self.pairs, title=f"Filtering pairs by tags {tags}..."):
            if all([tag in self.pairs[pair].question.tags for tag in tags]):
                filtered_pairs[pair] = self.pairs[pair]
        print("Found {} pairs with tags {}".format(len(filtered_pairs), tags))
        self.pairs = filtered_pairs
        return self

    def filter_by_tags(self, tags):
        filtered_pairs = {}
        for pair in alive_it(self.pairs, title=f"Filtering pairs by tags {tags}..."):
            if all([tag in self.pairs[pair].question.tags for tag in tags]):
                filtered_pairs[pair] = self.pairs[pair]
        print("Found {} pairs with tags {}".format(len(filtered_pairs), tags))
        return filtered_pairs

    def random_sample(self, k):
        print(f"Taking random sample of {k} pairs...")
        k = min(k, len(self.pairs))
        self.pairs = dict(random.sample(list(self.pairs.items()), k=k))
        return self

    def answer_with_gpt_single_threaded(self):
        for pair in self.pairs:
            title = self.pairs[pair].question.title
            body = self.pairs[pair].question.body

            question = f"{title}\n\n{body}"

            gpt_answer = ""
            try:
                for chunk in openai.ChatCompletion.create(
                    model=self.config.gpt_model,
                    messages=[
                        {
                            "role": "system",
                            "content": self.config.gpt_prompt,
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
                quit(f"oh no! something bad happened: {e}")

            self.pairs[pair].gpt_answer = gpt_answer

        return self

    def answer(self, pair: Pair):
        title = pair.question.title
        body = pair.question.body

        question = f"{title}\n\n{body}"

        gpt_answer = ""
        try:
            for chunk in openai.ChatCompletion.create(
                model=self.config.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": self.config.gpt_prompt,
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
            quit(f"oh no! something bad happened: {e}, {pair}")

        gpt_answer = markdown.markdown(gpt_answer)

        pair.gpt_answer = gpt_answer

        return (pair.question.id, gpt_answer)

    def answer_with_gpt_multithreaded(self):
        with Pool(self.config.threads) as p:
            answers = []
            for answer in alive_it(
                p.imap_unordered(
                    self.answer,
                    self.pairs.values(),
                    # chunksize=len(self.pairs) // self.config.threads,
                ),
                total=len(self.pairs),
                title="Generating answers with GPT-4...",
            ):
                answers.append(answer)
            # answers = p.map(self.answer, self.pairs.values())

            for id, answer in answers:
                self.pairs[id].gpt_answer = answer

        return self
