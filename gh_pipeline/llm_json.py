"""Utilities for extracting JSON payloads from LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any


class LLMJSONParseError(ValueError):
    pass


VALID_ENTITY_TYPES = frozenset(
    {"person", "polity", "school", "organization", "civilization", "religion"}
)


def sanitize_extraction_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Drop or fix LLM fields that fail Pydantic validation."""
    entities = []
    for ent in data.get("entities") or []:
        if not isinstance(ent, dict):
            continue
        et = ent.get("entity_type")
        if et not in VALID_ENTITY_TYPES:
            if et in ("event", "location", "region", "place"):
                continue
            ent = {**ent, "entity_type": None}
        entities.append(ent)
    return {**data, "entities": entities}


_CODE_FENCE_RE = re.compile(r"```\s*(?:json)?\s*", re.IGNORECASE)


def extract_json_from_response(content: str) -> dict[str, Any]:
    if not content or not content.strip():
        raise LLMJSONParseError("Content is empty")

    match = _CODE_FENCE_RE.search(content)
    if match:
        start_pos = match.end()
        end_pos = content.find("```", start_pos)
        json_str = content[start_pos:end_pos].strip() if end_pos != -1 else content[start_pos:].strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                return json.loads(json_str[start_idx : end_idx + 1])
            raise

    start_idx = content.find("{")
    end_idx = content.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(content[start_idx : end_idx + 1])
        except json.JSONDecodeError:
            pass

    return json.loads(content)
