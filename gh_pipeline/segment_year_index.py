"""Build paragraph-level year index from adapted_book.json."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from gh_pipeline.time_parsing import (
    ParsedYearRange,
    parse_chapter_title_years,
    parse_part_title_years,
    parse_year_from_text,
    parse_year_range_from_text,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_adapted_book(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "paragraphs" not in data:
        raise ValueError("adapted_book.json must contain paragraphs[]")
    return data


def load_book_structure(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def chapter_meta_from_structure(structure: dict[str, Any]) -> dict[int, dict[str, Any]]:
    meta: dict[int, dict[str, Any]] = {}
    for part in structure.get("parts", []):
        part_range = parse_part_title_years(part.get("title_cn", ""))
        for ch in part.get("chapters", []):
            idx = int(ch["chapter_index"])
            title_range = parse_chapter_title_years(ch.get("title_cn", ""))
            meta[idx] = {
                "chapter_index": idx,
                "title_cn": ch.get("title_cn", ""),
                "part_index": part.get("part_index"),
                "part_title_cn": part.get("title_cn", ""),
                "era": part.get("era"),
                "title_year_range": title_range,
                "part_year_range": part_range,
            }
    return meta


def iter_paragraphs(book: dict[str, Any]) -> Iterable[dict[str, Any]]:
    paragraphs = book.get("paragraphs", [])
    return sorted(
        paragraphs,
        key=lambda p: (int(p["chapter_index"]), int(p["paragraph_index"])),
    )


def segment_key(chapter_index: int, paragraph_index: int) -> str:
    return f"{chapter_index}-{paragraph_index}"


def build_segment_year_index(
    *,
    book: dict[str, Any],
    structure: dict[str, Any],
    overrides: Optional[dict[str, Any]] = None,
    version: str = "v1",
) -> dict[str, Any]:
    chapter_meta = chapter_meta_from_structure(structure)
    overrides_map: dict[str, Any] = {}
    if overrides:
        overrides_map = overrides.get("overrides", overrides)

    segments: dict[str, Any] = {}
    by_chapter: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for para in iter_paragraphs(book):
        chapter_index = int(para["chapter_index"])
        paragraph_index = int(para["paragraph_index"])
        key = segment_key(chapter_index, paragraph_index)
        text = para.get("text", "")
        raw_time = para.get("segment_start_time_raw")

        override = overrides_map.get(key)
        if override is not None:
            year = override.get("year") if isinstance(override, dict) else override
            segments[key] = {
                "chapter_index": chapter_index,
                "paragraph_index": paragraph_index,
                "segment_start_time_raw": raw_time,
                "year": int(year) if year is not None else None,
                "parse_method": "override",
                "confidence": 1.0,
            }
            by_chapter[chapter_index].append(segments[key])
            continue

        parsed = parse_year_from_text(text)
        if parsed:
            segments[key] = {
                "chapter_index": chapter_index,
                "paragraph_index": paragraph_index,
                "segment_start_time_raw": raw_time or text[:120],
                "year": parsed.year,
                "parse_method": parsed.parse_method,
                "confidence": parsed.confidence,
            }
        else:
            segments[key] = {
                "chapter_index": chapter_index,
                "paragraph_index": paragraph_index,
                "segment_start_time_raw": raw_time,
                "year": None,
                "parse_method": None,
                "confidence": 0.0,
            }
        by_chapter[chapter_index].append(segments[key])

    return {
        "version": version,
        "generated_at": now_iso(),
        "segments": segments,
    }


def chapter_year_bounds(
    chapter_index: int,
    items: list[dict[str, Any]],
    chapter_meta: dict[int, dict[str, Any]],
) -> tuple[Optional[int], Optional[int]]:
    explicit_years = [int(item["year"]) for item in items if item.get("year") is not None]
    meta = chapter_meta.get(chapter_index, {})
    title_range: Optional[ParsedYearRange] = meta.get("title_year_range")
    part_range: Optional[ParsedYearRange] = meta.get("part_year_range")

    if title_range:
        return title_range.start_year, title_range.end_year

    start: Optional[int] = None
    end: Optional[int] = None

    if part_range:
        start, end = part_range.start_year, part_range.end_year
    elif meta.get("era") == "post-1500":
        start, end = 1500, None

    if explicit_years:
        ymin, ymax = min(explicit_years), max(explicit_years)
        start = ymin if start is None else min(start, ymin)
        end = ymax if end is None else max(end, ymax)

    return start, end


def extract_chapter_bounds(
    segment_payload: dict[str, Any],
    *,
    structure: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Optional[int]], dict[str, Optional[int]]]:
    chapter_meta = chapter_meta_from_structure(structure) if structure else {}
    by_chapter: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for seg in segment_payload.get("segments", {}).values():
        chapter = int(seg["chapter_index"])
        by_chapter[chapter].append(seg)

    start_years: dict[str, Optional[int]] = {}
    end_years: dict[str, Optional[int]] = {}
    for chapter, items in sorted(by_chapter.items(), key=lambda kv: kv[0]):
        start, end = chapter_year_bounds(chapter, items, chapter_meta)
        start_years[str(chapter)] = start
        end_years[str(chapter)] = end
    return start_years, end_years


def build_chapter_year_index(
    segment_payload: dict[str, Any],
    *,
    structure: Optional[dict[str, Any]] = None,
    overrides: Optional[dict[str, Any]] = None,
    version: str = "v1",
) -> dict[str, Any]:
    chapter_meta = chapter_meta_from_structure(structure) if structure else {}
    by_chapter: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for seg in segment_payload.get("segments", {}).values():
        by_chapter[int(seg["chapter_index"])].append(seg)

    start_years: dict[str, Optional[int]] = {}
    end_years: dict[str, Optional[int]] = {}
    for chapter, items in sorted(by_chapter.items(), key=lambda kv: kv[0]):
        start, end = chapter_year_bounds(chapter, items, chapter_meta)
        start_years[str(chapter)] = start
        end_years[str(chapter)] = end

    override_map: dict[str, Any] = {}
    if overrides:
        override_map = overrides.get("chapter_overrides", overrides.get("overrides", {}))

    for chapter_key in set(start_years) | set(end_years) | set(override_map):
        chapter_index = int(chapter_key)
        override = override_map.get(chapter_key) or override_map.get(str(chapter_index))
        if not override:
            continue
        if isinstance(override, dict):
            if override.get("start_year") is not None:
                start_years[str(chapter_index)] = int(override["start_year"])
            if override.get("end_year") is not None:
                end_years[str(chapter_index)] = int(override["end_year"])
        else:
            start_years[str(chapter_index)] = int(override)

        meta = chapter_meta.get(chapter_index, {})
        title_range = meta.get("title_year_range")
        if title_range and end_years.get(str(chapter_index)) is None:
            end_years[str(chapter_index)] = title_range.end_year

    # Title-only chapters: fill from title range when paragraph parsing failed
    for chapter_index, meta in chapter_meta.items():
        key = str(chapter_index)
        title_range = meta.get("title_year_range")
        if not title_range:
            continue
        if start_years.get(key) is None:
            start_years[key] = title_range.start_year
        if end_years.get(key) is None:
            end_years[key] = title_range.end_year

    # Stable numeric order
    start_years = dict(sorted(start_years.items(), key=lambda kv: int(kv[0])))
    end_years = dict(sorted(end_years.items(), key=lambda kv: int(kv[0])))

    return {
        "version": version,
        "generated_at": now_iso(),
        "chapter_start_year": start_years,
        "chapter_end_year": end_years,
        "juan_start_year": start_years,
        "juan_end_year": end_years,
    }


def validate_segment_year_index(segment_payload: dict[str, Any]) -> list[str]:
    """Advisory checks only — global history chapters are not strictly chronological."""
    return []


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
