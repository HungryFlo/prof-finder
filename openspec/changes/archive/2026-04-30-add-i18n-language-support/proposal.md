# Change: Add i18n Language Support

## Why

The application has two language-mixing problems:
1. **LLM-generated content** (profiles, summaries) is always in Chinese because prompts hardcode "输出中文", but source data is mixed Chinese/English — producing inconsistent output. Students applying to international PhD programs need English profiles.
2. **Frontend UI strings** are hardcoded in Chinese across ~50+ files with zero i18n infrastructure, making it impossible to serve non-Chinese-speaking users or switch UI language.

## What Changes

**Phase 1 — LLM Content Language Control:**
- Add `profile_language` field to `UserSettings` model (default `"zh"`, options `"zh"`/`"en"`)
- Pass `language` parameter through all LLM generators (student profile, professor profile, paper summarizer)
- Update YAML prompt templates to support `{{ language }}` variable
- Add language selector UI to profile detail and professor detail pages
- Preserve existing `language` parameter in `LetterGenerator` (already implemented)

**Phase 2 — Frontend i18n Framework:**
- Install `vue-i18n` and create locale files (`zh.json`, `en.json`)
- Wire vue-i18n to Naive UI locale system
- Extract all hardcoded UI strings from Vue components to locale files
- Add language switcher to main layout header

## Impact

- Affected specs: `user-settings`, `student-profile`, `professor-profile`, `web-frontend`
- Affected code:
  - Backend: `models/schema.py`, `api/schemas.py`, `api/routes/settings.py`, `api/routes/profiles.py`, `api/routes/professors.py`, `llm/student_profile_generator.py`, `llm/professor_profile_generator.py`, `llm/paper_summarizer.py`, `prompts/*.yaml`
  - Frontend: `main.ts`, `App.vue`, `layouts/MainLayout.vue`, all `views/*.vue`, all `components/*.vue`, `stores/*.ts`, `api/*.ts`
