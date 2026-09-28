#!/usr/bin/env python3
"""Verify chapter extraction completeness and list missing chunks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 5


def load_book(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_chunks(book: dict, chapter: int, chunk_size: int) -> int:
    n = sum(1 for p in book["paragraphs"] if p["chapter_index"] == chapter)
    return (n + chunk_size - 1) // chunk_size if n else 0


def chunk_starts(book: dict, chapter: int, chunk_size: int) -> list[int]:
    n = sum(1 for p in book["paragraphs"] if p["chapter_index"] == chapter)
    return list(range(0, n, chunk_size))


def verify_chapter(store_dir: Path, book: dict, chapter: int, chunk_size: int) -> dict:
    expected = expected_chunks(book, chapter, chunk_size)
    path = store_dir / f"chapter_{chapter}.json"
    if not path.exists():
        return {
            "chapter": chapter,
            "ok": False,
            "expected": expected,
            "found": 0,
            "missing_starts": chunk_starts(book, chapter, chunk_size),
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    present = {
        int(k.split("-")[-1])
        for k, v in data.items()
        if isinstance(v, dict) and k.count("-") == 2
    }
    all_starts = chunk_starts(book, chapter, chunk_size)
    missing = [s for s in all_starts if s not in present]
    return {
        "chapter": chapter,
        "ok": len(missing) == 0 and expected > 0,
        "expected": expected,
        "found": len(present),
        "missing_starts": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify extraction completeness")
    parser.add_argument("--start", type=int, default=22)
    parser.add_argument("--end", type=int, default=44)
    parser.add_argument("--adapted-book", type=Path, default=Path("adapted_book.json"))
    parser.add_argument("--store-dir", type=Path, default=Path("data/store"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    book = load_book(args.adapted_book)
    results = [
        verify_chapter(args.store_dir, book, ch, CHUNK_SIZE)
        for ch in range(args.start, args.end + 1)
    ]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        ok = 0
        for r in results:
            status = "OK" if r["ok"] else "INCOMPLETE"
            if r["ok"]:
                ok += 1
            extra = ""
            if r["missing_starts"]:
                extra = f" missing={r['missing_starts'][:5]}{'...' if len(r['missing_starts'])>5 else ''}"
            print(f"Ch{r['chapter']:2d} [{status}] {r['found']}/{r['expected']}{extra}")
        print(f"\n{ok}/{len(results)} chapters complete")

    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
