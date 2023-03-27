from dataclasses import dataclass
from datetime import datetime


@dataclass
class Config:
    cutoff_date: datetime
    posts_path: str
    total: int
    time_format: str
    pairs_path: str
    raw_pairs_path: str
    gpt_prompt: str
    gpt_model: str
    threads: int
