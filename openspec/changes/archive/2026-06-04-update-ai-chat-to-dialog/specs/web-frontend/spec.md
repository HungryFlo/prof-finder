## MODIFIED Requirements

### Requirement: Profile AI Chat Panel

The system SHALL provide a dialog-based chat interface on the profile detail page for AI-guided profile refinement.

#### Scenario: Open chat dialog
- **WHEN** the user clicks "AI 优化" on the profile detail page
- **THEN** a chat dialog opens as an overlay (dialog or drawer)
- **AND** the page content behind the dialog remains visible (dimmed)
- **AND** the AI automatically sends an opening question based on profile gaps

#### Scenario: Chat message exchange
- **WHEN** the user types a message and presses send (or Enter)
- **THEN** the message appears in the chat history (right-aligned, user label)
- **AND** a loading indicator shows while waiting for the AI reply
- **AND** the AI reply appears (left-aligned, AI label)
- **AND** the input is cleared for the next message

#### Scenario: Trigger profile refinement
- **WHEN** the user clicks "优化画像" in the chat dialog header
- **AND** at least one Q&A exchange has occurred
- **THEN** a loading state shows on the button
- **AND** the refinement API is called with the full chat history
- **AND** on success, the displayed academic profile updates with the refined version
- **AND** a success message is shown

#### Scenario: Refine with no chat history
- **WHEN** the user clicks "优化画像" without any Q&A exchanges
- **THEN** a warning message is shown: "请先与AI进行至少一轮对话"

#### Scenario: Close and reopen chat dialog
- **WHEN** the user closes the chat dialog
- **AND** later clicks "AI 优化" again
- **THEN** the dialog reopens with the previous chat history preserved
- **AND** the user can continue the conversation from where they left off

#### Scenario: Empty profile
- **WHEN** the profile has no `academic_profile` or `profile_analysis`
- **THEN** the AI asks broad discovery questions about the student's background and goals

#### Scenario: Error handling
- **WHEN** the chat API returns an error
- **THEN** an error message is shown in the chat (not as a separate toast)
- **AND** the user can retry sending the message
