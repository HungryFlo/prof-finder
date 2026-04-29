## 1. Create ProfessorSummaryDrawer

- [x] 1.1 Create `frontend/src/components/ProfessorSummaryDrawer.vue` — NDrawer with v-model:show, professorId prop, fetches on open, displays basic info + research profile + "查看详情" button

## 2. Create ProfessorDetailView

- [x] 2.1 Create `frontend/src/views/professor/ProfessorDetailView.vue` at route `/professor/:id`
- [x] 2.2 Basic info form card — editable fields (name, affiliation, email, homepage, research_interests, manual_notes) with save via `PUT /professors/:id`
- [x] 2.3 SourceInputPanel card — embed existing component with "论文总结" action button
- [x] 2.4 Publications card — NDataTable with columns (title, year, citations, journal, abstract expandable), action buttons ("Scholar更新", "获取论文摘要"), cross-reference badges for matching summaries
- [x] 2.5 Paper summaries card — NList of summaries with title, summary, keywords
- [x] 2.6 Research profile card — generate button, markdown display, evidence/conflict tags
- [x] 2.7 All async task callbacks call `fetchData()` for auto-refresh

## 3. Update Routes

- [x] 3.1 Add route `/professor/:id` → ProfessorDetailView in `router/index.ts`
- [x] 3.2 Remove route `/professor/:id/edit` → ProfessorEditView
- [x] 3.3 Add redirect from `/professor/:id/edit` to `/professor/:id`

## 4. Refactor ProfessorListView

- [x] 4.1 Import ProfessorSummaryDrawer, add `showSummaryDrawer` / `summaryDrawerProfId` state
- [x] 4.2 Make name column clickable → `openSummaryDrawer(row.id)`
- [x] 4.3 Change "查看" → `openSummaryDrawer(row.id)`, merge with "编辑" → single "详情" button
- [x] 4.4 Change "编辑" button → `router.push('/professor/${id}')`
- [x] 4.5 Replace inline NDrawer template with `<ProfessorSummaryDrawer>`
- [x] 4.6 Remove old `showDetail`, `professorDetail`, `detailLoading` state and `handleFillPublications` function

## 5. Cleanup

- [x] 5.1 Verify no references to ProfessorEditView remain
- [x] 5.2 Delete `frontend/src/views/professor/ProfessorEditView.vue`
- [x] 5.3 Run `npm run build` to verify type-check passes

## 6. Post-implementation fixes

- [x] 6.1 Fix `professorId` from `computed` to `const` to avoid async callback context issues
- [x] 6.2 Replace abstract "悬停查看" tag with NEllipsis for proper abstract display
