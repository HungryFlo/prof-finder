## 1. Backend: UserSettings language field

- [x] 1.1 Add `profile_language` column (String, default "zh") to UserSettings model in `schema.py`
- [x] 1.2 Add `profile_language` to UserSettings Pydantic schema in `api/schemas.py`
- [x] 1.3 Update Settings API routes to accept/return `profile_language`
- [x] 1.4 Create database migration for new column

## 2. Backend: LLM generator language support

- [x] 2.1 Update `StudentProfileGenerator.generate()` to accept `language` parameter
- [x] 2.2 Update `StudentProfileGenerator.refine_from_chat()` to accept `language` parameter
- [x] 2.3 Update `ProfessorProfileGenerator.generate()` to accept `language` parameter
- [x] 2.4 Update `PaperSummarizer.summarize()` to accept `language` parameter
- [x] 2.5 Update `student_profile.yaml` prompts with `{language_instruction}` variable
- [x] 2.6 Update `professor_profile.yaml` prompts with `{language_instruction}` variable
- [x] 2.7 Update `paper_summarizer.yaml` prompt with `{language_summary_format}` and `{language_summary_rule}` variables
- [x] 2.8 Update API routes (profiles, professors) to read `profile_language` from user settings and pass to generators

## 3. Frontend: Language selector in content pages

- [x] 3.1 Add language selector to SettingsView (profile_language field in settings)
- [x] 3.2 Language preference auto-read by backend from user settings on generation

## 4. Frontend: vue-i18n infrastructure

- [x] 4.1 Install `vue-i18n` dependency
- [x] 4.2 Create `frontend/src/locales/zh.json` with all UI strings
- [x] 4.3 Create `frontend/src/locales/en.json` with English translations
- [x] 4.4 Configure vue-i18n in `main.ts`
- [x] 4.5 Wire vue-i18n locale to Naive UI locale in `App.vue`
- [x] 4.6 Add language switcher to MainLayout header
- [x] 4.7 Replace hardcoded strings in auth views, settings, task components, MainLayout with `$t()` calls
- [x] 4.8 Replace hardcoded strings in stores/tasks.ts with i18n calls
- [x] 4.9 Sync `<html lang>` with UI locale via `syncHtmlLang` in `frontend/src/i18n.ts`

## 5. Verification

- [x] 5.1 Run `npm run build` (vue-tsc + vite) — no type errors
- [x] 5.2 Run backend tests: `conda activate prof-finder` then `cd backend && python -m pytest` — 191 passed, 1 skipped

**Manual / release smoke (not in CI):** LLM outputs in zh vs en; full UI copy and Naive UI locale in a browser.

## Follow-up (not in this change)

Per-page language toggle on ProfileDetailView (backend already supports `profile_language` via settings).
