"""Tests for book structure and ingest helpers."""

from __future__ import annotations

import json
from pathlib import Path


def test_book_structure_has_44_chapters():
    path = Path("sources/book_structure.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    chapters = [ch for part in data["parts"] for ch in part["chapters"]]
    assert len(chapters) == 44
    assert [c["chapter_index"] for c in chapters] == list(range(1, 45))


def test_era_split_at_chapter_22():
    path = Path("sources/book_structure.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    ch22 = next(
        ch
        for part in data["parts"]
        for ch in part["chapters"]
        if ch["chapter_index"] == 22
    )
    part6 = next(p for p in data["parts"] if p["part_index"] == 6)
    assert part6["era"] == "post-1500"
    assert ch22["title_cn"].startswith("西欧的扩张")
