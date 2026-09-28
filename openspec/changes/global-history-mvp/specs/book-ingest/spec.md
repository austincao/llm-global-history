## ADDED Requirements

### Requirement: Local EPUB ingestion
The system SHALL parse a user-provided EPUB from `sources/private/` into `adapted_book.json` without committing copyrighted content to Git.

#### Scenario: Successful ingest
- **WHEN** user runs `ingest_book.py --input sources/private/<file>.epub`
- **THEN** the script writes `adapted_book.json` with at least one paragraph and exits 0

#### Scenario: Missing input file
- **WHEN** the input path does not exist
- **THEN** the script exits non-zero with instructions to place a legal copy in `sources/private/`

#### Scenario: Git ignore protection
- **WHEN** repository `.gitignore` is inspected
- **THEN** `sources/private/` and `adapted_book.json` SHALL be listed

### Requirement: Chapter heading detection
The ingest script SHALL detect Chinese chapter headings matching `第N章` and attach paragraphs to the corresponding chapter metadata from `book_structure.json`.

#### Scenario: Known chapter maps to structure
- **WHEN** heading `第7章 中国文明` is encountered
- **THEN** subsequent paragraphs SHALL include `chapter_index: 7` and part metadata from the manifest
