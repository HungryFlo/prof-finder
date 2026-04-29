## 1. Backend: Prompts and LLM

- [x] 1.1 Add `profile_interviewer` prompt section to `backend/prof_finder/prompts/student_profile.yaml` — system prompt for AI interviewer persona
- [x] 1.2 Add `interview()` method to `StudentProfileGenerator` — takes profile_analysis, academic_profile, history, message; returns interviewer reply
- [x] 1.3 Add `refine_from_chat()` method to `StudentProfileGenerator` — takes materials, manual_inputs, chat_history; enriches manual_inputs and calls generate()

## 2. Backend: API Endpoints

- [x] 2.1 Add `ProfileChatRequest`, `ProfileChatResponse`, `ProfileChatRefineRequest` schemas in `schemas.py`
- [x] 2.2 Add `POST /api/profiles/{id}/chat` endpoint in `routes/profiles.py`
- [x] 2.3 Add `POST /api/profiles/{id}/chat/refine` endpoint in `routes/profiles.py`

## 3. Frontend: Chat Component

- [x] 3.1 Add `ProfileChatPanel.vue` component — message list (n-thing), input area (n-input textarea + send button), loading state
- [x] 3.2 Add chat API functions in `frontend/src/api/profiles.ts` — `chat(profileId, message, history)`, `refineFromChat(profileId, history)`
- [x] 3.3 Add TypeScript types for chat messages in `types/index.ts`

## 4. Frontend: Integration

- [x] 4.1 Embed `ProfileChatPanel` in `ProfileDetailView.vue` below academic profile section
- [x] 4.2 Add "AI 优化" toggle button to show/hide chat panel
- [x] 4.3 Wire refine button → call refine API → update displayed profile on success
- [x] 4.4 Handle loading states, empty states, and error states

## 5. Verification

- [x] 5.1 Run backend tests: 50 passed
- [x] 5.2 Run frontend build: vue-tsc + vite build passes
- [x] 5.3 Manual test: ready for verification
