#!/usr/bin/env python3
"""Geocode unified locations via Nominatim (OpenStreetMap) with persistent cache."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "global-history-geocoder/0.1 (local research; contact: local)"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clean_paren_suffix(name: str) -> str:
    return re.sub(r"（[^）]*）|\([^)]*\)", "", name).strip()


def build_query(loc: dict, hints: dict) -> str:
    overrides = hints.get("query_overrides", {})
    canonical = loc.get("canonical_name", "")
    if canonical in overrides:
        return overrides[canonical]
    modern = clean_paren_suffix(loc.get("modern_name", ""))
    if modern and modern != canonical:
        if modern in overrides:
            return overrides[modern]
        return modern
    for alias in loc.get("all_names", []):
        alias = clean_paren_suffix(alias)
        if alias in overrides:
            return overrides[alias]
    return canonical


def is_suspicious_match(query: str, display_name: str) -> bool:
    """Reject common false positives when Chinese queries hit domestic OSM data."""
    china_markers = ("中国", "China", "臺灣", "台湾", "安徽省", "合肥市", "西藏")
    if any(m in display_name for m in china_markers):
        if "China" not in query and "中国" not in query and "Macau" not in query and "Guangzhou" not in query:
            return True
    return False


def nominatim_search(query: str, *, sleep: float) -> dict[str, Any] | None:
    params = urlencode({"q": query, "format": "json", "limit": 1, "accept-language": "en"})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
    time.sleep(sleep)
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data:
        return None
    item = data[0]
    return {
        "coordinates": [float(item["lon"]), float(item["lat"])],
        "display_name": item.get("display_name", ""),
        "osm_type": item.get("osm_type"),
        "osm_id": item.get("osm_id"),
        "importance": float(item.get("importance", 0)),
    }


def geocode_location(loc: dict, hints: dict, *, sleep: float, offline: bool) -> dict:
    canonical = loc["canonical_name"]
    known = hints.get("known_coordinates", {})
    if canonical in known:
        return {
            "location_id": loc["id"],
            "canonical_name": canonical,
            "query": canonical,
            "coordinates": known[canonical],
            "confidence": 0.95,
            "source": "known",
            "evidence": "static known coordinate",
            "needs_review": False,
            "updated_at": now_iso(),
        }

    query = build_query(loc, hints)
    if offline:
        return {
            "location_id": loc["id"],
            "canonical_name": canonical,
            "query": query,
            "coordinates": None,
            "confidence": 0.0,
            "source": "offline",
            "evidence": "offline mode",
            "needs_review": True,
            "updated_at": now_iso(),
        }

    try:
        result = nominatim_search(query, sleep=sleep)
    except Exception as exc:
        return {
            "location_id": loc["id"],
            "canonical_name": canonical,
            "query": query,
            "coordinates": None,
            "confidence": 0.0,
            "source": "nominatim",
            "evidence": f"error: {exc}",
            "needs_review": True,
            "updated_at": now_iso(),
        }

    if not result:
        return {
            "location_id": loc["id"],
            "canonical_name": canonical,
            "query": query,
            "coordinates": None,
            "confidence": 0.0,
            "source": "nominatim",
            "evidence": "no result",
            "needs_review": True,
            "updated_at": now_iso(),
        }

    evidence = result.get("display_name", "")
    if is_suspicious_match(query, evidence):
        return {
            "location_id": loc["id"],
            "canonical_name": canonical,
            "query": query,
            "coordinates": None,
            "confidence": 0.0,
            "source": "nominatim",
            "evidence": f"rejected suspicious match: {evidence}",
            "needs_review": True,
            "updated_at": now_iso(),
        }

    importance = result.get("importance", 0)
    needs_review = importance < 0.25
    return {
        "location_id": loc["id"],
        "canonical_name": canonical,
        "query": query,
        "coordinates": result["coordinates"],
        "confidence": min(0.95, 0.5 + importance),
        "source": "nominatim",
        "evidence": result.get("display_name", ""),
        "needs_review": needs_review,
        "updated_at": now_iso(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Geocode locations with Nominatim")
    parser.add_argument("--kb", type=Path, default=Path("data/unified_knowledge.json"))
    parser.add_argument("--hints", type=Path, default=Path("data/location_geocode_hints.json"))
    parser.add_argument("--output", type=Path, default=Path("data/location_geocoding.json"))
    parser.add_argument("--sleep", type=float, default=1.1, help="Seconds between API calls")
    parser.add_argument("--offline", action="store_true", help="Only use known_coordinates")
    parser.add_argument("--force", action="store_true", help="Re-geocode all entries")
    args = parser.parse_args()

    if not args.kb.exists():
        raise SystemExit(f"Missing {args.kb}")

    kb = load_json(args.kb)
    hints = load_json(args.hints) if args.hints.exists() else {"known_coordinates": {}, "query_overrides": {}}

    cache: dict[str, Any] = {"version": "v1", "provider": "nominatim", "generated_at": now_iso(), "locations": {}}
    if args.output.exists() and not args.force:
        cache = load_json(args.output)

    locations = kb.get("locations", {})
    updated = 0
    for loc_id, loc in locations.items():
        if not args.force and loc_id in cache.get("locations", {}):
            existing = cache["locations"][loc_id]
            if existing.get("coordinates") and not existing.get("needs_review"):
                continue
        entry = geocode_location(loc, hints, sleep=args.sleep, offline=args.offline)
        cache.setdefault("locations", {})[loc_id] = entry
        updated += 1
        status = "ok" if entry.get("coordinates") else "miss"
        print(f"[{status}] {entry['canonical_name']} -> {entry.get('coordinates')}")

    cache["generated_at"] = now_iso()
    save_json(args.output, cache)

    ok = sum(1 for e in cache["locations"].values() if e.get("coordinates") and not e.get("needs_review"))
    review = sum(1 for e in cache["locations"].values() if e.get("needs_review"))
    print(f"Wrote {args.output} (updated={updated}, ok={ok}, needs_review={review}, total={len(cache['locations'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
