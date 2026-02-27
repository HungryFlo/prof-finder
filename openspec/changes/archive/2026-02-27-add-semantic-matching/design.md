# Design: Semantic Matching with allenai-specter

## Context
The project currently uses `KeywordMatcher` — a rule-based scorer that extracts terms
from a hardcoded list and checks substring membership. It misses synonyms and
cross-language variations, and produces noisy matches for common words.
Adding embedding-based similarity is the highest-ROI improvement with a contained blast
radius (one new file, one DB column, one changed call-site).

## Goals / Non-Goals
- Goals:
  - Replace scoring logic with cosine similarity over allenai-specter embeddings
  - Cache professor embeddings in DB to avoid re-encoding on every match run
  - Batch-encode all professors without cached embeddings before scoring
  - Maintain identical external API (`score: float 0-100`, `reasons: list[str]`)
  - Keep `KeywordMatcher` intact as a fallback / reference implementation
- Non-Goals:
  - Vector database (overkill at <10k professors per user)
  - Fine-tuning the model
  - Multi-model A/B switching at runtime
  - UI changes

## Decisions

### Model: allenai-specter
- Trained on 146k scientific paper citation pairs — semantic space matches academic context
- 768-dimension output vectors
- Available via `sentence-transformers` as `allenai-specter`
- Alternative considered: `all-MiniLM-L6-v2` (faster, 384-dim, general purpose) — rejected
  because academic vocabulary coverage matters more than speed here

### Embedding storage: JSON column on `professors`
- Chosen: `Professor.embedding = Column(JSON)` — stores `list[float]` (768 floats ≈ 6 KB/row)
- Alternative considered: separate `ProfessorEmbedding` table — rejected (unnecessary join complexity)
- Alternative considered: pgvector — rejected (project uses SQLite, pgvector is PostgreSQL-only)

### Text serialisation for professors
```
{research_interests joined by "; "} [SEP] {top-15 pub titles joined by ". "}. {affiliation}
```
The `[SEP]` token is the specter training convention for combining title + context.

### Text serialisation for profiles
```
{skills joined by "; "} [SEP] {research_experience title+description}. {projects name+description}
```

### Score normalisation
```
cosine_similarity ∈ [-1, 1]  →  score = (sim + 1) / 2 × 100  ∈ [0, 100]
```
Academic texts are rarely negatively correlated, so practical range is ~[30, 90].

### Batch encoding strategy
In `execute_match`:
1. Load all professors for the user.
2. Collect those without `professor.embedding`.
3. Build their texts, call `model.encode(texts, batch_size=32)`, store back to DB.
4. Encode profile text once.
5. Compute cosine similarity in a single NumPy dot-product pass over all embeddings.

This means a fresh professor pool encodes once; subsequent match runs skip encoding entirely.

### Model loading
Singleton pattern via module-level `_model = None` + `_get_model()`.
The model is ~400 MB and loads in ~2–3 s; it should not be loaded at import time.

## Risks / Trade-offs
- First-run model download (~400 MB) requires internet access → document in README
- `[SEP]` token is specter-specific; if model is swapped, text builder must be updated
- JSON storage of 768 floats per professor is ~6 KB; 1000 professors = ~6 MB, acceptable
- NumPy vectorised cosine assumes embeddings are L2-normalised (specter does this by default
  with `normalize_embeddings=True`); if not normalised, dot product ≠ cosine similarity

## Migration Plan
1. Add `embedding` column via Alembic migration (nullable JSON, default null).
2. Deploy new code; `execute_match` auto-fills embeddings on first run.
3. No manual data backfill required.
4. Rollback: revert `execute_match` to use `KeywordMatcher`; column is nullable so no data loss.

## Open Questions
- None blocking implementation.
