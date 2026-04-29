## ADDED Requirements

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
