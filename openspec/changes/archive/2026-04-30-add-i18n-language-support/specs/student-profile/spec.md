## MODIFIED Requirements
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
- **WHEN** profile generation is triggered with a language parameter
- **THEN** the system SHALL generate the academic profile in the specified language
- **AND** the language SHALL be passed to the LLM via the prompt template
- **AND** the default language SHALL be the user's `profile_language` setting

## ADDED Requirements
### Requirement: Profile Generation Language Control

The system SHALL allow users to select the output language for profile generation.

#### Scenario: User selects English for profile
- **WHEN** a user selects "English" on the profile generation UI
- **AND** triggers profile generation or refinement
- **THEN** the generated `academic_profile` and `profile_analysis` SHALL be in English
- **AND** the profile content SHALL use clean, consistent language without mixed Chinese/English terms

#### Scenario: Default to user language preference
- **WHEN** a user triggers profile generation without explicitly selecting a language
- **THEN** the system SHALL use the user's `profile_language` setting from UserSettings

#### Scenario: Profile language for chat-triggered refinement
- **WHEN** a user triggers profile refinement from chat history
- **THEN** the language used for the regenerated `academic_profile` and analysis SHALL match the authenticated user's `profile_language` setting in UserSettings

### Requirement: AI interviewer chat locale

The interviewer dialogue for `POST /api/profiles/{id}/chat` SHALL follow the client's UI locale conveyed in the request body.

#### Scenario: Locale matches frontend language
- **WHEN** the client sends `locale` aligned with the signed-in user's UI language (`en` or `zh`)
- **THEN** prompts for the interviewer SHALL instruct the model to use that spoken language for questions and short acknowledgements

