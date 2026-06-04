# Change: Add Table Search, Filter, and Sort

## Why

Professor management and match results tables lack search, filtering, and column sorting. Users cannot quickly find specific professors or sort results by different criteria. The backend already exposes `affiliation`/`interest` filter params on `GET /api/professors` and `min_score` on `GET /api/match/results`, but none are wired to the UI. Sorting is hardcoded server-side with no user control.

## What Changes

- Backend: Add `sort_by`, `sort_order`, `search` query params to `GET /api/professors` and `GET /api/match/results`
- Backend: Add `GET /api/professors/affiliations` endpoint returning distinct affiliation values for filter dropdown
- Frontend: Wire NDataTable `remote` mode with native column sorter/filter UI on both tables
- Frontend: Add search input above each table for cross-column text search
- Frontend: Wire existing `affiliation`/`interest` filter params to professor table; wire `min_score` to match table
- i18n: Add new translation keys for search/filter/sort labels

## Impact

- Affected specs: `rest-api`, `web-frontend`
- Affected code:
  - `backend/prof_finder/api/routes/professors.py`
  - `backend/prof_finder/api/routes/match.py`
  - `frontend/src/api/professors.ts`
  - `frontend/src/api/match.ts`
  - `frontend/src/views/professor/ProfessorListView.vue`
  - `frontend/src/views/match/MatchResultsView.vue`
  - `frontend/src/locales/zh.json`
  - `frontend/src/locales/en.json`
