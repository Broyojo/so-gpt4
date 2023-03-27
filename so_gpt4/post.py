from dataclasses import dataclass
from datetime import datetime

from .config import Config


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

    def to_json(self, config: Config):
        return {
            "id": self.id,
            "post_type_id": self.post_type_id,
            "score": self.score,
            "accepted_answer_id": self.accepted_answer_id,
            "parent_id": self.parent_id,
            "creation_date": self.creation_date.strftime(config.time_format),
            "view_count": self.view_count,
            "body": self.body.strip(),
            "title": self.title,
            "tags": self.tags,
            "answer_count": self.answer_count,
            "comment_count": self.comment_count,
            "favorite_count": self.favorite_count,
        }

    def from_json(self, config: Config, json):
        self.id = json["id"]
        self.post_type_id = json["post_type_id"]
        self.score = json["score"]
        self.accepted_answer_id = json["accepted_answer_id"]
        self.parent_id = json["parent_id"]
        self.creation_date = datetime.strptime(
            json["creation_date"], config.time_format
        )
        self.view_count = json["view_count"]
        self.body = json["body"]
        self.title = json["title"]
        self.tags = json["tags"]
        self.answer_count = json["answer_count"]
        self.comment_count = json["comment_count"]
        self.favorite_count = json["favorite_count"]
        return self

    def empty_post() -> "Post":
        return Post(
            id="",
            post_type_id=0,
            score=0,
            accepted_answer_id="",
            parent_id="",
            creation_date=datetime.now(),
            view_count=0,
            body="",
            title="",
            tags=[],
            answer_count=0,
            comment_count=0,
            favorite_count=0,
        )
