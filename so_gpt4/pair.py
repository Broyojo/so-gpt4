from dataclasses import dataclass

from .post import Post


@dataclass
class Pair:
    question: Post
    answers: list[Post]
    gpt_answer: str

    def to_json(self, config):
        return {
            "question": self.question.to_json(config),
            "answers": [answer.to_json(config) for answer in self.answers],
            "gpt_answer": self.gpt_answer,
        }

    def from_json(self, config, json):
        self.question = Post.empty_post().from_json(config, json["question"])
        self.answers = [
            Post.empty_post().from_json(config, answer) for answer in json["answers"]
        ]
        self.gpt_answer = json["gpt_answer"]
        return self
