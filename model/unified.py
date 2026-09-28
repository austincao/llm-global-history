"""Unified knowledge base models for global history."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EntityOccurrence(BaseModel):
    chapter_index: int = 0
    segment_index: int = 0
    chunk_index: int = 0
    sentence_indexes: list[int] = Field(default_factory=list)
    original_description: str = ""
    source_sentence: str = ""


class UnifiedEntity(BaseModel):
    id: str
    entity_type: str
    canonical_name: str
    all_names: set[str] = Field(default_factory=set)
    description: str = ""
    original_descriptions: list[str] = Field(default_factory=list)
    powers: list[str] = Field(default_factory=list)
    primary_power: Optional[str] = None
    first_appearance_chapter: int = 0
    last_appearance_chapter: int = 0
    occurrences: list[EntityOccurrence] = Field(default_factory=list)
    total_mentions: int = 0
    chapters_appeared: set[int] = Field(default_factory=set)
    related_entities: set[str] = Field(default_factory=set)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UnifiedLocation(BaseModel):
    id: str
    canonical_name: str
    all_names: set[str] = Field(default_factory=set)
    location_type: str = ""
    description: str = ""
    modern_name: str = ""
    coordinates: Optional[tuple[float, float]] = None
    associated_entities: set[str] = Field(default_factory=set)
    associated_events: list[str] = Field(default_factory=list)
    occurrences: list[EntityOccurrence] = Field(default_factory=list)
    total_mentions: int = 0
    chapters_appeared: set[int] = Field(default_factory=set)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UnifiedEvent(BaseModel):
    id: str
    name: str
    canonical_name: str
    all_names: set[str] = Field(default_factory=set)
    time: Optional[str] = None
    time_start: Optional[int] = None
    location: Optional[str] = None
    participants: list[str] = Field(default_factory=list)
    description: str = ""
    background: str = ""
    significance: str = ""
    source_chapters: set[int] = Field(default_factory=set)
    occurrences: list[EntityOccurrence] = Field(default_factory=list)
    total_mentions: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UnifiedRelation(BaseModel):
    id: str
    from_entity: str
    to_entity: str
    relation_type: str
    description: str = ""
    context: str = ""
    result: Optional[str] = None
    event_name: Optional[str] = None
    location: Optional[str] = None
    time: Optional[str] = None
    first_interaction_year: Optional[int] = None
    last_interaction_year: Optional[int] = None
    is_commentary: bool = False
    source_chapters: set[int] = Field(default_factory=set)
    action_count: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UnifiedKnowledgeBase(BaseModel):
    version: str = "v1"
    source_chapters: list[int] = Field(default_factory=list)
    roles: dict[str, UnifiedEntity] = Field(default_factory=dict)
    polities: dict[str, UnifiedEntity] = Field(default_factory=dict)
    civilizations: dict[str, UnifiedEntity] = Field(default_factory=dict)
    religions: dict[str, UnifiedEntity] = Field(default_factory=dict)
    organizations: dict[str, UnifiedEntity] = Field(default_factory=dict)
    schools: dict[str, UnifiedEntity] = Field(default_factory=dict)
    locations: dict[str, UnifiedLocation] = Field(default_factory=dict)
    events: dict[str, UnifiedEvent] = Field(default_factory=dict)
    relations: dict[str, UnifiedRelation] = Field(default_factory=dict)
    name_to_entity_id: dict[str, str] = Field(default_factory=dict)
    name_to_location_id: dict[str, str] = Field(default_factory=dict)
    total_roles: int = 0
    total_polities: int = 0
    total_civilizations: int = 0
    total_religions: int = 0
    total_organizations: int = 0
    total_schools: int = 0
    total_locations: int = 0
    total_events: int = 0
    total_relations: int = 0
