# professor-profile Specification

## Purpose
TBD - created by archiving change add-professor-research-profiles. Update Purpose after archive.
## Requirements
### Requirement: Professor Research Source Bundle
The system SHALL assemble a professor research source bundle from stored professor information before generating a research profile.

#### Scenario: Build source bundle from existing fields
- **WHEN** a professor research profile generation task starts
- **THEN** the system includes available `research_interests`, `publications`, `paper_summaries`, `manual_notes`, affiliation, homepage, Google Scholar URL, source URL, and linked source input metadata

#### Scenario: Manual notes priority
- **WHEN** manual notes conflict with inferred conclusions from publications or summaries
- **THEN** the analyzer treats manual notes as higher-priority user-supplied context
- **AND** records the conflict in the analysis output

#### Scenario: Sparse professor data
- **WHEN** a professor has only name and affiliation
- **THEN** the generation task completes with explicit insufficient-evidence markers
- **AND** does not invent research themes or representative works

### Requirement: Professor Research Analyzer
The system SHALL analyze professor source bundles into structured, evidence-oriented research characterization.

#### Scenario: Extract research dimensions
- **WHEN** a source bundle contains professor research evidence
- **THEN** the analyzer extracts research positioning, research themes, methods and assets, representative works, recent directions, student fit signals, evidence notes, confidence levels, and gaps

#### Scenario: Separate facts from inference
- **WHEN** the analyzer derives a theme from publication titles or summaries rather than explicit research interests
- **THEN** the output labels that theme as inferred

#### Scenario: Preserve source evidence
- **WHEN** a research claim is included in the analysis
- **THEN** the output links the claim to one or more source fields such as `research_interests`, publication title, paper summary, source input, or manual note

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
- **WHEN** research profile generation runs
- **THEN** the system SHALL generate the research profile and structured analysis in English
- **AND** the language SHALL be passed to the LLM via the prompt template as English

### Requirement: Professor name locales

The system SHALL store optional explicit `name_locales` on `Professor` (`zh` / `en`) for letters; crawler-created professors remain with empty `name_locales` until the user edits them.

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

### Requirement: Paper summarization for research profiles

Paper summarization used in the professor research-profile pipeline SHALL run in English so outputs align with English research profiles.

#### Scenario: Summary language for pipeline
- **WHEN** paper summarization is invoked from professor edit preview/apply or background summary tasks serving profile generation
- **THEN** the summary output SHALL be in English

