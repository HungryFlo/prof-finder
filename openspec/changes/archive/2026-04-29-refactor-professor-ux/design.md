# Design: Professor Management UX Refactoring

## Context

The current professor management consists of:
- **ProfessorListView** at `/professor`: Table + large inline NDrawer (publications + abstracts + research profile + "获取论文摘要" button)
- **ProfessorEditView** at `/professor/:id/edit`: Full page with basic info form, SourceInputPanel, edit-preview/apply flow, paper summaries list, research profile card

Problems: publications in drawer vs paper_summaries in edit page are disconnected; async task results don't auto-refresh the drawer; viewing/editing/profile are fragmented across two surfaces.

## Goals / Non-Goals

**Goals:**
- Click professor name → quick summary (basic info + research profile) in right-side drawer
- Navigate to unified detail+edit page for full information and operations
- Unify paper data display: Scholar publications + source input paper summaries in one page
- All async task completions auto-refresh the page they're initiated from
- Paper data persisted in backend and survives page reloads

**Non-Goals:**
- Making papers manually editable (remain read-only)
- Changing how paper crawling/summarization works on the backend
- Changing the data model or API endpoints

## Decisions

### Decision 1: Summary drawer as separate component
Create `ProfessorSummaryDrawer.vue` as a reusable component (props: `show`, `professorId`; emits: `close`). This keeps ProfessorListView lean and makes the drawer testable independently.

**Alternatives considered:** Keep inline drawer but reduce content. Rejected because the current inline drawer is 150+ lines of template and hard to maintain.

### Decision 2: Replace edit-preview/apply with direct PUT
The edit page's basic info form saves directly via `PUT /professors/:id` instead of the two-step edit-preview → apply-edits flow. The preview/apply flow was designed for merging source inputs with manual edits, but in the new design source inputs have their own dedicated async operations (summarize-sources) separate from basic field edits.

**Alternatives considered:** Keep edit-preview/apply. Rejected because it adds unnecessary complexity — the preview step doesn't provide meaningful value when source inputs are handled separately.

### Decision 3: Publications table + paper summaries list with cross-reference
Display both data sources in separate cards but with computed cross-reference (matching by title) indicated by badges in the publications table.

**Alternatives considered:** Merge publications and paper_summaries into a single unified list. Rejected because they are semantically different data types (Scholar metadata vs LLM summaries) and merging would complicate the backend model.

### Decision 4: fetchData() pattern for all task callbacks
Every async task (fill-publications, paper-summary, professor-profile, refresh) calls the same `fetchData()` on completion, which re-fetches both `GET /professors/:id` and `GET /source-inputs?professor_id=:id`.

**Alternatives considered:** Selective refresh (only refresh relevant section). Rejected because it's more error-prone — a single full refresh ensures all sections stay consistent after any operation.

### Decision 5: Keep `POST /professors/:id/refresh` synchronous
The "Scholar更新" button triggers the existing sync refresh endpoint (not an async task). This is distinct from "获取论文摘要" which is the async `fill-publications` task. Display a warning when refresh would clear existing paper_summaries (`professor.paper_summaries = []` at `professors.py:919`).

## Component Tree

```
ProfessorListView.vue (refactored)
├── NDataTable (name column click → openSummaryDrawer)
├── Modals (Scholar, manual, university crawl) [unchanged]
├── Batch action buttons [unchanged]
└── ProfessorSummaryDrawer (NEW, replaced inline NDrawer)

ProfessorSummaryDrawer.vue (NEW)
├── NDrawer (width 480, v-model:show)
│   ├── NDescriptions (basic info)
│   ├── Research Profile (conditional Markdown)
│   └── "查看详情" NButton → /professor/:id

ProfessorDetailView.vue (NEW, replaces ProfessorEditView)
├── NCard: Basic Info Form (editable, direct PUT save)
├── NCard: SourceInputPanel (existing)
├── NCard: Publications Table (read-only, with cross-ref badges)
├── NCard: Paper Summaries List (read-only)
└── NCard: Research Profile (generate + display)
```

## Route Changes

```
/professor                → ProfessorListView (modified)
/professor/:id            → ProfessorDetailView (NEW)
/professor/:id/edit       → redirect to /professor/:id
```

## Risks / Trade-offs

- **Refresh clears paper_summaries**: `POST /professors/:id/refresh` at `professors.py:919` sets `paper_summaries = []`. The UI should warn users. Mitigation: show a confirmation dialog when paper_summaries exist.
- **Removing edit-preview/apply**: The backend endpoints remain, but if other clients depend on them they'll still work. The new frontend just doesn't call them.
- **Race condition on task completion**: If the SSE `complete` event fires before the DB transaction commits, `fetchData()` might return stale data. Mitigation: existing task manager always marks complete after `session.flush()`, so this is already handled.

## Open Questions

None.
