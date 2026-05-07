## 1. OpenSpec

- [x] 1.1 Scaffold `proposal.md`, `tasks.md`, `design.md`, and `specs/web-frontend/spec.md`
- [x] 1.2 Run `openspec validate update-frontend-visual-design --strict --no-interactive` and fix issues

## 2. Implementation

- [x] 2.1 Align `frontend/src/style.css`: Geist-only stack, `100dvh`, `scroll-behavior: smooth`, refined oklch tokens (single accent, cool neutrals), optional subtle grain overlay
- [x] 2.2 Wire Naive UI `theme` / `themeOverrides` in `frontend/src/App.vue` to match CSS variables
- [x] 2.3 Update `frontend/src/layouts/MainLayout.vue`: skip link, content max-width, menu active styling, spacing
- [x] 2.4 Update `frontend/index.html` meta/og; add branded favicon under `frontend/public/`

## 3. Verification

- [x] 3.1 `cd frontend && npm run build`
- [x] 3.2 Smoke-check login layout, main layout nav, settings, and a view that uses shadcn (e.g. profile AI chat) for visual consistency
