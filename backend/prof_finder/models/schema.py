"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for legacy CLI users
    is_admin = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    professors = relationship("Professor", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', is_admin={self.is_admin})>"


class UserSettings(Base):
    """User settings model for storing API keys and preferences."""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # API configuration
    deepseek_api_key = Column(String(255))  # Encrypted in production
    deepseek_base_url = Column(String(500), default="https://api.deepseek.com/v1")

    # Crawler settings
    request_delay = Column(Integer, default=3)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id})>"


class UserProfile(Base):
    """User profile/resume model. A user can have multiple profiles."""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Profile metadata
    title = Column(String(200), nullable=False)  # e.g., "NLP方向申请简历"
    is_active = Column(Boolean, default=True)
    
    # Parsed content
    name = Column(String(100))  # Name from resume
    education = Column(JSON, default=list)  # [{degree, school, major, period}]
    research_experience = Column(JSON, default=list)  # [{title, organization, description, period}]
    projects = Column(JSON, default=list)  # [{name, description}]
    skills = Column(JSON, default=list)  # ["Python", "NLP", ...]
    
    # Raw content
    raw_content = Column(Text)
    source_format = Column(String(20))  # "markdown", "latex", "manual"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profiles")
    match_records = relationship("MatchRecord", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class Professor(Base):
    """Professor information model. Each user has their own professor pool."""

    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic info
    name = Column(String(200), nullable=False)
    affiliation = Column(String(500))  # University/Department
    email = Column(String(200))
    homepage = Column(String(500))
    
    # Google Scholar data
    google_scholar_id = Column(String(50))
    google_scholar_url = Column(String(500))
    
    # Academic data
    research_interests = Column(JSON, default=list)  # ["NLP", "Machine Learning"]
    publications = Column(JSON, default=list)  # [{title, year, citations, authors}]
    h_index = Column(Integer)
    total_citations = Column(Integer)

    # Semantic embedding (list[float], allenai-specter 768-dim, nullable)
    embedding = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="professors")
    match_records = relationship("MatchRecord", back_populates="professor", cascade="all, delete-orphan")

    # Unique constraint: same scholar ID per user
    __table_args__ = (
        UniqueConstraint("user_id", "google_scholar_id", name="uq_user_scholar"),
    )

    def __repr__(self) -> str:
        return f"<Professor(id={self.id}, name='{self.name}', affiliation='{self.affiliation}')>"


class MatchRecord(Base):
    """Match result between a user profile and a professor."""

    __tablename__ = "match_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False, index=True)
    
    # Match result
    score = Column(Float, nullable=False)  # 0-100
    match_reasons = Column(JSON, default=list)  # ["研究方向匹配: NLP", "技能匹配: Python"]
    
    # Generated letter
    letter_content = Column(Text)
    letter_generated_at = Column(DateTime)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="match_records")
    professor = relationship("Professor", back_populates="match_records")

    # Unique constraint: one match per profile-professor pair
    __table_args__ = (
        UniqueConstraint("user_profile_id", "professor_id", name="uq_profile_professor"),
    )

    def __repr__(self) -> str:
        return f"<MatchRecord(profile_id={self.user_profile_id}, professor_id={self.professor_id}, score={self.score})>"
