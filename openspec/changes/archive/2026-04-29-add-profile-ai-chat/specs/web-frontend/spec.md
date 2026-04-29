## ADDED Requirements

### Requirement: Profile AI Chat Panel

The system SHALL provide an embedded chat interface on the profile detail page for AI-guided profile refinement.

#### Scenario: Open chat panel
- **WHEN** the user clicks "AI 优化" on the profile detail page
- **THEN** a chat panel expands below the academic profile section
- **AND** the AI automatically sends an opening question based on profile gaps

#### Scenario: Chat message exchange
- **WHEN** the user types a message and presses send (or Enter)
- **THEN** the message appears in the chat history (right-aligned, user label)
- **AND** a loading indicator shows while waiting for the AI reply
- **AND** the AI reply appears (left-aligned, AI label)
- **AND** the input is cleared for the next message

#### Scenario: Trigger profile refinement
- **WHEN** the user clicks "优化画像" in the chat panel header
- **AND** at least one Q&A exchange has occurred
- **THEN** a loading state shows on the button
- **AND** the refinement API is called with the full chat history
- **AND** on success, the displayed academic profile updates with the refined version
- **AND** a success message is shown

#### Scenario: Refine with no chat history
- **WHEN** the user clicks "优化画像" without any Q&A exchanges
- **THEN** a warning message is shown: "请先与AI进行至少一轮对话"

#### Scenario: Collapse chat panel
- **WHEN** the user clicks the collapse toggle or "AI 优化" button again
- **THEN** the chat panel collapses (chat history preserved in component state while on page)

#### Scenario: Empty profile
- **WHEN** the profile has no `academic_profile` or `profile_analysis`
- **THEN** the AI asks broad discovery questions about the student's background and goals

#### Scenario: Error handling
- **WHEN** the chat API returns an error
- **THEN** an error message is shown in the chat (not as a separate toast)
- **AND** the user can retry sending the message
