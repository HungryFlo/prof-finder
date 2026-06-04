# student-profile Specification

## Purpose

定义多材料学生学术画像：从简历、研究兴趣、个人陈述等多源文本经分析—构建两阶段 LLM 流程生成结构化画像，供语义匹配与套磁信生成使用；支持 Web 上传、手动字段与画像激活状态。
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

#### Scenario: Language-controlled output
- **WHEN** profile generation or chat-triggered refinement runs
- **THEN** the system SHALL generate `academic_profile` and structured `profile_analysis` in English
- **AND** the language SHALL be passed to the LLM via the prompt template as English

### Requirement: Student name locales

The system SHALL store optional explicit `name_locales` on `UserProfile` (`zh` / `en`) for use in contact letters without relying on machine translation of `name`.

#### Scenario: Persist name locales
- **WHEN** a user saves name locale strings via the profile API
- **THEN** the system stores them in `name_locales` as validated keys only

### Requirement: Student Profile Downstream Usage
The system SHALL use generated academic profile fields to improve matching and letter generation when they are available.

#### Scenario: Matching uses generated profile
- **WHEN** a profile has generated academic profile content
- **THEN** semantic matching uses the generated academic profile fields as primary student text
- **AND** preserves existing resume fields as supporting signals

#### Scenario: Resume-only profiles remain usable
- **WHEN** a profile does not have generated academic profile content
- **THEN** matching and letter generation continue to use existing resume fields

### Requirement: Student Profile AI Interview Chat

The system SHALL provide an AI interviewer that converses with the student to refine their academic profile through targeted Q&A.

#### Scenario: Start interview session
- **WHEN** a student opens the chat panel on their profile detail page
- **THEN** the AI reviews the current `profile_analysis`, identifies gaps and insufficient-evidence areas
- **AND** sends an opening question focused on the highest-priority gap

#### Scenario: Student answers a question
- **WHEN** the student types a free-text answer and sends it
- **THEN** the AI acknowledges the answer and asks a follow-up question on another gap or deeper detail
- **AND** the AI asks only one question at a time

#### Scenario: AI detects sufficient information
- **WHEN** the AI has gathered enough answers across key profile dimensions (typically 3-4 rounds)
- **THEN** the AI signals that refinement can proceed
- **AND** suggests the student trigger "优化画像"

#### Scenario: Profile refinement from chat
- **WHEN** the student triggers refinement after chat Q&A
- **THEN** the system regenerates the academic profile incorporating all chat-derived information
- **AND** updates `academic_profile`, `profile_analysis`, `evidence_notes`, and `conflict_notes`
- **AND** preserves the original materials and manual inputs

#### Scenario: No existing profile analysis
- **WHEN** the student opens chat for a profile that has no `profile_analysis`
- **THEN** the AI uses available profile fields (education, skills, experiences) as context
- **AND** asks broad questions to discover research interests and target directions

### Requirement: Profile generation language (fixed English)

The system SHALL produce LLM-generated student academic profile text in English only. Manual parsing fields (education, experiences, raw materials) remain in their original language.

#### Scenario: English profile output
- **WHEN** a user triggers profile generation or refinement
- **THEN** the generated `academic_profile` and `profile_analysis` SHALL be in English

#### Scenario: Chat-triggered refinement language
- **WHEN** a user triggers profile refinement from chat history
- **THEN** the regenerated `academic_profile` and analysis SHALL be in English

### Requirement: AI interviewer chat locale

The interviewer dialogue for `POST /api/profiles/{id}/chat` SHALL follow the client's UI locale conveyed in the request body.

#### Scenario: Locale matches frontend language
- **WHEN** the client sends `locale` aligned with the signed-in user's UI language (`en` or `zh`)
- **THEN** prompts for the interviewer SHALL instruct the model to use that spoken language for questions and short acknowledgements

