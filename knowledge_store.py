"""Persistent storage for chapter-level LLM extractions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from model.action import Action
from model.event import Event
from model.location import Location
from model.role import Role


class ChunkExtraction(BaseModel):
    chapter_index: int
    segment_index: int
    chunk_start_index: int
    chunk_end_index: int
    chapter_title: str = ""
    segment_start_time: str = ""
    source_sentences: list[str] = Field(default_factory=list)
    entities: list[Role] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    relations: list[Action] = Field(default_factory=list)
    extracted_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    model_name: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class KnowledgeStore:
    def __init__(self, store_dir: str = "data/store"):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.store_dir / "metadata.json"
        self.metadata = self._load_metadata()
        self._processed_keys: set[str] = set()
        self._init_processed_keys()
        self._current_chapter_index = -1
        self._current_chapter_data: dict[str, Any] = {}

    def _load_metadata(self) -> dict[str, Any]:
        if self.metadata_path.exists():
            return json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "progress": {"total_chunks_processed": 0},
        }

    def _save_metadata(self) -> None:
        self.metadata_path.write_text(
            json.dumps(self.metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _chapter_file_path(self, chapter_index: int) -> Path:
        return self.store_dir / f"chapter_{chapter_index}.json"

    def _load_chapter_data(self, chapter_index: int) -> dict[str, Any]:
        path = self._chapter_file_path(chapter_index)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def _save_chapter_data(self, chapter_index: int, data: dict[str, Any]) -> None:
        self._chapter_file_path(chapter_index).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _iter_chapter_data_files(self) -> list[Path]:
        return [
            p
            for p in self.store_dir.glob("chapter_*.json")
            if not p.name.endswith("_summary.json")
        ]

    def _init_processed_keys(self) -> None:
        for file_path in self._iter_chapter_data_files():
            data = json.loads(file_path.read_text(encoding="utf-8"))
            for key, value in data.items():
                if isinstance(value, dict):
                    self._processed_keys.add(key)

    @staticmethod
    def _make_key(chapter_index: int, segment_index: int, chunk_start: int) -> str:
        return f"{chapter_index}-{segment_index}-{chunk_start}"

    def save_chunk(self, extraction: ChunkExtraction) -> None:
        if self._current_chapter_index != extraction.chapter_index:
            self._current_chapter_index = extraction.chapter_index
            self._current_chapter_data = self._load_chapter_data(extraction.chapter_index)

        key = self._make_key(
            extraction.chapter_index, extraction.segment_index, extraction.chunk_start_index
        )
        self._current_chapter_data[key] = extraction.model_dump()
        self._save_chapter_data(extraction.chapter_index, self._current_chapter_data)
        self._processed_keys.add(key)
        self.metadata["progress"]["total_chunks_processed"] = len(self._processed_keys)
        self._save_metadata()

    def has_chunk(self, chapter_index: int, segment_index: int, chunk_start: int) -> bool:
        return self._make_key(chapter_index, segment_index, chunk_start) in self._processed_keys

    def get_chapter_chunks(self, chapter_index: int) -> list[ChunkExtraction]:
        data = self._load_chapter_data(chapter_index)
        return sorted(
            [ChunkExtraction(**v) for v in data.values()],
            key=lambda x: x.chunk_start_index,
        )

    def summary(self) -> str:
        total_entities = total_locations = total_events = total_relations = 0
        for file_path in self._iter_chapter_data_files():
            data = json.loads(file_path.read_text(encoding="utf-8"))
            for chunk in data.values():
                if not isinstance(chunk, dict):
                    continue
                total_entities += len(chunk.get("entities", []))
                total_locations += len(chunk.get("locations", []))
                total_events += len(chunk.get("events", []))
                total_relations += len(chunk.get("relations", []))
        n = self.metadata["progress"]["total_chunks_processed"]
        return (
            f"Knowledge Store: {n} chunks | "
            f"entities={total_entities} locations={total_locations} "
            f"events={total_events} relations={total_relations}"
        )
