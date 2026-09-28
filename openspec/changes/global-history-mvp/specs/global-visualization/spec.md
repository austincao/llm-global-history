## ADDED Requirements

### Requirement: Visualization deferred with contract
Global visualization (timeline, network, map) SHALL be specified in design but implemented in a follow-up change after unified KB exists.

#### Scenario: MVP scope excludes frontend build
- **WHEN** global-history-mvp tasks are completed
- **THEN** no `visualization/` npm build is required for change validation

#### Scenario: URL context model documented
- **WHEN** design.md global context section is read (future)
- **THEN** it SHALL define chapterRange, yearRange, and selection compatible with zizhitongjian URL state patterns
