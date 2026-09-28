from typing import List
from pydantic import BaseModel, Field

from model.role import Role
from model.action import Action
from model.event import Event
from model.location import Location


class EntityRelationExtraction(BaseModel):
    entities: List[Role] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    relations: List[Action] = Field(default_factory=list)
