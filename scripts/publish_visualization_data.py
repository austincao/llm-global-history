#!/usr/bin/env python3
"""Publish unified_knowledge.json for the React visualization (zizhitongjian-compatible schema)."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def chapter_to_juan(chapter_index: int) -> int:
    """Frontend uses juan_* field names; we map chapter_index 1:1."""
    return chapter_index


def map_occurrence(occ: dict) -> dict:
    return {
        "juan_index": chapter_to_juan(occ.get("chapter_index", 0)),
        "segment_index": occ.get("segment_index", 1),
        "chunk_index": occ.get("chunk_index", 0),
        "sentence_indexes": occ.get("sentence_indexes", []),
        "original_description": occ.get("original_description", ""),
        "source_sentence": occ.get("source_sentence", ""),
    }


def map_entity_as_role(entity: dict, *, as_polity: bool = False) -> dict:
    chapters = sorted(entity.get("chapters_appeared", []))
    juans = [chapter_to_juan(c) for c in chapters]
    return {
        "id": entity["id"],
        "canonical_name": entity["canonical_name"],
        "all_names": sorted(entity.get("all_names", [])),
        "description": entity.get("description", ""),
        "original_descriptions": entity.get("original_descriptions", []),
        "powers": entity.get("powers", []),
        "primary_power": entity.get("primary_power") or (entity["canonical_name"] if as_polity else None),
        "first_appearance_juan": chapter_to_juan(entity.get("first_appearance_chapter", 0)),
        "last_appearance_juan": chapter_to_juan(entity.get("last_appearance_chapter", 0)),
        "active_period": None,
        "occurrences": [map_occurrence(o) for o in entity.get("occurrences", [])],
        "total_mentions": entity.get("total_mentions", 0),
        "juans_appeared": juans,
        "related_entities": sorted(entity.get("related_entities", [])),
        "created_at": entity.get("created_at", ""),
        "updated_at": entity.get("updated_at", ""),
    }


def map_location(loc: dict) -> dict:
    chapters = sorted(loc.get("chapters_appeared", []))
    return {
        "id": loc["id"],
        "canonical_name": loc["canonical_name"],
        "all_names": sorted(loc.get("all_names", [])),
        "location_type": loc.get("location_type", ""),
        "description": loc.get("description", ""),
        "modern_name": loc.get("modern_name", ""),
        "coordinates": loc.get("coordinates"),
        "associated_entities": sorted(loc.get("associated_entities", [])),
        "associated_events": loc.get("associated_events", []),
        "occurrences": [map_occurrence(o) for o in loc.get("occurrences", [])],
        "total_mentions": loc.get("total_mentions", 0),
        "juans_appeared": [chapter_to_juan(c) for c in chapters],
        "created_at": loc.get("created_at", ""),
        "updated_at": loc.get("updated_at", ""),
    }


def map_event(evt: dict) -> dict:
    chapters = sorted(evt.get("source_chapters", []))
    juans = [chapter_to_juan(c) for c in chapters]
    return {
        "id": evt["id"],
        "name": evt.get("name", evt.get("canonical_name", "")),
        "time": evt.get("time"),
        "time_start": evt.get("time_start"),
        "time_end": evt.get("time_start"),
        "imputed_time_start": evt.get("time_start"),
        "imputed_time_end": evt.get("time_start"),
        "location": evt.get("location"),
        "participants": evt.get("participants", []),
        "description": evt.get("description", ""),
        "background": evt.get("background", ""),
        "significance": evt.get("significance", ""),
        "source_juans": juans,
        "source_segments": [],
        "action_count": evt.get("total_mentions", 1),
        "created_at": evt.get("created_at", ""),
        "updated_at": evt.get("updated_at", ""),
    }


def map_relation(rel: dict) -> dict:
    chapters = sorted(rel.get("source_chapters", []))
    ctx = rel.get("context", "")
    return {
        "id": rel["id"],
        "from_entity": rel["from_entity"],
        "to_entity": rel["to_entity"],
        "action_types": [rel.get("relation_type", rel.get("description", "关系"))],
        "primary_action": rel.get("relation_type", rel.get("description", "关系")),
        "interaction_count": rel.get("action_count", 1),
        "first_interaction_time": rel.get("time"),
        "last_interaction_time": rel.get("time"),
        "first_interaction_year": rel.get("first_interaction_year"),
        "last_interaction_year": rel.get("last_interaction_year"),
        "contexts": [ctx] if ctx else [],
        "source_juans": [chapter_to_juan(c) for c in chapters],
        "created_at": rel.get("created_at", ""),
        "updated_at": rel.get("updated_at", ""),
    }


def transform_kb(raw: dict) -> dict:
    roles: dict[str, dict] = {}
    name_to_role_id: dict[str, str] = {}

    for entity in raw.get("roles", {}).values():
        role = map_entity_as_role(entity)
        roles[role["id"]] = role
        for name in role["all_names"]:
            name_to_role_id[name] = role["id"]
        name_to_role_id[role["canonical_name"]] = role["id"]

    polities: dict[str, dict] = {}
    name_to_polity_id: dict[str, str] = {}
    for entity in raw.get("polities", {}).values():
        polity = map_entity_as_role(entity, as_polity=True)
        polities[polity["id"]] = {
            k: polity[k]
            for k in (
                "id", "canonical_name", "all_names", "description",
                "original_descriptions", "occurrences", "total_mentions",
                "juans_appeared", "created_at", "updated_at",
            )
        }
        # Polities also appear as network nodes (merged into roles for graph)
        roles[polity["id"]] = polity
        for name in polity["all_names"]:
            name_to_role_id[name] = polity["id"]
        name_to_polity_id[polity["canonical_name"]] = polity["id"]
        name_to_polity_id[polity["id"]] = polity["id"]

    for bucket in ("civilizations", "religions", "organizations", "schools"):
        for entity in raw.get(bucket, {}).values():
            role = map_entity_as_role(entity)
            roles[role["id"]] = role
            for name in role["all_names"]:
                name_to_role_id[name] = role["id"]

    locations = {lid: map_location(loc) for lid, loc in raw.get("locations", {}).items()}
    name_to_location_id = {}
    for loc in locations.values():
        for name in loc["all_names"]:
            name_to_location_id[name] = loc["id"]
        name_to_location_id[loc["canonical_name"]] = loc["id"]

    events = {eid: map_event(evt) for eid, evt in raw.get("events", {}).items()}
    relations = {rid: map_relation(rel) for rid, rel in raw.get("relations", {}).items()}

    power_to_roles: dict[str, list[str]] = defaultdict(list)
    for role in roles.values():
        if role.get("primary_power") and role["primary_power"] != role["canonical_name"]:
            power_to_roles[role["primary_power"]].append(role["id"])

    juan_to_roles: dict[int, list[str]] = defaultdict(list)
    juan_to_polities: dict[int, list[str]] = defaultdict(list)
    juan_to_events: dict[int, list[str]] = defaultdict(list)

    for role in roles.values():
        for j in role["juans_appeared"]:
            juan_to_roles[j].append(role["id"])
    for polity in polities.values():
        for j in polity["juans_appeared"]:
            juan_to_polities[j].append(polity["id"])
    for evt in events.values():
        for j in evt["source_juans"]:
            juan_to_events[j].append(evt["id"])

    chapters = sorted(raw.get("source_chapters", []))

    return {
        "roles": roles,
        "locations": locations,
        "events": events,
        "relations": relations,
        "polities": polities,
        "organizations": {},
        "schools": {},
        "name_to_role_id": name_to_role_id,
        "name_to_location_id": name_to_location_id,
        "name_to_polity_id": name_to_polity_id,
        "name_to_organization_id": {},
        "name_to_school_id": {},
        "power_to_roles": dict(power_to_roles),
        "juan_to_roles": {str(k): v for k, v in juan_to_roles.items()},
        "juan_to_polities": {str(k): v for k, v in juan_to_polities.items()},
        "juan_to_events": {str(k): v for k, v in juan_to_events.items()},
        "juan_to_organizations": {},
        "juan_to_schools": {},
        "total_roles": len([r for r in roles.values() if r["id"] in raw.get("roles", {})]),
        "total_locations": len(locations),
        "total_events": len(events),
        "total_relations": len(relations),
        "total_polities": len(polities),
        "total_organizations": 0,
        "total_schools": 0,
        "juans_processed": [chapter_to_juan(c) for c in chapters],
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "_meta": {
            "source": "global-history",
            "chapters": chapters,
            "chapter_titles": {
                "22": "西欧的扩张：伊比利亚阶段（1500—1600年）",
            },
        },
    }


def build_chapter_year_index(chapters: list[int]) -> dict:
    """Load real chapter year index, or fall back to minimal stub."""
    index_path = PROJECT_ROOT / "data/chapter_year_index.json"
    if index_path.exists():
        data = json.loads(index_path.read_text(encoding="utf-8"))
        if chapters:
            keys = {str(c) for c in chapters}
            data["chapter_start_year"] = {
                k: v for k, v in data.get("chapter_start_year", {}).items() if k in keys
            }
            data["chapter_end_year"] = {
                k: v for k, v in data.get("chapter_end_year", {}).items() if k in keys
            }
            data["juan_start_year"] = data["chapter_start_year"]
            data["juan_end_year"] = data.get("chapter_end_year", {})
        return data

    juan_start_year = {str(c): 1500 for c in chapters}
    return {
        "version": "v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chapter_start_year": juan_start_year,
        "chapter_end_year": juan_start_year,
        "juan_start_year": juan_start_year,
        "juan_end_year": juan_start_year,
        "note": "stub: run scripts/build_year_index.py",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish visualization runtime JSON")
    parser.add_argument("--input", type=Path, default=Path("data/unified_knowledge.json"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("visualization/public/data"),
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Missing {args.input}. Run entity_resolution.py first.")

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    viz_kb = transform_kb(raw)
    chapters = raw.get("source_chapters", [22])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    kb_path = args.output_dir / "unified_knowledge.json"
    year_path = args.output_dir / "juan_year_index.json"

    kb_path.write_text(json.dumps(viz_kb, ensure_ascii=False, indent=2), encoding="utf-8")
    year_path.write_text(
        json.dumps(build_chapter_year_index(chapters), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Published {kb_path}")
    print(f"  roles(nodes)={len(viz_kb['roles'])} events={viz_kb['total_events']} relations={viz_kb['total_relations']}")
    print(f"Published {year_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
