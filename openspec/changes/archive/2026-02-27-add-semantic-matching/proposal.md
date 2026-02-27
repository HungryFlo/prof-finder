# Change: Add Semantic Matching with Sentence Transformers

## Why
The current keyword matcher relies on exact substring matching against a hardcoded
term list, causing misses for synonyms (e.g. "NLP" vs "natural language processing")
and false positives from partial matches. Replacing it with sentence-transformer
embeddings + cosine similarity provides genuine semantic understanding with minimal
code change.

## What Changes
- Add `sentence-transformers` dependency (allenai-specter model, ~400 MB, downloaded on first use)
- **BREAKING**: Add `embedding` column (JSON) to `professors` table — requires DB migration
- New `SemanticMatcher` class in `backend/prof_finder/matcher/semantic_matcher.py`
- `execute_match` task in `task_manager.py` switches to `SemanticMatcher` with batch encoding
- Professor embeddings are pre-computed and cached in DB; recomputed when professor data changes
- Score formula: `(cosine_similarity + 1) / 2 × 100`, normalised to 0–100 to match existing API

## Impact
- Affected specs: professor-matching (new capability)
- Affected code:
  - `backend/prof_finder/matcher/keyword_matcher.py` — kept as fallback, no changes
  - `backend/prof_finder/matcher/semantic_matcher.py` — new file
  - `backend/prof_finder/models/schema.py` — add `Professor.embedding` column
  - `backend/prof_finder/api/task_manager.py` — `execute_match` uses `SemanticMatcher`
  - `backend/requirements.txt` — add `sentence-transformers`
  - DB migration script — add `embedding` column
