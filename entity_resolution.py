"""Entity resolution for global history extractions."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

from model.action import Action
from model.event import Event
from model.location import Location
from model.role import Role
from model.unified import (
    EntityOccurrence,
    UnifiedEntity,
    UnifiedEvent,
    UnifiedKnowledgeBase,
    UnifiedLocation,
    UnifiedRelation,
)

POLITY_NAMES = {
    "西班牙", "葡萄牙", "荷兰", "英国", "法国", "奥斯曼帝国", "阿兹特克帝国",
    "印加帝国", "墨西哥", "巴西", "俄国", "俄罗斯", "中国", "日本", "印度",
    "Spain", "Portugal", "Netherlands", "England", "France", "Ottoman Empire",
}

RELIGION_NAMES = {"伊斯兰教", "基督教", "天主教", "新教", "犹太教", "Islam", "Christianity"}

CIVILIZATION_NAMES = {"欧洲", "西方", "伊斯兰世界", "美洲", "亚洲", "Africa", "Europe"}

BLOCKED_ALIASES = {
    "国王", "女王", "皇帝", "教皇", "君主", "君王", "the King", "King",
    "探险家", "航海家", "评论者", "战无不胜的君王们",
    "您", "他", "她", "我", "此人", "其人",
}

GENERIC_REGIONS = {"欧洲", "亚洲", "美洲", "非洲", "西方", "东方", "世界"}


def slug_id(name: str) -> str:
    return re.sub(r"\s+", "_", name.strip())


def normalize_event_name(name: str) -> str:
    n = name.strip()
    replacements = {
        "哥伦布发现美洲": "哥伦布首航发现美洲",
        "哥伦布首次航行": "哥伦布首航发现美洲",
        "哥伦布第一次航行": "哥伦布首航发现美洲",
        "哥伦布首次西航": "哥伦布首航发现美洲",
    }
    return replacements.get(n, n)


def load_segment_year_index(path: str | Path) -> dict[str, int]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    mapping: dict[str, int] = {}
    for key, seg in (data.get("segments") or {}).items():
        year = seg.get("year")
        if year is not None:
            mapping[key] = int(year)
    return mapping


def load_chapter_year_bounds(path: str | Path) -> dict[int, tuple[Optional[int], Optional[int]]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    bounds: dict[int, tuple[Optional[int], Optional[int]]] = {}
    starts = data.get("chapter_start_year") or data.get("juan_start_year") or {}
    ends = data.get("chapter_end_year") or data.get("juan_end_year") or {}
    for key in set(starts) | set(ends):
        bounds[int(key)] = (starts.get(key), ends.get(key))
    return bounds


def resolve_year_from_segment(
    chapter_index: int,
    paragraph_index: int,
    segment_years: dict[str, int],
    chapter_bounds: dict[int, tuple[Optional[int], Optional[int]]],
) -> Optional[int]:
    key = f"{chapter_index}-{paragraph_index}"
    if key in segment_years:
        return segment_years[key]
    start, _ = chapter_bounds.get(chapter_index, (None, None))
    return start


def parse_year_from_text(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"前\s*(\d{1,4})\s*年", text)
    if m:
        return -int(m.group(1))
    m = re.search(r"(\d{3,4})\s*年", text)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{4})\s*[—\-–]\s*(\d{4})", text)
    if m:
        return int(m.group(1))
    return None


class EntityResolver:
    MAX_GROUP_SIZE = 12

    def __init__(
        self,
        *,
        segment_years: Optional[dict[str, int]] = None,
        chapter_bounds: Optional[dict[int, tuple[Optional[int], Optional[int]]]] = None,
    ) -> None:
        self.segment_years = segment_years or {}
        self.chapter_bounds = chapter_bounds or {}
        self.parent: dict[str, str] = {}
        self.group_size: dict[str, int] = defaultdict(lambda: 1)
        self.entity_buckets: dict[str, dict[str, list[tuple[Role, EntityOccurrence]]]] = {
            "person": defaultdict(list),
            "polity": defaultdict(list),
            "civilization": defaultdict(list),
            "religion": defaultdict(list),
            "organization": defaultdict(list),
            "school": defaultdict(list),
        }
        self.location_occurrences: dict[str, list[tuple[Location, EntityOccurrence]]] = defaultdict(list)
        self.event_occurrences: dict[str, list[tuple[Event, EntityOccurrence]]] = defaultdict(list)
        self.relations: list[Action] = []
        self.chapters_seen: set[int] = set()

    def _find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self._find(self.parent[x])
        return self.parent[x]

    def _union(self, x: str, y: str) -> bool:
        px, py = self._find(x), self._find(y)
        if px == py:
            return True
        new_size = self.group_size[px] + self.group_size[py]
        if new_size > self.MAX_GROUP_SIZE:
            return False
        if len(px) <= len(py):
            self.parent[py] = px
            self.group_size[px] = new_size
        else:
            self.parent[px] = py
            self.group_size[py] = new_size
        return True

    def _classify_entity_type(self, role: Role) -> str:
        explicit = role.entity_type or "person"
        name = role.name.strip()
        if explicit in self.entity_buckets:
            if explicit == "person" and name in POLITY_NAMES:
                return "polity"
            if explicit == "person" and name in RELIGION_NAMES:
                return "religion"
            if explicit == "person" and name in CIVILIZATION_NAMES:
                return "civilization"
            if explicit == "location":
                return "location"
            return explicit
        if name in POLITY_NAMES or name.endswith("帝国") or name.endswith("王国"):
            return "polity"
        if name in RELIGION_NAMES:
            return "religion"
        if name in CIVILIZATION_NAMES:
            return "civilization"
        return "person"

    def _valid_alias(self, name: str, alias: str) -> bool:
        alias = alias.strip()
        if not alias or alias in BLOCKED_ALIASES:
            return False
        if alias in POLITY_NAMES and name not in POLITY_NAMES:
            return False
        return True

    def add_role(
        self,
        role: Role,
        chapter_index: int,
        segment_index: int,
        chunk_index: int,
        source_sentence: str = "",
    ) -> None:
        occurrence = EntityOccurrence(
            chapter_index=chapter_index,
            segment_index=segment_index,
            chunk_index=chunk_index,
            sentence_indexes=role.sentence_indexes_in_segment,
            original_description=role.original_description_in_book,
            source_sentence=source_sentence,
        )
        entity_type = self._classify_entity_type(role)
        if entity_type == "location":
            loc = Location(
                name=role.name,
                alias=list(role.alias),
                type="地区",
                description=role.description,
                modern_name="",
                related_entities=[],
                sentence_indexes_in_segment=role.sentence_indexes_in_segment,
                chapter_index=chapter_index,
                segment_index=segment_index,
            )
            self.add_location(loc, chapter_index, segment_index, chunk_index)
            return

        bucket = self.entity_buckets[entity_type]
        name = role.name.strip()
        if name in BLOCKED_ALIASES:
            return
        bucket[name].append((role, occurrence))
        for alias in role.alias:
            if self._valid_alias(name, alias):
                self._union(name, alias.strip())

    def add_location(
        self,
        location: Location,
        chapter_index: int,
        segment_index: int,
        chunk_index: int,
    ) -> None:
        if location.name.strip() in GENERIC_REGIONS:
            return
        occurrence = EntityOccurrence(
            chapter_index=chapter_index,
            segment_index=segment_index,
            chunk_index=chunk_index,
            sentence_indexes=location.sentence_indexes_in_segment,
            original_description=location.description,
        )
        name = location.name.strip()
        self.location_occurrences[name].append((location, occurrence))

    def add_event(self, event: Event, chapter_index: int, segment_index: int, chunk_index: int) -> None:
        occurrence = EntityOccurrence(
            chapter_index=chapter_index,
            segment_index=segment_index,
            chunk_index=chunk_index,
            sentence_indexes=event.sentence_indexes_in_segment,
            original_description=event.description,
        )
        key = normalize_event_name(event.name)
        self.event_occurrences[key].append((event, occurrence))

    def add_relation(self, relation: Action, chapter_index: int) -> None:
        relation.chapter_index = chapter_index
        self.relations.append(relation)

    def _merge_entity_group(
        self,
        entity_type: str,
        names: set[str],
        bucket: dict[str, list[tuple[Role, EntityOccurrence]]],
    ) -> UnifiedEntity:
        all_roles: list[tuple[Role, EntityOccurrence]] = []
        for name in names:
            all_roles.extend(bucket.get(name, []))

        canonical = max(names, key=lambda n: len(bucket.get(n, [])))
        descriptions = [r.description for r, _ in all_roles if r.description]
        originals = list({r.original_description_in_book for r, _ in all_roles if r.original_description_in_book})
        powers = [r.power for r, _ in all_roles if r.power]
        chapters = {occ.chapter_index for _, occ in all_roles}
        occurrences = [occ for _, occ in all_roles]

        return UnifiedEntity(
            id=slug_id(canonical),
            entity_type=entity_type,
            canonical_name=canonical,
            all_names=set(names),
            description=max(descriptions, key=len) if descriptions else "",
            original_descriptions=originals,
            powers=list(dict.fromkeys(powers)),
            primary_power=powers[0] if powers else None,
            first_appearance_chapter=min(chapters) if chapters else 0,
            last_appearance_chapter=max(chapters) if chapters else 0,
            occurrences=occurrences,
            total_mentions=len(occurrences),
            chapters_appeared=chapters,
        )

    def _build_entity_maps(self) -> tuple[dict[str, UnifiedEntity], ...]:
        outputs: dict[str, dict[str, UnifiedEntity]] = {
            k: {} for k in self.entity_buckets
        }
        name_to_id: dict[str, str] = {}

        for entity_type, bucket in self.entity_buckets.items():
            groups: dict[str, set[str]] = defaultdict(set)
            for name in bucket:
                root = self._find(name)
                groups[root].add(name)

            for names in groups.values():
                if not names:
                    continue
                unified = self._merge_entity_group(entity_type, names, bucket)
                outputs[entity_type][unified.id] = unified
                for n in unified.all_names:
                    name_to_id[n] = unified.id
        return (
            outputs["person"],
            outputs["polity"],
            outputs["civilization"],
            outputs["religion"],
            outputs["organization"],
            outputs["school"],
            name_to_id,
        )

    def _build_locations(self) -> tuple[dict[str, UnifiedLocation], dict[str, str]]:
        loc_parent: dict[str, str] = {}

        def loc_find(x: str) -> str:
            if x not in loc_parent:
                loc_parent[x] = x
            if loc_parent[x] != x:
                loc_parent[x] = loc_find(loc_parent[x])
            return loc_parent[x]

        for name in self.location_occurrences:
            loc_find(f"loc:{name}")

        alias_to_canonical: dict[str, str] = {}
        for name, entries in self.location_occurrences.items():
            for loc, _ in entries:
                for alias in loc.alias:
                    alias = alias.strip()
                    if alias and alias not in BLOCKED_ALIASES:
                        alias_to_canonical[alias] = name

        for alias, canonical_name in alias_to_canonical.items():
            if alias in self.location_occurrences:
                a = loc_find(f"loc:{alias}")
                b = loc_find(f"loc:{canonical_name}")
                if a != b:
                    loc_parent[b] = a

        groups: dict[str, set[str]] = defaultdict(set)
        for name in self.location_occurrences:
            root = loc_find(f"loc:{name}")
            groups[root].add(name)

        locations: dict[str, UnifiedLocation] = {}
        name_to_location_id: dict[str, str] = {}
        for names in groups.values():
            entries: list[tuple[Location, EntityOccurrence]] = []
            for name in names:
                entries.extend(self.location_occurrences[name])
            canonical = max(names, key=lambda n: len(self.location_occurrences[n]))
            all_names: set[str] = set(names)
            for loc, _ in entries:
                all_names.update(loc.alias)
            descriptions = [loc.description for loc, _ in entries if loc.description]
            modern = next((loc.modern_name for loc, _ in entries if loc.modern_name), "")
            loc_type = next((loc.type for loc, _ in entries if loc.type), "")
            related = set()
            for loc, _ in entries:
                related.update(loc.related_entities)
            chapters = {occ.chapter_index for _, occ in entries}
            unified = UnifiedLocation(
                id=slug_id(canonical),
                canonical_name=canonical,
                all_names=all_names,
                location_type=loc_type,
                description=max(descriptions, key=len) if descriptions else "",
                modern_name=modern,
                associated_entities=related,
                occurrences=[occ for _, occ in entries],
                total_mentions=len(entries),
                chapters_appeared=chapters,
            )
            locations[unified.id] = unified
            for n in all_names:
                name_to_location_id[n] = unified.id
        return locations, name_to_location_id

    def _build_events(self, name_to_entity_id: dict[str, str]) -> dict[str, UnifiedEvent]:
        events: dict[str, UnifiedEvent] = {}
        for key, entries in self.event_occurrences.items():
            descriptions = [e.description for e, _ in entries if e.description]
            backgrounds = [e.background for e, _ in entries if e.background]
            significances = [e.significance for e, _ in entries if e.significance]
            participants: list[str] = []
            for e, _ in entries:
                participants.extend(e.participants)
            participants = list(dict.fromkeys(participants))
            times = [e.time for e, _ in entries if e.time]
            locations = [e.location for e, _ in entries if e.location]
            chapters = {occ.chapter_index for _, occ in entries}
            time_start = parse_year_from_text(times[0] if times else None)
            if time_start is None:
                for _, occ in entries:
                    paragraph_index = (occ.chunk_index or 0) + 1
                    time_start = resolve_year_from_segment(
                        occ.chapter_index,
                        paragraph_index,
                        self.segment_years,
                        self.chapter_bounds,
                    )
                    if time_start is not None:
                        break
            event_id = slug_id(key)
            events[event_id] = UnifiedEvent(
                id=event_id,
                name=key,
                canonical_name=key,
                all_names={e.name for e, _ in entries},
                time=times[0] if times else None,
                time_start=time_start,
                location=locations[0] if locations else None,
                participants=participants,
                description=max(descriptions, key=len) if descriptions else key,
                background=max(backgrounds, key=len) if backgrounds else "",
                significance=max(significances, key=len) if significances else "",
                source_chapters=chapters,
                occurrences=[occ for _, occ in entries],
                total_mentions=len(entries),
            )
        return events

    def _resolve_endpoint(self, name: str, name_to_entity_id: dict[str, str]) -> str:
        return name_to_entity_id.get(name, name)

    def _build_relations(self, name_to_entity_id: dict[str, str]) -> dict[str, UnifiedRelation]:
        grouped: dict[str, list[Action]] = defaultdict(list)
        for rel in self.relations:
            if not rel.from_roles or not rel.to_roles:
                continue
            from_name = self._resolve_endpoint(rel.from_roles[0], name_to_entity_id)
            to_name = self._resolve_endpoint(rel.to_roles[0], name_to_entity_id)
            if from_name in BLOCKED_ALIASES or to_name in BLOCKED_ALIASES:
                continue
            pair_key = f"{from_name}|{to_name}|{rel.action[:40]}"
            grouped[pair_key].append(rel)

        relations: dict[str, UnifiedRelation] = {}
        for pair_key, actions in grouped.items():
            from_name, to_name, _ = pair_key.split("|", 2)
            years = [parse_year_from_text(a.time) for a in actions]
            years = [y for y in years if y is not None]
            rel_id = slug_id(pair_key)
            relations[rel_id] = UnifiedRelation(
                id=rel_id,
                from_entity=from_name,
                to_entity=to_name,
                relation_type=actions[0].action,
                description=actions[0].action,
                context=max((a.context for a in actions if a.context), key=len, default=""),
                result=next((a.result for a in actions if a.result), None),
                event_name=next((a.event_name for a in actions if a.event_name), None),
                location=next((a.location for a in actions if a.location), None),
                time=next((a.time for a in actions if a.time), None),
                first_interaction_year=min(years) if years else None,
                last_interaction_year=max(years) if years else None,
                is_commentary=any(a.is_commentary for a in actions),
                source_chapters={a.chapter_index for a in actions},
                action_count=len(actions),
            )
        return relations

    def build_knowledge_base(self) -> UnifiedKnowledgeBase:
        roles, polities, civilizations, religions, organizations, schools, name_to_entity_id = (
            self._build_entity_maps()
        )
        locations, name_to_location_id = self._build_locations()
        events = self._build_events(name_to_entity_id)
        relations = self._build_relations(name_to_entity_id)

        for rel in relations.values():
            if rel.from_entity in name_to_entity_id:
                ent = (
                    roles.get(name_to_entity_id[rel.from_entity])
                    or polities.get(name_to_entity_id[rel.from_entity])
                )
                if ent:
                    ent.related_entities.add(rel.to_entity)
            if rel.to_entity in name_to_entity_id:
                ent = (
                    roles.get(name_to_entity_id[rel.to_entity])
                    or polities.get(name_to_entity_id[rel.to_entity])
                )
                if ent:
                    ent.related_entities.add(rel.from_entity)

        return UnifiedKnowledgeBase(
            source_chapters=sorted(self.chapters_seen),
            roles=roles,
            polities=polities,
            civilizations=civilizations,
            religions=religions,
            organizations=organizations,
            schools=schools,
            locations=locations,
            events=events,
            relations=relations,
            name_to_entity_id=name_to_entity_id,
            name_to_location_id=name_to_location_id,
            total_roles=len(roles),
            total_polities=len(polities),
            total_civilizations=len(civilizations),
            total_religions=len(religions),
            total_organizations=len(organizations),
            total_schools=len(schools),
            total_locations=len(locations),
            total_events=len(events),
            total_relations=len(relations),
        )


def load_and_resolve(
    store_dir: str,
    *,
    chapter_filter: Optional[list[int]] = None,
    segment_year_index_path: Optional[str] = None,
    chapter_year_index_path: Optional[str] = None,
) -> UnifiedKnowledgeBase:
    store_path = Path(store_dir)
    segment_years: dict[str, int] = {}
    chapter_bounds: dict[int, tuple[Optional[int], Optional[int]]] = {}
    seg_path = segment_year_index_path or "data/segment_year_index.json"
    chap_path = chapter_year_index_path or "data/chapter_year_index.json"
    if Path(seg_path).exists():
        segment_years = load_segment_year_index(seg_path)
    if Path(chap_path).exists():
        chapter_bounds = load_chapter_year_bounds(chap_path)

    resolver = EntityResolver(segment_years=segment_years, chapter_bounds=chapter_bounds)

    for chapter_file in sorted(store_path.glob("chapter_*.json")):
        if chapter_file.name.endswith("_summary.json"):
            continue
        chapter_index = int(chapter_file.stem.split("_", 1)[1])
        if chapter_filter and chapter_index not in chapter_filter:
            continue

        data = json.loads(chapter_file.read_text(encoding="utf-8"))
        resolver.chapters_seen.add(chapter_index)
        for extraction in data.values():
            chapter_idx = extraction.get("chapter_index", chapter_index)
            seg_idx = extraction.get("segment_index", 1)
            chunk_idx = extraction.get("chunk_start_index", 0)
            source_text = " ".join(extraction.get("source_sentences", []))

            for entity in extraction.get("entities", []):
                resolver.add_role(Role(**entity), chapter_idx, seg_idx, chunk_idx, source_text)
            for loc in extraction.get("locations", []):
                resolver.add_location(Location(**loc), chapter_idx, seg_idx, chunk_idx)
            for evt in extraction.get("events", []):
                resolver.add_event(Event(**evt), chapter_idx, seg_idx, chunk_idx)
            for rel in extraction.get("relations", []):
                resolver.add_relation(Action(**rel), chapter_idx)

    return resolver.build_knowledge_base()


def save_unified_knowledge_base(kb: UnifiedKnowledgeBase, output_path: str) -> None:
    def serialize(obj):
        if isinstance(obj, set):
            return sorted(obj)
        raise TypeError(type(obj))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(kb.model_dump(), ensure_ascii=False, indent=2, default=serialize),
        encoding="utf-8",
    )
    print(f"Saved unified KB -> {output_path}")
    print(
        f"  roles={kb.total_roles} polities={kb.total_polities} "
        f"locations={kb.total_locations} events={kb.total_events} relations={kb.total_relations}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Resolve chapter extractions into unified KB")
    parser.add_argument("--store-dir", default="data/store")
    parser.add_argument("--output", default="data/unified_knowledge.json")
    parser.add_argument("--chapter", type=int, action="append", help="Limit to chapter(s)")
    args = parser.parse_args()

    kb = load_and_resolve(args.store_dir, chapter_filter=args.chapter)
    save_unified_knowledge_base(kb, args.output)
