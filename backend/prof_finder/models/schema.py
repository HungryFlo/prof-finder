"""SQLAlchemy database models."""

from ..utils.time import utc_now
from typing import Optional
from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    LargeBinary,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    professors = relationship("Professor", back_populates="user", cascade="all, delete-orphan")
    source_inputs = relationship("SourceInput", back_populates="user", cascade="all, delete-orphan")
    experience_pools = relationship(
        "ExperiencePool", back_populates="user", cascade="all, delete-orphan"
    )
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', is_admin={self.is_admin})>"


class UserSettings(Base):
    """User settings model for storing API keys and preferences."""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # LLM API configuration (user-controlled provider, base URL, model)
    llm_provider = Column(String(20), default="openai")
    llm_api_key = Column(String(255))  # Stored in local SQLite; API returns masked value only
    llm_base_url = Column(String(500), default="https://api.deepseek.com/v1")
    llm_model = Column(String(100), default="deepseek-chat")
    # Legacy columns (migrated into llm_* on upgrade; still read as fallback)
    deepseek_api_key = Column(String(255))
    deepseek_base_url = Column(String(500))
    deepseek_model = Column(String(100))

    # Crawler settings
    request_delay = Column(Integer, default=3)

    # Auto professor-enrichment after manual save or Scholar sync (default all on)
    auto_enrich_on_save_fetch_publication_details = Column(Boolean, default=True)
    auto_enrich_on_save_paper_summaries = Column(Boolean, default=True)
    auto_enrich_on_save_research_profile = Column(Boolean, default=True)

    # Language preference for LLM-generated content
    profile_language = Column(String(10), default="zh")

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

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
    name_locales = Column(JSON, default=dict)  # optional {"zh", "en"} for letters / explicit forms
    education = Column(JSON, default=list)  # [{degree, school, major, period}]
    research_experience = Column(JSON, default=list)  # [{title, organization, description, period}]
    projects = Column(JSON, default=list)  # [{name, description}]
    skills = Column(JSON, default=list)  # ["Python", "NLP", ...]
    
    # Raw content
    raw_content = Column(Text)
    source_format = Column(String(20))  # "markdown", "latex", "manual"

    # Generated academic profile from multi-material intake
    profile_materials = Column(JSON, default=list)
    manual_inputs = Column(JSON, default=dict)
    academic_profile = Column(Text)
    profile_analysis = Column(JSON, default=dict)
    evidence_notes = Column(JSON, default=list)
    conflict_notes = Column(JSON, default=list)
    profile_generated_at = Column(DateTime)

    # Optional link to one experience pool (素材信息池)
    experience_pool_id = Column(
        Integer, ForeignKey("experience_pools.id"), nullable=True, index=True
    )
    
    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="profiles")
    match_records = relationship("MatchRecord", back_populates="profile", cascade="all, delete-orphan")
    experience_pool = relationship("ExperiencePool", back_populates="profiles")

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class ExperiencePool(Base):
    """User-owned experience material pool (信息池)."""

    __tablename__ = "experience_pools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    phase = Column(String(20), default="brainstorm")  # brainstorm|cluster|detail|compose

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="experience_pools")
    seeds = relationship(
        "ExperienceSeed", back_populates="pool", cascade="all, delete-orphan"
    )
    clusters = relationship(
        "ExperienceCluster", back_populates="pool", cascade="all, delete-orphan"
    )
    compositions = relationship(
        "PoolComposition", back_populates="pool", cascade="all, delete-orphan"
    )
    profiles = relationship("UserProfile", back_populates="experience_pool")

    def __repr__(self) -> str:
        return f"<ExperiencePool(id={self.id}, title='{self.title}')>"


class ExperienceCluster(Base):
    """A thematic cluster of experience seeds within a pool."""

    __tablename__ = "experience_clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey("experience_pools.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    note = Column(Text)
    color = Column(String(20))
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    pool = relationship("ExperiencePool", back_populates="clusters")
    seeds = relationship("ExperienceSeed", back_populates="cluster")

    def __repr__(self) -> str:
        return f"<ExperienceCluster(id={self.id}, title='{self.title}')>"


class ExperienceSeed(Base):
    """Short brainstorm fragment in an experience pool."""

    __tablename__ = "experience_seeds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey("experience_pools.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    status = Column(String(20), default="active")  # active|discarded
    cluster_id = Column(Integer, ForeignKey("experience_clusters.id"), nullable=True, index=True)
    standalone = Column(Boolean, default=False)  # keep for detail without clustering
    sort_order = Column(Integer, default=0)
    tags = Column(JSON, default=list)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    pool = relationship("ExperiencePool", back_populates="seeds")
    cluster = relationship("ExperienceCluster", back_populates="seeds")
    story = relationship(
        "ExperienceStory",
        back_populates="seed",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ExperienceSeed(id={self.id}, status='{self.status}')>"


class ExperienceStory(Base):
    """Detailed narrative for one retained seed (1:1)."""

    __tablename__ = "experience_stories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seed_id = Column(
        Integer, ForeignKey("experience_seeds.id"), nullable=False, unique=True, index=True
    )
    origin = Column(Text)
    process = Column(Text)
    outcome = Column(Text)
    problems = Column(Text)
    setbacks = Column(Text)
    knowledge = Column(Text)
    insights = Column(Text)
    freeform = Column(Text)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    seed = relationship("ExperienceSeed", back_populates="story")

    def __repr__(self) -> str:
        return f"<ExperienceStory(id={self.id}, seed_id={self.seed_id})>"


