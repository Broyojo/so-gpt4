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
            "body": self.body,
            "title": self.title,
            "tags": self.tags,
            "answer_count": self.answer_count,
            "comment_count": self.comment_count,
            "favorite_count": self.favorite_count,
        }
