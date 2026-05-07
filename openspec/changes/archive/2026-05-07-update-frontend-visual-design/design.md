## Context

Prof-Finder uses Vue 3 with Naive UI for the shell and data-heavy views, and Tailwind CSS 4 + shadcn-vue (Reka UI) for newer surfaces including AI chat. Visual drift comes from Naive defaults not reading the same tokens as `style.css`.

## Goals

- One cool-neutral palette with a single accent (low chroma blue-cyan) usable in light and dark.
- Geist as the only primary UI font; weights 400–700 available from the existing Google Fonts import.
- Naive `themeOverrides` map `primaryColor`, `borderRadius`, `fontFamily`, and common `common`/`Menu`/`Button` tokens to values derived from the same hex/oklch decisions as CSS variables.

## Non-Goals

- Replacing every `lucide-vue-next` icon in shadcn-vue primitives (high churn); new feature UI should prefer `@vicons/ionicons5` or Naive where practical.
- Migrating off Naive UI or shadcn-vue.
- Full dark-mode redesign of every page beyond token alignment.

## Decisions

- **Accent**: oklch-based primary around hue 230–240 with chroma capped (~0.08–0.12 in light, slightly higher readable contrast on dark) instead of purple (hue ~264).
- **Grain**: single fixed pseudo-layer on `body` via `::after` with tiny opacity and `pointer-events: none` so it does not affect hit targets.
- **Skip link**: absolutely positioned off-screen until `:focus-visible`, targets `#main-content`.

## Risks

- Naive theme API typing: use `GlobalThemeOverrides` from `naive-ui` and keep overrides minimal to avoid version mismatch.
- OG absolute URLs: use relative `og:image` path only (`/favicon.svg`) per common crawler support; omit `og:url` if no canonical deploy URL is configured in-repo.