class PoolComposition(Base):
    """Document fragment composed from selected stories."""

    __tablename__ = "pool_compositions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey("experience_pools.id"), nullable=False, index=True)
    doc_type = Column(String(40), nullable=False)  # resume_bullet|personal_statement|research_plan|letter_snippet
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False, default="")
    source_story_ids = Column(JSON, default=list)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    pool = relationship("ExperiencePool", back_populates="compositions")

    def __repr__(self) -> str:
        return f"<PoolComposition(id={self.id}, doc_type='{self.doc_type}')>"


class University(Base):
    """University entity — reusable across multiple crawler configs for the same school."""

    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    full_name = Column(String(300), nullable=False)  # e.g. "西安交通大学"
    name_variants = Column(JSON, default=list)  # ["XJTU", "Xi'an Jiaotong University", "西交"]

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User")
    crawler_configs = relationship("UniversityCrawlerConfig", back_populates="university_ref")

    __table_args__ = (
        Index("ix_university_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<University(id={self.id}, full_name='{self.full_name}')>"


class UniversityCrawlerConfig(Base):
    """User-defined or built-in university crawler configuration."""

    __tablename__ = "university_crawler_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Identification
    name = Column(String(200), nullable=False)  # e.g. "Stanford CS"
    university = Column(String(300), nullable=False)  # e.g. "Stanford University"
    department = Column(String(300))  # e.g. "Computer Science"

    # Crawl target
    list_url = Column(String(1000), nullable=False)  # Professor list page URL

    # Extraction mode: "css" or "llm"
    extraction_mode = Column(String(10), nullable=False, default="css")

    # CSS selector config (JSON, only used when extraction_mode="css")
    css_selectors = Column(JSON, default=dict)

    # Affiliation string to assign to all crawled professors
    affiliation = Column(String(500))

    # Status
    is_builtin = Column(Boolean, default=False)
    builtin_crawler_id = Column(String(50))  # e.g. "xjtu-cs" if is_builtin

    # Link to University for reusable name variants
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User")
    university_ref = relationship("University", back_populates="crawler_configs")

    __table_args__ = (
        Index("ix_crawler_config_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UniversityCrawlerConfig(id={self.id}, name='{self.name}')>"


class Professor(Base):
    """Professor information model. Each user has their own professor pool."""

    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic info
    name = Column(String(200), nullable=False)
    name_locales = Column(JSON, default=dict)  # optional {"zh", "en"} — not set by crawler
    affiliation = Column(String(500))  # University/Department
    email = Column(String(200))
    homepage = Column(String(500))
    
    # Google Scholar data
    google_scholar_id = Column(String(50))
    google_scholar_url = Column(String(500))

    # DBLP data
    dblp_pid = Column(String(100), index=True)
    dblp_url = Column(String(500))
    dblp_enrichment_status = Column(String(20))
    dblp_candidates = Column(JSON, nullable=True)

    # Source tracking for school-crawler professors
    source = Column(String(20), default="manual")  # "school_crawler" | "google_scholar" | "manual"
    enrichment_status = Column(String(20))  # "pending" | "matched" | "not_found" | "ambiguous" | "user_confirmed"
    scholar_candidates = Column(JSON, nullable=True)  # [{scholar_id, name, affiliation, score, email_domain_match}]
    
    # Academic data
    research_interests = Column(JSON, default=list)  # ["NLP", "Machine Learning"]
    publications = Column(JSON, default=list)  # [{title, year, citations, authors}]
    paper_summaries = Column(JSON, default=list)  # [{title, summary, keywords, source_input_id, source_type}]
    h_index = Column(Integer)
    total_citations = Column(Integer)
    manual_notes = Column(Text)

    # Semantic embedding (float32 BLOB, Qwen3-Embedding-0.6B 1024-dim, nullable)
    embedding = Column(LargeBinary, nullable=True)

    # Generated professor research profile
    research_profile = Column(Text)
    research_profile_analysis = Column(JSON, default=dict)
    research_profile_sources = Column(JSON, default=list)
    research_profile_evidence = Column(JSON, default=list)
    research_profile_conflicts = Column(JSON, default=list)
    research_profile_generated_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="professors")
    match_records = relationship("MatchRecord", back_populates="professor", cascade="all, delete-orphan")
    source_inputs = relationship("SourceInput", back_populates="professor")

    # Unique constraint: same scholar ID per user + composite index for crawl dedup
    __table_args__ = (
        UniqueConstraint("user_id", "google_scholar_id", name="uq_user_scholar"),
        Index("ix_professor_user_affiliation", "user_id", "affiliation"),
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
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    profile = relationship("UserProfile", back_populates="match_records")
    professor = relationship("Professor", back_populates="match_records")

    # Unique constraint: one match per profile-professor pair + composite index
    __table_args__ = (
        UniqueConstraint("user_profile_id", "professor_id", name="uq_profile_professor"),
        Index("ix_match_profile_professor", "user_profile_id", "professor_id"),
    )

    def __repr__(self) -> str:
        return f"<MatchRecord(profile_id={self.user_profile_id}, professor_id={self.professor_id}, score={self.score})>"


class SourceInput(Base):
    """Reusable source input model for PDF/ArXiv enrichment."""

    __tablename__ = "source_inputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=True, index=True)

    source_type = Column(String(20), nullable=False)  # "arxiv" (legacy rows may have "pdf")
    original_name = Column(String(500))
    source_url = Column(String(1000))
    canonical_id = Column(String(50))
    title = Column(String(500))
    abstract = Column(Text)
    pdf_url = Column(String(1000))
    downloaded_pdf_path = Column(String(1000))

    extracted_text = Column(Text)
    extracted_markdown = Column(Text)

    status = Column(String(20), default="pending")  # pending/succeeded/failed
    error_message = Column(Text)
    metadata_only = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="source_inputs")
    professor = relationship("Professor", back_populates="source_inputs")

    def __repr__(self) -> str:
        return f"<SourceInput(id={self.id}, source_type={self.source_type}, status={self.status})>"
