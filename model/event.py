from typing import List
from pydantic import BaseModel, Field, field_validator


class Event(BaseModel):
    name: str
    time: str | None = None
    location: str | None = None
    participants: List[str] = Field(default_factory=list)
    description: str
    background: str = ""
    significance: str = ""
    source: str = ""
    sentence_indexes_in_segment: List[int] = Field(default_factory=list)
    chapter_index: int = 0
    segment_index: int = 0

    @field_validator("significance", "source", "background", mode="before")
    @classmethod
    def empty_string_if_none(cls, v):
        return "" if v is None else v
