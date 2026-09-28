from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Role(BaseModel):
    entity_type: Optional[
        Literal["person", "polity", "school", "organization", "civilization", "religion"]
    ] = Field(default=None)
    name: str
    alias: list[str] = Field(default_factory=list)
    original_description_in_book: str = ""
    description: str = ""
    power: str | None = None
    sentence_indexes_in_segment: List[int] = Field(default_factory=list)
    chapter_index: int = 0
    segment_index: int = 0

    @field_validator("original_description_in_book", "description", mode="before")
    @classmethod
    def empty_string_if_none(cls, v):
        return "" if v is None else v
