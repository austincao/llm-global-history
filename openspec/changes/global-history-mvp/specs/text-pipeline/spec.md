## ADDED Requirements

### Requirement: Pipeline artifact contracts
The project SHALL document JSON artifact paths and fields aligned with zizhitongjian patterns: `segment_year_index.json`, `chapter_year_index.json`, `unified_knowledge.json`, `location_geocoding.json`.

#### Scenario: Design documents artifacts
- **WHEN** `openspec/changes/global-history-mvp/design.md` is read
- **THEN** it SHALL list each artifact path and BCE-negative year convention

### Requirement: Entity type enumeration
The unified knowledge model SHALL support at minimum: person, polity, civilization, religion, location, organization, event, relation.

#### Scenario: Design lists entity types
- **WHEN** design.md entity section is read
- **THEN** all eight types SHALL be explicitly named

### Requirement: LLM extraction placeholder
The repository SHALL reserve modules and tasks for `knowledge_extraction.py` and `entity_resolution.py` without requiring API keys for MVP scaffold validation.

#### Scenario: Tests run without API keys
- **WHEN** `uv run pytest -q` executes on a clean checkout
- **THEN** tests pass without `DEEPSEEK_API_KEY` set
