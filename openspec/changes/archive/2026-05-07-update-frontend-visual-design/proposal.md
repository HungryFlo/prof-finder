# Change: Update frontend visual design

## Why

The Web UI mixes Naive UI defaults with Tailwind/shadcn tokens without a single design system, and global CSS still references Inter while Geist is partially loaded. Dark-mode sidebar uses a saturated purple accent that clashes with a restrained academic-tool aesthetic. Meta tags and favicon remain Vite defaults.

## What Changes

- Add OpenSpec requirements for visual design tokens, typography, interaction states, layout rhythm, accessibility (skip link, focus), and HTML meta/branding.
- Unify typography: Geist as the sole primary stack; align `@import` with `@theme` font family names; use `min-height: 100dvh` where full viewport height is intended.
- Refine light/dark CSS variables: one cool-neutral family with a single low-saturation accent; remove the strong purple sidebar primary in dark mode.
- Bridge Naive UI to the same tokens via `NConfigProvider` `theme-overrides` (and light/dark `theme` as needed).
- Polish main layout: content max-width, vertical spacing, active route styling in the sidebar menu, skip-to-content link.
- Update `index.html` with description, basic Open Graph tags, and a branded favicon.

## Impact

- Affected specs: `web-frontend`
- Affected code: `frontend/src/style.css`, `frontend/src/App.vue`, `frontend/src/layouts/MainLayout.vue`, `frontend/index.html`, `frontend/public/` (favicon asset if added)
