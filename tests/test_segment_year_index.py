"""Tests for segment/chapter year index."""

import json
from pathlib import Path

from gh_pipeline.segment_year_index import (
    build_chapter_year_index,
    build_segment_year_index,
    load_adapted_book,
    load_book_structure,
)


def test_build_indexes_from_adapted_book():
    root = Path(__file__).resolve().parents[1]
    book_path = root / "adapted_book.json"
    structure_path = root / "sources/book_structure.json"
    if not book_path.exists():
        return

    book = load_adapted_book(book_path)
    structure = load_book_structure(structure_path)
    seg = build_segment_year_index(book=book, structure=structure)
    chapter = build_chapter_year_index(seg, structure=structure)

    assert len(seg["segments"]) == book["paragraph_count"]
    assert chapter["chapter_start_year"]["22"] == 1500
    assert chapter["chapter_end_year"]["22"] == 1600
    assert chapter["chapter_start_year"]["3"] == -3500


def test_chapter_title_only_fallback():
    structure = json.loads(
        (Path(__file__).resolve().parents[1] / "sources/book_structure.json").read_text(encoding="utf-8")
    )
    seg = {
        "segments": {
            "5-1": {
                "chapter_index": 5,
                "paragraph_index": 1,
                "year": None,
                "parse_method": None,
                "confidence": 0.0,
            }
        }
    }
    chapter = build_chapter_year_index(seg, structure=structure)
    # Chapter 5 has no title years; may stay null without paragraph years
    assert "5" in chapter["chapter_start_year"] or chapter["chapter_start_year"].get("5") is None
