import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

from alive_progress import alive_it


@dataclass
class Post:
    id: int
    post_type_id: int
    accepted_answer_id: int
    parent_id: int
    creation_date: datetime
    score: int
    view_count: int
    body: str
    owner_user_id: int
    owner_display_name: str
    last_editor_user_id: int
    last_activity_date: datetime
    last_edit_date: datetime
    title: str
    tags: list[str]
    answer_count: int
    comment_count: int
    favorite_count: int


def read_posts(path, total):
    for _, post in alive_it(
        ET.iterparse(path),
        title=f"Reading posts from {path}...",
        total=total,
    ):

        def get_int(key):
            return int(i) if (i := post.attrib.get(key)) else None

        def get_str(key):
            return post.attrib.get(key)

        def get_datetime(key):
            return datetime.fromisoformat(d) if (d := post.attrib.get(key)) else None

        def get_tags(key):
            return (
                ts.replace(">", " ").replace("<", " ").split()
                if (ts := post.attrib.get(key))
                else None
            )

        if post.tag == "row":
            post_type_id = int(post.attrib.get("PostTypeId"))
            if post_type_id == 1 or post_type_id == 2:
                yield Post(
                    id=get_int("Id"),
                    post_type_id=post_type_id,
                    accepted_answer_id=get_int("AcceptedAnswerId"),
                    parent_id=get_int("ParentId"),
                    creation_date=get_datetime("CreationDate"),
                    score=get_int("Score"),
                    view_count=get_int("ViewCount"),
                    body=get_str("Body"),
                    owner_user_id=get_int("OwnerUserId"),
                    owner_display_name=get_str("OwnerDisplayName"),
                    last_editor_user_id=get_int("LastEditorUserId"),
                    last_activity_date=get_datetime("LastActivityDate"),
                    last_edit_date=get_datetime("LastEditDate"),
                    title=get_str("Title"),
                    tags=get_tags("Tags"),
                    answer_count=get_int("AnswerCount"),
                    comment_count=get_int("CommentCount"),
                    favorite_count=get_int("FavoriteCount"),
                )

        post.clear()  # must clear to avoid memory leak
