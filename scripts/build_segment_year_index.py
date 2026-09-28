#!/usr/bin/env python3
"""Build data/segment_year_index.json from adapted_book.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gh_pipeline.segment_year_index import (
    build_segment_year_index,
    load_adapted_book,
    load_book_structure,
    validate_segment_year_index,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build paragraph-level year index")
    parser.add_argument("--input", default="adapted_book.json")
    parser.add_argument("--structure", default="sources/book_structure.json")
    parser.add_argument("--output", default="data/segment_year_index.json")
    parser.add_argument("--overrides", default=None, help="Optional segment overrides JSON")
    parser.add_argument("--validate", action="store_true", help="Run advisory validation")
    parser.add_argument("--fail-on-validate", action="store_true", help="Exit 1 on validation issues")
    args = parser.parse_args()

    book = load_adapted_book(Path(args.input))
    structure = load_book_structure(Path(args.structure))
    overrides = None
    if args.overrides:
        overrides = json.loads(Path(args.overrides).read_text(encoding="utf-8"))

    payload = build_segment_year_index(book=book, structure=structure, overrides=overrides)
    write_json(Path(args.output), payload)

    parsed = sum(1 for s in payload["segments"].values() if s.get("year") is not None)
    print(f"Wrote {args.output} (segments={len(payload['segments'])}, with_year={parsed})")

    if args.validate or args.fail_on_validate:
        errors = validate_segment_year_index(payload)
        if errors:
            print(f"Validation: {len(errors)} issue(s)")
            for err in errors[:20]:
                print(f"  - {err}")
            if args.fail_on_validate:
                return 1
        else:
            print("Validation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
