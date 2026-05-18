## 1. Backend

- [x] 1.1 Add `sort_by`, `sort_order`, `search` params to `GET /api/professors` with dynamic column sorting
- [x] 1.2 Add `GET /api/professors/affiliations` endpoint returning distinct affiliations
- [x] 1.3 Add `sort_by`, `sort_order`, `search` params to `GET /api/match/results` with dynamic column sorting

## 2. Frontend API Layer

- [x] 2.1 Extend `ProfessorListParams` and add `getAffiliations()` method
- [x] 2.2 Extend `MatchResultsParams` with sort/search params

## 3. Frontend Views

- [x] 3.1 Update `ProfessorListView.vue`: search bar, remote sorting, affiliation column filter
- [x] 3.2 Update `MatchResultsView.vue`: search bar, remote sorting

## 4. i18n

- [x] 4.1 Add new keys to `zh.json` and `en.json`

## 5. Validation

- [x] 5.1 Run `openspec validate add-table-search-filter-sort --strict --no-interactive`
