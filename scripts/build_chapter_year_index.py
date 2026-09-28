#!/usr/bin/env python3
"""Build data/chapter_year_index.json from segment_year_index.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gh_pipeline.segment_year_index import (
    build_chapter_year_index,
    load_book_structure,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build chapter/juan year index")
    parser.add_argument("--input", default="data/segment_year_index.json")
    parser.add_argument("--structure", default="sources/book_structure.json")
    parser.add_argument("--output", default="data/chapter_year_index.json")
    parser.add_argument("--overrides", default=None, help="Optional chapter year overrides")
    args = parser.parse_args()

    segment_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    structure = load_book_structure(Path(args.structure))
    overrides = None
    if args.overrides:
        overrides = json.loads(Path(args.overrides).read_text(encoding="utf-8"))

    payload = build_chapter_year_index(
        segment_payload,
        structure=structure,
        overrides=overrides,
    )
    write_json(Path(args.output), payload)

    missing = sum(1 for y in payload["chapter_start_year"].values() if y is None)
    print(
        f"Wrote {args.output} (chapters={len(payload['chapter_start_year'])}, missing_start={missing})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
