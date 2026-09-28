## ADDED Requirements

### Requirement: Book structure manifest
The system SHALL maintain a versioned JSON manifest describing 8 parts and 44 chapters with a 1500 CE era split.

#### Scenario: Valid structure passes validation
- **WHEN** `scripts/validate_book_structure.py` runs against `sources/book_structure.json`
- **THEN** it exits 0 and reports 8 parts, 44 chapters, and 21/23 pre/post-1500 chapter counts

#### Scenario: Chapter indices are contiguous
- **WHEN** the manifest is loaded
- **THEN** chapter_index values SHALL be integers 1 through 44 with no gaps or duplicates

### Requirement: Era split at 1500
The manifest SHALL mark parts 1–5 as `pre-1500` and parts 6–8 as `post-1500`.

#### Scenario: Chapter 22 is post-1500
- **WHEN** chapter 22 metadata is read
- **THEN** its parent part era SHALL be `post-1500`
