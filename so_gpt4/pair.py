from dataclasses import dataclass

from .post import Post


@dataclass
class Pair:
    question: Post
    answers: list[Post]
    gpt_answer: str
