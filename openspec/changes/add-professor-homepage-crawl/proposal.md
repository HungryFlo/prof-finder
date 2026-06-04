# Change: Professor profile page enrichment (crawl4ai)

## Why

Generic university crawlers only extract list-page fields. Profile URLs are stored as `homepage` but detail pages (email, research interests, bio) are not fetched unless a site-specific crawler implements follow-up logic.

## What Changes

- Add crawl4ai + LLM single-page profile extraction (`profile_extractor.py`).
- Merge extracted fields without overwriting existing data (`profile_merge.py`).
- Run profile enrichment automatically after list crawl in `GenericUniversityCrawler`.
- Add `POST /professors/{id}/crawl-homepage` and `professor-homepage-crawl` background task.
- Professor detail UI button to trigger manual homepage crawl.

## Impact

- Affected specs: `professor-crawler`
- Affected code: `crawl4ai_engine/`, `api/task_manager.py`, `api/routes/professors.py`, frontend professor detail view
