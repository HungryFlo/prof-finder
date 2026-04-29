## ADDED Requirements
### Requirement: Resume Content as Profile Material
The system SHALL preserve resume parsing as one input extraction path for student academic profile generation.

#### Scenario: Resume contributes structured fields
- **WHEN** a supported resume file is included in a student profile material bundle
- **THEN** the resume parser may extract `education`, `research_experience`, `projects`, and `skills`
- **AND** those parsed fields are included as source evidence for the student profile analyzer

#### Scenario: Non-resume material bypasses resume assumptions
- **WHEN** a supported text file is labeled or detected as research interests, personal statement, research plan, or notes
- **THEN** the system does not require that file to fit the resume parser schema
- **AND** the file remains available to the student profile analyzer as raw academic material
