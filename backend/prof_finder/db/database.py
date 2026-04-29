"""Database connection and session management."""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from ..config import settings
from ..models.schema import Base, User


class Database:
    """Database manager for Prof-Finder."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. Uses settings if not provided.
        """
        self.db_path = db_path or settings.database_path
        
        # Ensure directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False},
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        
        # Initialize tables
        self._init_tables()

    def _init_tables(self) -> None:
        """Create all tables if they don't exist, then apply incremental migrations."""
        Base.metadata.create_all(bind=self.engine)
        self._migrate()

    def _migrate(self) -> None:
        """Apply incremental schema changes that create_all cannot handle."""
        with self.engine.connect() as conn:
            # Add generated student profile columns for existing deployments.
            profile_result = conn.execute(text("PRAGMA table_info(user_profiles)"))
            profile_columns = {row[1] for row in profile_result}
            profile_additions = {
                "profile_materials": "JSON",
                "manual_inputs": "JSON",
                "academic_profile": "TEXT",
                "profile_analysis": "JSON",
                "evidence_notes": "JSON",
                "conflict_notes": "JSON",
                "profile_generated_at": "DATETIME",
            }
            for column, sql_type in profile_additions.items():
                if column not in profile_columns:
                    conn.execute(
                        text(f"ALTER TABLE user_profiles ADD COLUMN {column} {sql_type}")
                    )
                    conn.commit()

            # Add professors.embedding column if missing (added in semantic-matching change)
            result = conn.execute(text("PRAGMA table_info(professors)"))
            existing_columns = {row[1] for row in result}
            if "embedding" not in existing_columns:
                conn.execute(text("ALTER TABLE professors ADD COLUMN embedding JSON"))
                conn.commit()
            if "manual_notes" not in existing_columns:
                conn.execute(text("ALTER TABLE professors ADD COLUMN manual_notes TEXT"))
                conn.commit()
            if "paper_summaries" not in existing_columns:
                conn.execute(text("ALTER TABLE professors ADD COLUMN paper_summaries JSON"))
                conn.commit()

            prof_research_additions = {
                "research_profile": "TEXT",
                "research_profile_analysis": "JSON",
                "research_profile_sources": "JSON",
                "research_profile_evidence": "JSON",
                "research_profile_conflicts": "JSON",
                "research_profile_generated_at": "DATETIME",
            }
            for column, sql_type in prof_research_additions.items():
                if column not in existing_columns:
                    conn.execute(
                        text(f"ALTER TABLE professors ADD COLUMN {column} {sql_type}")
                    )
                    conn.commit()

            # Backfill source_inputs incremental columns for existing deployments.
            source_table_exists = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='source_inputs'"
                )
            ).fetchone()
            if source_table_exists:
                source_cols = {
                    row[1] for row in conn.execute(text("PRAGMA table_info(source_inputs)"))
                }
                if "metadata_only" not in source_cols:
                    conn.execute(
                        text(
                            "ALTER TABLE source_inputs ADD COLUMN metadata_only BOOLEAN DEFAULT 0"
                        )
                    )
                    conn.commit()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup.
        
        Usage:
            with db.session() as session:
                session.query(User).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_or_create_user(self, username: str) -> User:
        """Get existing user or create new one.
        
        Args:
            username: Username to find or create.
            
        Returns:
            User instance (detached from session, safe to use outside).
        """
        with self.session() as session:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                user = User(username=username)
                session.add(user)
                session.commit()
                session.refresh(user)
            
            # Expunge to detach from session and make usable outside
            session.expunge(user)
            return user


# Global database instance (lazy initialization)
_db: Optional[Database] = None


def get_db() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
    return _db
