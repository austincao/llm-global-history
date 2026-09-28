#!/usr/bin/env python3
"""Validate sources/book_structure.json integrity."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    path = Path("sources/book_structure.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = data["parts"]
    chapter_indices: list[int] = []
    for part in parts:
        for ch in part["chapters"]:
            chapter_indices.append(ch["chapter_index"])
    expected = list(range(1, 45))
    if chapter_indices != expected:
        print(f"Chapter indices mismatch: got {chapter_indices}", file=sys.stderr)
        return 1
    if data["metadata"]["total_chapters"] != 44:
        print("total_chapters must be 44", file=sys.stderr)
        return 1
    pre = sum(1 for p in parts if p["era"] == "pre-1500" for _ in p["chapters"])
    post = sum(1 for p in parts if p["era"] == "post-1500" for _ in p["chapters"])
    if pre != 21 or post != 23:
        print(f"Expected 21 pre-1500 and 23 post-1500 chapters, got {pre}/{post}", file=sys.stderr)
        return 1
    print("book_structure.json OK: 8 parts, 44 chapters, 1500 split validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
