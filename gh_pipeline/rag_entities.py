"""Match entity names from unified knowledge base in retrieved text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def load_name_index(kb_path: str | Path) -> list[tuple[str, str, str]]:
    """Return (name, entity_id, bucket) sorted by name length descending."""
    data = json.loads(Path(kb_path).read_text(encoding="utf-8"))
    entries: list[tuple[str, str, str]] = []

    for bucket in ("roles", "polities", "civilizations", "religions", "organizations", "schools"):
        for entity_id, entity in (data.get(bucket) or {}).items():
            names = set(entity.get("all_names") or [])
            canonical = entity.get("canonical_name")
            if canonical:
                names.add(canonical)
            for name in names:
                name = str(name).strip()
                if len(name) >= 2:
                    entries.append((name, entity_id, bucket))

    for name, loc_id in (data.get("name_to_location_id") or {}).items():
        name = str(name).strip()
        if len(name) >= 2:
            entries.append((name, loc_id, "locations"))

    entries.sort(key=lambda x: len(x[0]), reverse=True)
    return entries


def find_entities_in_text(
    text: str,
    name_index: list[tuple[str, str, str]],
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if not text:
        return []

    found: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    occupied = [False] * len(text)

    for name, entity_id, bucket in name_index:
        if entity_id in seen_ids:
            continue
        start = 0
        while True:
            idx = text.find(name, start)
            if idx < 0:
                break
            end = idx + len(name)
            if any(occupied[idx:end]):
                start = idx + 1
                continue
            for i in range(idx, end):
                occupied[i] = True
            found.append({"name": name, "entity_id": entity_id, "entity_type": bucket})
            seen_ids.add(entity_id)
            break
        if len(found) >= limit:
            break

    return found


def find_entities_in_citations(
    citations: list[dict[str, Any]],
    kb_path: Optional[str | Path],
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if not kb_path or not Path(kb_path).exists():
        return []

    name_index = load_name_index(kb_path)
    combined = "\n".join(c.get("text", "") for c in citations)
    return find_entities_in_text(combined, name_index, limit=limit)
