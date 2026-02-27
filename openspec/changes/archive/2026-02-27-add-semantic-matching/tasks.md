# Tasks: Add Semantic Matching

## 1. Dependencies
- [x] 1.1 Add `sentence-transformers>=3.0.0` and `numpy>=1.24` to `pyproject.toml`

## 2. Database Migration
- [x] 2.1 Add nullable `embedding` JSON column to `Professor` model in `backend/prof_finder/models/schema.py`
- [x] 2.2 Add `_migrate()` helper in `backend/prof_finder/db/database.py` (ALTER TABLE via PRAGMA, no Alembic — project uses SQLite + create_all)
- [x] 2.3 Migration runs automatically on `Database._init_tables()`

## 3. SemanticMatcher Implementation
- [x] 3.1 Created `backend/prof_finder/matcher/semantic_matcher.py` with:
  - `_get_model()` singleton loader for `allenai-specter`
  - `build_professor_text(professor: dict) -> str`
  - `build_profile_text(profile: dict) -> str`
  - `encode_texts(texts) -> np.ndarray` (batch, L2-normalised)
  - `SemanticMatcher.match(profile, professor, professor_embedding, profile_embedding) -> tuple[float, list[str]]`

## 4. Task Manager Integration
- [x] 4.1 Updated `execute_match` in `backend/prof_finder/api/task_manager.py`:
  - Collect professors missing `embedding`
  - Batch-encode them with `batch_size=32`, persist to DB
  - Encode profile text once, pass `profile_embedding` to every `matcher.match()` call
  - Replace `KeywordMatcher` with `SemanticMatcher`

## 5. Tests
- [x] 5.1 Added 14 unit tests in `backend/tests/test_semantic_matcher.py` (all pass)
- [x] 5.2 Fixed pre-existing test in `test_api_match.py` (was asserting sync response from now-async route); all 22 tests pass
