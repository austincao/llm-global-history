#!/usr/bin/env python3
"""Parse a user-provided EPUB into adapted_book.json (local only, not committed)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


CHAPTER_HEADING = re.compile(
    r"^第([一二三四五六七八九十百零\d]{1,4})章[\s　]*(.*)$"
)

CN_DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_numeral_to_int(raw: str) -> int | None:
    if raw.isdigit():
        return int(raw)
    total = 0
    num = 0
    for ch in raw:
        if ch == "十":
            num = 1 if num == 0 else num
            total += num * 10
            num = 0
        elif ch == "百":
            num = 1 if num == 0 else num
            total += num * 100
            num = 0
        elif ch in CN_DIGITS:
            num = CN_DIGITS[ch]
        else:
            return None
    return total + num


def parse_chapter_heading(line: str) -> tuple[int, str] | None:
    match = CHAPTER_HEADING.match(line.strip())
    if not match:
        return None
    chapter_index = cn_numeral_to_int(match.group(1))
    if chapter_index is None or not (1 <= chapter_index <= 44):
        return None
    title = match.group(2).strip() or line.strip()
    return chapter_index, title


def html_to_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return [ln.strip() for ln in soup.get_text("\n").splitlines() if ln.strip()]


def load_structure(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def chapter_title_map(structure: dict) -> dict[int, dict]:
    mapping: dict[int, dict] = {}
    for part in structure["parts"]:
        for ch in part["chapters"]:
            mapping[ch["chapter_index"]] = {
                "part_index": part["part_index"],
                "part_title_cn": part["title_cn"],
                "era": part["era"],
                "chapter_index": ch["chapter_index"],
                "title_cn": ch["title_cn"],
            }
    return mapping


def chapter_meta(chapter_map: dict[int, dict], chapter_index: int, fallback_title: str) -> dict:
    meta = chapter_map.get(chapter_index)
    if meta is not None:
        return dict(meta)
    return {
        "part_index": 0,
        "part_title_cn": "未知编",
        "era": "unknown",
        "chapter_index": chapter_index,
        "title_cn": fallback_title,
    }


def parse_epub(epub_path: Path, structure: dict) -> list[dict]:
    book = epub.read_epub(str(epub_path))
    chapter_map = chapter_title_map(structure)
    paragraphs: list[dict] = []
    seen_chapters: set[int] = set()

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        lines = html_to_lines(item.get_content().decode("utf-8", errors="ignore"))
        if not lines:
            continue
        heading = parse_chapter_heading(lines[0])
        if heading is None:
            continue
        chapter_index, fallback_title = heading
        if chapter_index in seen_chapters:
            continue
        seen_chapters.add(chapter_index)
        current_meta = chapter_meta(chapter_map, chapter_index, fallback_title)
        for paragraph_index, line in enumerate(lines[1:], start=1):
            paragraphs.append(
                {
                    **current_meta,
                    "paragraph_index": paragraph_index,
                    "text": line,
                    "segment_start_time_raw": None,
                    "source_document": item.get_name(),
                }
            )
    return paragraphs


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Stavrianos EPUB into adapted_book.json")
    parser.add_argument("--input", required=True, type=Path, help="Path to EPUB in sources/private/")
    parser.add_argument(
        "--structure",
        type=Path,
        default=Path("sources/book_structure.json"),
        help="Book TOC structure JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("adapted_book.json"),
        help="Output path (gitignored by default)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(
            f"Input not found: {args.input}\n"
            "Place your legally obtained EPUB in sources/private/ — see sources/private/README.md"
        )
    if args.input.suffix.lower() != ".epub":
        raise SystemExit("MVP only supports EPUB. PDF/TXT coming later.")

    structure = load_structure(args.structure)
    paragraphs = parse_epub(args.input, structure)
    if not paragraphs:
        raise SystemExit(
            "No paragraphs extracted. EPUB chapter headings may not match '第N章' pattern.\n"
            "Try a different export or extend ingest_book.py for your file layout."
        )

    chapters_found = sorted({p["chapter_index"] for p in paragraphs})
    payload = {
        "version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(args.input.name),
        "book": structure["book"],
        "paragraph_count": len(paragraphs),
        "chapters_found": chapters_found,
        "paragraphs": paragraphs,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {len(paragraphs)} paragraphs across {len(chapters_found)} chapters -> {args.output}"
    )
    if len(chapters_found) != 44:
        print(f"WARNING: expected 44 chapters, found {len(chapters_found)}: {chapters_found}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
