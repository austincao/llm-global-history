from typing import List
from pydantic import BaseModel, Field, field_validator


class Action(BaseModel):
    time: str | None = None
    from_roles: List[str]
    to_roles: List[str]
    action: str
    context: str
    result: str | None = None
    event_name: str | None = None
    location: str | None = None
    is_commentary: bool = False
    sentence_indexes_in_segment: List[int] = Field(default_factory=list)
    chapter_index: int = 0
    segment_index: int = 0

    @field_validator("context", "action", mode="before")
    @classmethod
    def empty_string_if_none(cls, v):
        return "" if v is None else v
