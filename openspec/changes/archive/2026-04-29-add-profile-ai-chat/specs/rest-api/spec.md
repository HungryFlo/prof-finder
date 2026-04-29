## ADDED Requirements

### Requirement: Profile Chat API

The system SHALL provide REST API endpoints for AI interviewer chat and profile refinement.

#### Scenario: Send chat message
- **WHEN** `POST /api/profiles/{id}/chat` with `{ "message": "...", "history": [...] }`
- **AND** the profile belongs to the current user
- **THEN** the backend constructs an interviewer prompt using the profile's `profile_analysis`, `academic_profile`, chat history, and the new message
- **AND** returns `{ "reply": "AI interviewer response" }`

#### Scenario: Chat with empty history
- **WHEN** `POST /api/profiles/{id}/chat` with `{ "message": "开始", "history": [] }`
- **THEN** the AI interviewer reviews the profile and sends an opening question about the most significant gap

#### Scenario: Refine profile from chat
- **WHEN** `POST /api/profiles/{id}/chat/refine` with `{ "history": [...] }`
- **AND** the profile belongs to the current user
- **THEN** the backend enriches the manual inputs with chat-derived information
- **AND** re-runs the two-stage profile generation pipeline (analyze + build)
- **AND** saves the updated `academic_profile`, `profile_analysis`, `evidence_notes`, `conflict_notes`
- **AND** returns the updated profile

#### Scenario: Chat on non-existent profile
- **WHEN** `POST /api/profiles/{id}/chat` for a profile that does not exist or does not belong to the user
- **THEN** returns 404 error

#### Scenario: LLM unavailable
- **WHEN** the LLM API key is not configured or the API is unreachable
- **THEN** returns 503 error with a descriptive message
