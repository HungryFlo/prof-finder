## Context

Prof-Finder is a Chinese-first application but handles inherently bilingual academic data (English from Google Scholar, Chinese from university crawlers). The LLM-generated content (profiles, summaries) currently hardcodes Chinese output, producing mixed-language results. The frontend has zero i18n infrastructure.

## Goals / Non-Goals

- Goals:
  - Let users choose output language (zh/en) for LLM-generated profiles and summaries
  - Build vue-i18n framework so UI strings can be translated
  - Keep changes backward-compatible (default zh behavior unchanged)
- Non-Goals:
  - Storing bilingual versions of every data field
  - Translating backend API error messages (future work)
  - Supporting languages beyond zh/en for now

## Decisions

### Decision 1: Language preference stored in UserSettings

Store `profile_language` (default "zh") in UserSettings. This is the user's default preference for ALL LLM-generated content. Individual pages can override via UI toggle.

- Alternative: Per-request parameter only. Rejected because users likely always want the same language.
- Alternative: Per-profile field. Rejected as over-engineering for now.

### Decision 2: Language parameter flows through generator method signatures

Each LLM generator's `generate()` method accepts an explicit `language` parameter. The API route reads `profile_language` from user settings and passes it down.

- Alternative: Read settings inside generators. Rejected because it couples generators to DB.

### Decision 3: Prompt templates use `{{ language }}` variable substitution

YAML prompts use `{{ language }}` placeholder, replaced at runtime with full language instruction (e.g., "输出中文 Markdown" or "Output in English Markdown").

- Alternative: Separate zh/en prompt files. Rejected because prompts are 90% identical.

### Decision 4: vue-i18n with JSON locale files

Use `vue-i18n` (standard Vue 3 i18n library) with JSON locale files. Naive UI's built-in locale system is wired to vue-i18n's locale.

- Alternative: Custom i18n solution. Rejected because vue-i18n is mature and integrates with Naive UI.

### Decision 5: Single change proposal covers both phases

Combined because Phase 1 (content language) and Phase 2 (UI i18n) share the same user settings field and language switcher UI. Implementing together avoids rework.

## Risks / Trade-offs

- **Risk**: vue-i18n adds ~15KB to bundle. → Acceptable for the functionality gained.
- **Risk**: String extraction is tedious. → Mitigated by AI-assisted bulk translation; do all .vue files in one pass.
- **Risk**: Database migration on SQLite. → SQLite supports ALTER TABLE ADD COLUMN with DEFAULT.

## Migration Plan

1. Add `profile_language` column with default "zh" → no existing data affected
2. LLM generators gain `language` parameter with default "zh" → existing callers unchanged
3. Frontend locale files created → English strings initially generated, can be refined later
4. No breaking changes to API contracts
