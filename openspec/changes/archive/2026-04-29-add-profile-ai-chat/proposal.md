# Change: Add AI Chat Interview for Student Profile Refinement

## Why

The current student profile generation is a one-shot process: upload materials → LLM analyzes → profile generated. Students have no way to iteratively refine the profile through conversation. An AI interviewer that asks targeted questions and progressively improves the profile based on student answers would produce more accurate and nuanced profiles.

## What Changes

- **New API endpoint** `POST /api/profiles/{id}/chat`: Takes user message + chat history, returns AI interviewer reply. The AI reviews current profile analysis, identifies gaps, and asks targeted follow-up questions.
- **New API endpoint** `POST /api/profiles/{id}/chat/refine`: Triggers full profile regeneration incorporating all chat Q&A context. Returns updated profile.
- **New LLM prompt** `profile_interviewer` in `student_profile.yaml`: System prompt for the AI interviewer persona — reviews profile gaps, asks one question at a time, acknowledges answers, can summarize what it's learned.
- **Frontend chat panel** in `ProfileDetailView.vue`: Collapsible chat interface embedded below the academic profile section. Shows message history (AI questions + user answers), text input for responses, and a "优化画像" button that triggers refinement.
- **Chat history** passed as message array with each request (stateless — no server-side session storage needed).

## Impact

- Affected specs: `rest-api`, `web-frontend`, `student-profile`
- Affected code: `routes/profiles.py` (new endpoints), `student_profile.yaml` (new prompt), `student_profile_generator.py` (new interview method), `ProfileDetailView.vue` (chat panel), `schemas.py` (new request/response models)
- No database schema changes (chat history is client-side only)
