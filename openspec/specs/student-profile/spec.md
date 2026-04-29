# student-profile Specification

## Purpose
TBD - created by archiving change add-student-profile-materials. Update Purpose after archive.
## Requirements
### Requirement: Multi-Material Student Profile Intake
The system SHALL allow Web users to create a student academic profile from multiple text-based materials and direct manual text in a single profile generation request.

#### Scenario: Upload multiple supported text files
- **WHEN** a Web user uploads one or more `.md`, `.markdown`, `.txt`, `.tex`, or `.latex` files for profile generation
- **THEN** the system accepts the files as profile materials
- **AND** preserves each material's original filename, source type, and text content for the generation task

#### Scenario: Add manual academic context
- **WHEN** a Web user provides direct text for research interests, personal statement, research plan, or free-form notes
- **THEN** the system includes those manual fields in the same material bundle as uploaded files
- **AND** marks the manual fields as user-provided sources

#### Scenario: Reject unsupported formats
- **WHEN** a Web user uploads a file outside `.md`, `.markdown`, `.txt`, `.tex`, or `.latex`
- **THEN** the request is rejected with a clear unsupported-format error

### Requirement: Student Profile Analyzer
The system SHALL analyze student materials into a structured, evidence-oriented academic profile analysis before generating the final readable profile.

#### Scenario: Extract academic dimensions
- **WHEN** student materials are submitted for generation
- **THEN** the analyzer extracts research interests, academic background, research experiences, projects, methods, skills, target directions, strengths, gaps, and source evidence

#### Scenario: Manual input priority
- **WHEN** manual text conflicts with uploaded file content
- **THEN** the analyzer treats manual text as higher priority
- **AND** records the conflict in the analysis output

#### Scenario: Insufficient evidence
- **WHEN** a profile dimension has fewer than two supporting material signals
- **THEN** the analyzer marks that dimension as insufficiently evidenced instead of inventing details

### Requirement: Student Academic Profile Generation
The system SHALL build a readable student academic profile from analyzer output without adding unsupported claims.

#### Scenario: Generate profile sections
- **WHEN** analyzer output is available
- **THEN** the builder generates academic positioning, research interests, background evidence, methods and skills, target directions, strengths and gaps, and source notes

#### Scenario: Preserve evidence boundaries
- **WHEN** a generated claim is based on inference rather than explicit text
- **THEN** the generated profile labels the claim as inferred

#### Scenario: Save generated profile
- **WHEN** profile generation completes successfully
- **THEN** the system saves the generated profile content, structured analysis, material metadata, evidence notes, conflict notes, and generation timestamp on the created `UserProfile`

### Requirement: Student Profile Downstream Usage
The system SHALL use generated academic profile fields to improve matching and letter generation when they are available.

#### Scenario: Matching uses generated profile
- **WHEN** a profile has generated academic profile content
- **THEN** semantic matching uses the generated academic profile fields as primary student text
- **AND** preserves existing resume fields as supporting signals

#### Scenario: Resume-only profiles remain usable
- **WHEN** a profile does not have generated academic profile content
- **THEN** matching and letter generation continue to use existing resume fields

