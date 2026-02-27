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
            # Add professors.embedding column if missing (added in semantic-matching change)
            result = conn.execute(text("PRAGMA table_info(professors)"))
            existing_columns = {row[1] for row in result}
            if "embedding" not in existing_columns:
                conn.execute(text("ALTER TABLE professors ADD COLUMN embedding JSON"))
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
