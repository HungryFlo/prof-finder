# Change: Add Professor Research Profiles

## Why
Professor records currently combine crawled metadata, research interests, publications, paper summaries, and manual notes, but there is no dedicated research profile that explains a professor's research agenda with evidence. Matching and letter generation therefore rely on scattered fields and can miss the shape of the professor's work.

## What Changes
- Add a professor research profile generation capability using existing professor fields, paper summaries, publications, source inputs, homepages, and manual notes.
- Generate structured research characterization with evidence notes, research themes, methods, representative works, fit signals, and insufficient-evidence markers.
- Persist generated professor research profiles and source metadata on `Professor`.
- Update semantic matching to prefer generated professor research profile text when available.
- Update follow-up implementation tasks for letter generation and professor UI to use the generated research profile.

## Impact
- Affected specs: `professor-profile`, `data-model`, `professor-matching`
- Affected code: `backend/prof_finder/api/routes/professors.py`, `backend/prof_finder/api/schemas.py`, `backend/prof_finder/api/task_manager.py`, `backend/prof_finder/llm/paper_summarizer.py`, `backend/prof_finder/llm/letter_generator.py`, `backend/prof_finder/matcher/semantic_matcher.py`, `frontend/src/types/index.ts`, professor list/detail/edit views, `backend/tests/test_api_professors.py`, `backend/tests/test_semantic_matcher.py`
