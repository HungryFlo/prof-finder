# Design: AI Chat Interview for Student Profile

## Context

Current flow: upload materials → one-shot LLM analyze+build → static profile displayed.

Target flow: upload materials → one-shot profile → AI interviewer identifies gaps → student answers questions → AI refines profile iteratively.

The chat is **stateless** on the backend — the frontend sends the full message history with each request. This avoids session management complexity and keeps the architecture simple.

## Goals / Non-Goals

**Goals:**
- AI interviewer asks targeted questions about profile gaps, insufficient evidence areas, and ambiguous claims
- Student can answer in free-form text
- AI acknowledges answers and asks follow-up questions (max ~3-4 rounds before suggesting refinement)
- Student can trigger profile regeneration at any point, incorporating all chat Q&A
- Regenerated profile updates `academic_profile`, `profile_analysis`, `evidence_notes`, `conflict_notes`

**Non-Goals:**
- Real-time streaming (uses standard request/response)
- Multi-turn conversation beyond ~10 messages (prompt budget constraint)
- Voice/audio input
- Editing profile fields directly from chat (use existing form for that)

## Decisions

### Decision 1: Stateless chat with client-side history
Each `POST /chat` request includes the full message history. The LLM prompt receives the history as context. No server-side session storage.

**Rationale:** Simpler implementation, no session cleanup needed, works across page reloads (history in component state, lost on refresh — acceptable for MVP).

### Decision 2: Separate chat and refine endpoints
`/chat` handles the conversation loop. `/chat/refine` triggers full profile regeneration. The student explicitly triggers refinement rather than it happening automatically.

**Rationale:** Profile regeneration calls the two-stage LLM pipeline (analyze + build), which is expensive (~2 LLM calls). Batching it on explicit request avoids wasting tokens on partial conversations.

### Decision 3: AI interviewer prompt in student_profile.yaml
Add a `profile_interviewer` prompt section alongside existing `material_analysis` and `profile_builder`. The interviewer receives:
- Current `profile_analysis` JSON (gaps, insufficient evidence, weak claims)
- Current `academic_profile` Markdown  
- Full chat history
- Latest user message

The system prompt instructs the AI to:
- Ask ONE question at a time
- Focus on areas marked as `insufficient_evidence` or inferred claims
- Acknowledge the student's previous answer before asking the next question
- After 3-4 rounds, suggest it has enough to refine the profile

### Decision 4: Chat panel embedded in ProfileDetailView
A collapsible card section between the academic profile display and the editable form. Opens when user clicks "AI 优化" button.

**Alternatives considered:** Separate page, modal, or sidebar. Rejected because embedding keeps the profile context visible and makes the connection between chat and profile clear.

## Data Flow

```
ProfileDetailView
├── Academic Profile (read-only display)
├── Chat Panel (NEW)
│   ├── Message history (AI questions + user answers)
│   ├── Text input + send button
│   └── "优化画像" button → triggers refinement
└── Editable Form (existing)

Chat message flow:
1. User types answer → sends POST /api/profiles/{id}/chat
   Body: { message: "我在...", history: [{role, content}, ...] }
2. Backend loads profile, builds interviewer prompt with profile_analysis + history
3. LLM returns interviewer reply
4. Response: { reply: "谢谢你的回答。接下来我想了解..." }

Refinement flow:
1. User clicks "优化画像" → sends POST /api/profiles/{id}/chat/refine
   Body: { history: [{role, content}, ...] }
2. Backend builds refined manual_inputs from chat Q&A
3. Backend re-runs StudentProfileGenerator.generate() with original materials + enriched manual_inputs
4. Saves updated profile fields
5. Response: updated Profile
```

## Backend Architecture

### New methods on `StudentProfileGenerator`

```python
async def interview(self, profile_analysis: dict, academic_profile: str, 
                    history: list[dict], message: str) -> str:
    """Generate next interviewer question/response."""
    # Uses profile_interviewer prompt

async def refine_from_chat(self, materials: list, manual_inputs: dict,
                           chat_history: list[dict]) -> dict:
    """Regenerate profile incorporating chat Q&A."""
    # Enriches manual_inputs with chat-derived info, then calls generate()
```

### New API schemas

```python
class ProfileChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{role: "user"|"assistant", content: str}]

class ProfileChatResponse(BaseModel):
    reply: str

class ProfileChatRefineRequest(BaseModel):
    history: list[dict] = []

class ProfileChatRefineResponse(BaseModel):
    profile: ProfileResponse
```

## Frontend Component

Chat panel UI built with Naive UI components:
- `n-card` wrapper with "AI 画像优化" title and collapse toggle
- `n-scrollbar` for message list (max-height ~400px)
- Messages rendered as `n-thing` components:
  - AI messages: left-aligned, info-colored avatar ("AI")
  - User messages: right-aligned, success-colored avatar ("我")
- `n-input` (textarea) + `n-button` for message input
- `n-button` (type="warning") "优化画像" in the card header

## Risks / Trade-offs

- **Token usage**: Each chat request re-sends full history. Mitigation: limit history to ~10 messages, keep messages concise.
- **LLM latency**: ~2-5s per chat response. Mitigation: show loading spinner, keep user informed.
- **Profile regeneration cost**: Two LLM calls per refine. Mitigation: explicit trigger only, not automatic.
- **Chat lost on page refresh**: History is component state only. Mitigation: acceptable for MVP; student can re-answer questions.

## Open Questions

None.
