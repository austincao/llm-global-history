#!/usr/bin/env python3
"""Merge location geocoding cache into unified knowledge base."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_coords(coords: Any) -> tuple[float, float] | None:
    if coords is None:
        return None
    if not isinstance(coords, (list, tuple)) or len(coords) != 2:
        return None
    try:
        return float(coords[0]), float(coords[1])
    except (TypeError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", default="data/unified_knowledge.json")
    parser.add_argument("--geocoding", default="data/location_geocoding.json")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    kb_path = Path(args.kb)
    geo_path = Path(args.geocoding)
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    geo = json.loads(geo_path.read_text(encoding="utf-8"))

    updated = 0
    for loc_id, entry in (geo.get("locations") or {}).items():
        if loc_id not in kb.get("locations", {}):
            continue
        if entry.get("needs_review"):
            continue
        coords = normalize_coords(entry.get("coordinates"))
        if not coords:
            continue
        kb["locations"][loc_id]["coordinates"] = [coords[0], coords[1]]
        kb["locations"][loc_id]["updated_at"] = now_iso()
        updated += 1

    out_path = Path(args.out) if args.out else kb_path
    out_path.write_text(json.dumps(kb, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Merged coordinates into {out_path} ({updated} locations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
