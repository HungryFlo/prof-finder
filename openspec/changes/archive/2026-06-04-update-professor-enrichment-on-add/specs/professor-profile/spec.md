## MODIFIED Requirements

### Requirement: Professor Research Profile Downstream Usage
The system SHALL use generated professor research profile fields to improve matching and letter generation when they are available.

#### Scenario: Matching uses generated professor profile
- **WHEN** a professor has generated research profile content
- **THEN** semantic matching uses the generated research profile fields as primary professor text
- **AND** preserves research interests, publication titles, paper summaries, and affiliation as supporting signals

#### Scenario: Letter generation uses research profile
- **WHEN** a professor has generated research profile content
- **THEN** contact letter generation may cite research themes, representative works, and student fit signals from that profile

#### Scenario: Professors without generated profiles remain usable
- **WHEN** a professor does not have generated research profile content
- **THEN** matching and letter generation continue to use existing professor fields

#### Scenario: Auto-generation after professor create or Scholar refresh
- **WHEN** a professor is created through Scholar crawl, university crawl, manual API create, or Scholar data is refreshed for an existing professor
- **THEN** the system SHALL run the professor research profile generation pipeline as soon as practicable after persistence
- **AND** if evidence is insufficient, the pipeline SHALL complete with explicit insufficient-evidence markers per existing sparse-data rules
- **AND** manually added PDF/ArXiv paper summaries remain available to the analyzer when not removed by a Scholar refresh ruleset
