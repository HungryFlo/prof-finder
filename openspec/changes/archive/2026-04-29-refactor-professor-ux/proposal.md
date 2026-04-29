# Change: Refactor Professor Management UX

## Why

The professor management pages have three UX problems:
1. Paper abstracts fetched via async tasks don't auto-refresh in the drawer, appearing lost on reload
2. Publications (Scholar) and paper_summaries (source inputs) are displayed in separate UI surfaces with no cross-referencing
3. Viewing (drawer), editing (separate page), and research profile are three disconnected surfaces

## What Changes

- **Professor list page**: Clicking a professor name opens a lean right-side summary drawer (basic info + research profile only). "查看" button also opens the summary drawer. "编辑" button navigates to the unified detail page.
- **New ProfessorSummaryDrawer component**: Reusable NDrawer that fetches professor detail on open, displays basic info + research profile, with a "查看详情" CTA to the full detail page.
- **Combined detail+edit page** (`/professor/:id`, replaces `/professor/:id/edit`): Basic info form (editable, direct PUT save), SourceInputPanel, unified paper section (Scholar publications table + paper summaries list with cross-reference), and research profile card. All async task callbacks auto-refresh via `fetchData()`.
- **Route change**: `/professor/:id/edit` → `/professor/:id` with backward-compatible redirect.
- **Remove** `ProfessorEditView.vue` (replaced by `ProfessorDetailView.vue`).
- **Remove** inline detail drawer from `ProfessorListView.vue` (replaced by `ProfessorSummaryDrawer.vue`).

## Impact

- Affected specs: `web-frontend`
- Affected code: `ProfessorListView.vue`, `ProfessorEditView.vue` (removed), `router/index.ts`, new `ProfessorSummaryDrawer.vue`, new `ProfessorDetailView.vue`
- No backend changes required
