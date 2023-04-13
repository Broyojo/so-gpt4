from dataclasses import dataclass
from datetime import datetime

import jsonpickle

from post import Post, read_posts


@dataclass
class Pair:
    question: Post
    answers: list[Post]


def has_images_or_links(content):
    return "<a" in content or "</a>" in content or "<img" in content


def extract_pairs(path, cutoff_date, total):
    pairs: dict[str, Pair] = {}

    for post in read_posts(path, total):
        if (
            post.creation_date > cutoff_date
            and post.post_type_id == 1
            and post.answer_count > 0
            and not has_images_or_links(post.body)
        ):
            pairs[post.id] = Pair(question=post, answers=[])

    for post in read_posts(path, total):
        if post.post_type_id == 2 and post.parent_id in pairs:
            pairs[post.parent_id].answers.append(post)

    new_pairs = {}

    for id, pair in pairs.items():
        if len(pair.answers) > 0:
            earliest_answer = min(pair.answers, key=lambda a: a.creation_date)
            if not has_images_or_links(earliest_answer.body):
                new_pairs[id] = Pair(question=pair.question, answers=[earliest_answer])

    return new_pairs


if __name__ == "__main__":
    pairs = extract_pairs("data/cooking/Posts.xml", datetime(2021, 9, 30), 88_706)

    with open("pairs/cooking.json", "w") as f:
        f.write(jsonpickle.encode(pairs))
