# Global History — Agent Instructions

## Project

Build a knowledge graph + interactive visualization for **Stavrianos, A Global History (7th ed., Peking University Press Chinese translation)**.

## Workflow (mandatory)

1. Read `openspec/changes/global-history-mvp/` before coding.
2. Follow **OpenSpec + Superpowers**: propose → LGTM → apply → validate → archive.
3. Do **not** commit copyrighted book text. User-provided files live in `sources/private/` (gitignored).

## Commands

```bash
uv run pytest -q
uv run python scripts/validate_book_structure.py
openspec validate global-history-mvp
```

## Architecture (MVP)

- Text: `sources/book_structure.json` + user-ingested `adapted_book.json`
- Pipeline: ingest → year index → LLM extract → entity resolution → unified KB
- Frontend: React + D3 + Leaflet (phase 2, fork from zizhitongjian patterns)

## Time conventions

- BCE years are **negative** integers (e.g. -403)
- CE years are positive (e.g. 1500)
- Book split at **1500 CE** (Part VI starts)

## Entity types

person, polity, civilization, location, organization, religion, event, relation

## Do not

- Download or scrape pirated book copies
- Commit `sources/private/` or full `adapted_book.json`
- Skip OpenSpec specs when adding capabilities
