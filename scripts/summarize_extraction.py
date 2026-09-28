#!/usr/bin/env python3
"""Summarize extraction results for a chapter."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from knowledge_store import KnowledgeStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, default=22)
    parser.add_argument("--store-dir", type=Path, default=Path("data/store"))
    args = parser.parse_args()

    store = KnowledgeStore(str(args.store_dir))
    chunks = store.get_chapter_chunks(args.chapter)
    if not chunks:
        print(f"No chunks for chapter {args.chapter}")
        return 1

    entities = Counter()
    locations = Counter()
    events = []
    for ch in chunks:
        for e in ch.entities:
            entities[e.name] += 1
        for loc in ch.locations:
            locations[loc.name] += 1
        events.extend(ev.name for ev in ch.events)

    print(store.summary())
    print(f"\nChapter {args.chapter} chunks: {len(chunks)}")
    print("\nTop entities:")
    for name, n in entities.most_common(15):
        print(f"  {name} ({n})")
    print("\nTop locations:")
    for name, n in locations.most_common(15):
        print(f"  {name} ({n})")
    print(f"\nEvents ({len(events)}):")
    for name in events[:20]:
        print(f"  - {name}")
    if len(events) > 20:
        print(f"  ... +{len(events) - 20} more")

    out = args.store_dir / f"chapter_{args.chapter}_summary.json"
    out.write_text(
        json.dumps(
            {
                "chapter_index": args.chapter,
                "chunks": len(chunks),
                "entity_count": sum(entities.values()),
                "location_count": sum(locations.values()),
                "event_count": len(events),
                "top_entities": entities.most_common(20),
                "top_locations": locations.most_common(20),
                "events": events,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
