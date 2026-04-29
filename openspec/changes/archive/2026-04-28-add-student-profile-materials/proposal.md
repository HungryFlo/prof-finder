# Change: Add Student Profile Materials

## Why
Student profiles currently center on parsing a single resume into resume-shaped fields. To make the product more agent native, users need to build a richer academic profile from multiple self-supplied materials such as research interests, personal statements, research plans, and resumes.

## What Changes
- Add a student academic profile generation capability that accepts multiple text-based uploaded materials plus direct manual text input.
- Generate a structured, evidence-aware student profile using an analyzer-then-builder flow adapted from the reference persona method.
- Preserve resume parsing as an input extraction path while allowing non-resume materials to contribute to the final user profile.
- Store profile sources, generated profile content, evidence notes, and insufficient-evidence markers with the `UserProfile`.
- Keep first-stage file support limited to `.md`, `.markdown`, `.txt`, `.tex`, and `.latex`.

## Impact
- Affected specs: `student-profile`, `resume-parser`, `data-model`
- Affected code: `backend/prof_finder/api/routes/profiles.py`, `backend/prof_finder/api/schemas.py`, `backend/prof_finder/api/task_manager.py`, `backend/prof_finder/parser/llm_parser.py`, `backend/prof_finder/prompts/`, `backend/prof_finder/matcher/semantic_matcher.py`, `frontend/src/api/profiles.ts`, `frontend/src/views/profile/ProfileListView.vue`, `frontend/src/types/index.ts`, `backend/tests/test_api_profiles.py`
