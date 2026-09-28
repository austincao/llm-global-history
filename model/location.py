from typing import List
from pydantic import BaseModel, Field, field_validator


class Location(BaseModel):
    name: str
    alias: List[str] = Field(default_factory=list)
    type: str = ""
    description: str = ""
    modern_name: str = ""
    related_entities: List[str] = Field(default_factory=list)
    sentence_indexes_in_segment: List[int] = Field(default_factory=list)
    chapter_index: int = 0
    segment_index: int = 0

    @field_validator("type", "description", "modern_name", mode="before")
    @classmethod
    def empty_string_if_none(cls, v):
        return "" if v is None else v
