# Change: DBLP + Google Scholar complementary integration

## Why

Google Scholar search/crawl is often blocked. DBLP provides a stable official API for CS author discovery and publication lists. Both sources should enrich the same professor record.

## What Changes

- DBLP client (search JSON + PID XML), matcher, publication merge by source
- Professor fields: `dblp_pid`, `dblp_url`, `dblp_enrichment_status`, `dblp_candidates`
- REST: DBLP CRUD/match/refresh + `match-external` / `batch-refresh-external`
- Tasks: `single-dblp-crawl`, `batch-dblp-crawl`, `batch-dblp-match`, `batch-refresh-dblp`, `batch-refresh-external`
- University crawl enqueues Scholar and DBLP matching in parallel
- Enrichment: `scholar_pub` and `dblp_pub` summaries from merged publications
- Frontend: dual external-profile UI

## Impact

- Specs: `rest-api`
- Code: crawler, api/routes, task_manager, enrichment, frontend
