## MODIFIED Requirements
### Requirement: Professor Research Profile Generation
The system SHALL build and save a readable professor research profile from structured analysis.

#### Scenario: Generate research profile sections
- **WHEN** analyzer output is available
- **THEN** the builder generates research positioning, research themes, methods and assets, representative works, recent direction, student fit signals, evidence notes, and gaps

#### Scenario: Save generated professor profile
- **WHEN** professor research profile generation completes successfully
- **THEN** the system saves generated profile content, structured analysis, evidence notes, conflict notes, source metadata, and generation timestamp on the `Professor`

#### Scenario: Refresh matching representation
- **WHEN** generated professor research profile fields change
- **THEN** the system clears or refreshes the cached professor embedding before the next semantic match uses that professor

#### Scenario: Language-controlled output
- **WHEN** research profile generation is triggered with a language parameter
- **THEN** the system SHALL generate the research profile in the specified language
- **AND** the language SHALL be passed to the LLM via the prompt template
- **AND** the default language SHALL be the user's `profile_language` setting

## ADDED Requirements
### Requirement: Paper Summarization Language Control

The system SHALL support language selection for paper summarization.

#### Scenario: Summarize paper in Chinese
- **WHEN** paper summarization is triggered with language "zh"
- **THEN** the summary output SHALL be in Chinese
- **AND** keywords MAY include English technical terms where appropriate

#### Scenario: Summarize paper in English
- **WHEN** paper summarization is triggered with language "en"
- **THEN** the summary output SHALL be in English
- **AND** keywords SHALL be in English
