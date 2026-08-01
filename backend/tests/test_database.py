"""Database engine configuration tests."""

from __future__ import annotations

from sqlalchemy import text

from prof_finder.db.database import _BUSY_TIMEOUT_SECONDS


def test_wal_journal_mode_is_enabled(temp_db):
    """WAL keeps API reads working while a background task holds a write lock."""
    with temp_db.engine.connect() as conn:
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"


def test_busy_timeout_is_configured(temp_db):
    with temp_db.engine.connect() as conn:
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == _BUSY_TIMEOUT_SECONDS * 1000


def test_pragmas_apply_to_every_pooled_connection(temp_db):
    for _ in range(3):
        with temp_db.engine.connect() as conn:
            assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"


def test_a_reader_is_not_blocked_by_an_open_write_transaction(temp_db):
    """The rollback journal would block this; WAL must not."""
    from prof_finder.models.schema import User

    writer = temp_db.SessionLocal()
    reader = temp_db.SessionLocal()
    try:
        writer.add(User(username="writer", password_hash="x"))
        writer.flush()  # holds the write lock, uncommitted
        assert reader.query(User).count() == 0
    finally:
        writer.rollback()
        writer.close()
        reader.close()
