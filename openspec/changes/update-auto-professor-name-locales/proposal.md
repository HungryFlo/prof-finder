# Change: Auto-fill professor name_locales from trusted sources

## Why

School crawlers, Scholar, and DBLP already provide Chinese or English author names, but `name_locales` stayed empty until manual edit—hurting bilingual contact letters.

## What Changes

- `merge_name_locales` utility: fill empty `zh`/`en` only; never overwrite user edits
- Hooks on university crawl, Scholar/DBLP crawl & match, batch refresh
- CLI `professor backfill-name-locales` for existing records
- **No** pinyin inference into `en`; **no** professor list UI/API changes

## Impact

- Specs: `professor-profile`
- Code: `utils/name_locales.py`, `task_manager`, `routes/professors`, `cli/professor`
