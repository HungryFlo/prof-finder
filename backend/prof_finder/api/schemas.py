"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Any, Literal, Annotated

from pydantic import BaseModel, Field, field_validator, BeforeValidator

_ALLOWED_NAME_LOCALE_KEYS = frozenset({"zh", "en"})


def _parse_name_locales_input(v: Any) -> Optional[dict[str, str]]:
    """Validate optional name_locales body; None means omit from update."""
    if v is None:
        return None
    if not isinstance(v, dict):
        raise ValueError("name_locales must be an object")
    out: dict[str, str] = {}
    for k, val in v.items():
        if k not in _ALLOWED_NAME_LOCALE_KEYS:
            raise ValueError(f"Invalid locale key: {k}")
        if val is None:
            continue
        s = str(val).strip()
        if s:
            out[str(k)] = s[:200]
    return out


def _response_name_locales(v: Any) -> dict[str, str]:
    if not v or not isinstance(v, dict):
        return {}
    return {str(k): str(val) for k, val in v.items() if k in _ALLOWED_NAME_LOCALE_KEYS and val}


NameLocalesDict = Annotated[dict[str, str], BeforeValidator(_response_name_locales)]


# ============= Auth Schemas =============


class UserRegister(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """User login request."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class TokenRefresh(BaseModel):
    """Token refresh request."""

    refresh_token: str


class PasswordChange(BaseModel):
    """Password change request."""

    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class PasswordReset(BaseModel):
    """Admin password reset request."""

    new_password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    """User info response."""

    id: int
    username: str
    is_admin: bool
    must_change_password: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response for admin."""

    id: int
    username: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Profile Schemas =============


class EducationItem(BaseModel):
    """Education entry."""

    degree: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    period: Optional[str] = None


class ResearchItem(BaseModel):
    """Research experience entry."""

    title: Optional[str] = None
    organization: Optional[str] = None
    description: Optional[str] = None
    period: Optional[str] = None


class ProjectItem(BaseModel):
    """Project entry."""

    name: Optional[str] = None
    description: Optional[str] = None


class ProfileCreate(BaseModel):
    """Profile creation request."""

    title: str = Field(..., min_length=1, max_length=200)
    name: Optional[str] = None
    name_locales: dict[str, str] = Field(default_factory=dict)
    education: List[EducationItem] = []
    research_experience: List[ResearchItem] = []
    projects: List[ProjectItem] = []
    skills: List[str] = []
    raw_content: Optional[str] = None
    source_format: str = "manual"

    @field_validator("name_locales", mode="before")
    @classmethod
    def _validate_name_locales_create(cls, v: Any) -> dict[str, str]:
        if v is None:
            return {}
        p = _parse_name_locales_input(v)
        return p if p is not None else {}


class ProfileUpdate(BaseModel):
    """Profile update request."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    name: Optional[str] = None
    name_locales: Optional[dict] = None
    education: Optional[List[EducationItem]] = None
    research_experience: Optional[List[ResearchItem]] = None
    projects: Optional[List[ProjectItem]] = None
    skills: Optional[List[str]] = None

    @field_validator("name_locales", mode="before")
    @classmethod
    def _validate_name_locales_update(cls, v: Any) -> Optional[dict[str, str]]:
        return _parse_name_locales_input(v)


class ProfileResponse(BaseModel):
    """Profile response."""

    id: int
    title: str
    name: Optional[str]
    name_locales: NameLocalesDict = Field(default_factory=dict)
    is_active: bool
    education: List[dict]
    research_experience: List[dict]
    projects: List[dict]
    skills: List[str]
    source_format: Optional[str]
    profile_materials: Optional[List[dict]] = None
    manual_inputs: Optional[dict] = None
    academic_profile: Optional[str] = None
    profile_analysis: Optional[dict] = None
    evidence_notes: Optional[List[Any]] = None
    conflict_notes: Optional[List[Any]] = None
    profile_generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchDeleteRequest(BaseModel):
    """Batch delete request."""

    ids: List[int]


class ProfileChatRequest(BaseModel):
    """AI interviewer chat message request."""

    message: str
    history: List[dict] = []
    locale: Literal["zh", "en"] = "zh"


class ProfileChatResponse(BaseModel):
    """AI interviewer chat message response."""

    reply: str


class ProfileChatRefineRequest(BaseModel):
    """Request to regenerate profile from chat Q&A."""

    history: List[dict] = []


# ============= Professor Schemas =============


class PublicationItem(BaseModel):
    """Publication entry."""

    title: str
    year: Optional[int] = None
    citations: Optional[int] = None
    authors: Optional[str] = None


class ProfessorCreate(BaseModel):
    """Professor creation request (manual)."""

    name: str = Field(..., min_length=1, max_length=200)
    name_locales: dict[str, str] = Field(default_factory=dict)
    affiliation: Optional[str] = None
    email: Optional[str] = None
    homepage: Optional[str] = None
    research_interests: List[str] = []
    manual_notes: Optional[str] = None
    paper_summaries: Optional[List[dict]] = None

    @field_validator("name_locales", mode="before")
    @classmethod
    def _validate_name_locales_prof_create(cls, v: Any) -> dict[str, str]:
        if v is None:
            return {}
        p = _parse_name_locales_input(v)
        return p if p is not None else {}


class ProfessorUpdate(BaseModel):
    """Professor update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    name_locales: Optional[dict] = None
    affiliation: Optional[str] = None
    email: Optional[str] = None
    homepage: Optional[str] = None
    research_interests: Optional[List[str]] = None
    manual_notes: Optional[str] = None
    paper_summaries: Optional[List[dict]] = None

    @field_validator("name_locales", mode="before")
    @classmethod
    def _validate_name_locales_prof_update(cls, v: Any) -> Optional[dict[str, str]]:
        return _parse_name_locales_input(v)


class ProfessorScholarAdd(BaseModel):
    """Add professor by Google Scholar URL."""

    url: str


class ProfessorSearchRequest(BaseModel):
    """Search Google Scholar request."""

    query: str
    limit: int = Field(default=10, ge=1, le=50)


class ProfessorResponse(BaseModel):
    """Professor response."""

    id: int
    name: str
    name_locales: NameLocalesDict = Field(default_factory=dict)
    affiliation: Optional[str]
    email: Optional[str]
    homepage: Optional[str]
    google_scholar_id: Optional[str]
    google_scholar_url: Optional[str]
    research_interests: List[str]
    publications: List[dict]
    paper_summaries: Optional[List[dict]] = None
    h_index: Optional[int]
    total_citations: Optional[int]
    manual_notes: Optional[str]
    research_profile: Optional[str] = None
    research_profile_analysis: Optional[dict] = None
    research_profile_sources: Optional[List[dict]] = None
    research_profile_evidence: Optional[List[Any]] = None
    research_profile_conflicts: Optional[List[Any]] = None
    research_profile_generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    enrichment_task_id: Optional[str] = None
    enrichment_task_total: Optional[int] = None

    class Config:
        from_attributes = True


class ProfessorListResponse(BaseModel):
    """Professor list item (without full publications)."""

    id: int
    name: str
    affiliation: Optional[str]
    research_interests: List[str]
    h_index: Optional[int]
    publication_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScholarSearchResult(BaseModel):
    """Google Scholar search result."""

    name: str
    affiliation: Optional[str]
    scholar_id: str
    scholar_url: str
    interests: List[str]
    citations: Optional[int]


class SourceInputArxivCreate(BaseModel):
    """Create source input from ArXiv link."""

    url: str


class SourceInputResponse(BaseModel):
    """Source input response."""

    id: int
    source_type: str
    original_name: Optional[str]
    source_url: Optional[str]
    canonical_id: Optional[str]
    title: Optional[str]
    abstract: Optional[str]
    extracted_markdown: Optional[str]
    status: str
    error_message: Optional[str]
    metadata_only: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfessorEditPreviewRequest(BaseModel):
    """Preview professor edit request."""

    manual_patch: Optional[ProfessorUpdate] = None
    source_input_ids: List[int] = []


class ProfessorEditApplyRequest(BaseModel):
    """Apply professor edit request."""

    manual_patch: Optional[ProfessorUpdate] = None
    source_input_ids: List[int] = []


class ProfessorSourceSummaryRequest(BaseModel):
    """Start background paper summary generation for source inputs."""

    source_input_ids: List[int] = []


class ProfessorEditPreviewResponse(BaseModel):
    """Preview result for professor edits."""

    manual_patch_applied: dict
    source_suggestions: dict


# ============= Match Schemas =============


class MatchRunResponse(BaseModel):
    """Match run response."""

    message: str
    total_professors: int
    results_count: int


class MatchResultResponse(BaseModel):
    """Match result response."""

    professor_id: int
    professor_name: str
    professor_affiliation: Optional[str]
    score: float
    match_reasons: List[str]
    letter_generated: bool

    class Config:
        from_attributes = True


class MatchDetailResponse(BaseModel):
    """Detailed match result."""

    professor_id: int
    professor_name: str
    professor_affiliation: Optional[str]
    professor_interests: List[str]
    score: float
    match_reasons: List[str]
    letter_content: Optional[str]
    letter_generated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============= Letter Schemas =============


class LetterGenerateResponse(BaseModel):
    """Letter generation response."""

    professor_id: int
    professor_name: str
    content: str
    generated_at: datetime


class LetterUpdate(BaseModel):
    """Letter update request."""

    content: str


class LetterResponse(BaseModel):
    """Letter response."""

    professor_id: int
    professor_name: str
    content: Optional[str]
    generated_at: Optional[datetime]
    is_generated: bool


class BatchLetterRequest(BaseModel):
    """Batch letter generation request."""

    professor_ids: Optional[List[int]] = None
    top: Optional[int] = Field(None, ge=1, le=50)
    language: Literal["zh", "en"]


# ============= Settings Schemas =============


class UserSettingsUpdate(BaseModel):
    """User settings update request."""

    deepseek_api_key: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    request_delay: Optional[int] = Field(None, ge=1, le=60)
    auto_enrich_on_save_fetch_publication_details: Optional[bool] = None
    auto_enrich_on_save_paper_summaries: Optional[bool] = None
    auto_enrich_on_save_research_profile: Optional[bool] = None


class UserSettingsResponse(BaseModel):
    """User settings response."""

    deepseek_api_key_masked: Optional[str]  # Only show first/last 4 chars
    deepseek_base_url: str
    request_delay: int
    auto_enrich_on_save_fetch_publication_details: bool = True
    auto_enrich_on_save_paper_summaries: bool = True
    auto_enrich_on_save_research_profile: bool = True

    class Config:
        from_attributes = True


# ============= Task Schemas =============


class TaskStartResponse(BaseModel):
    """Task start response."""

    task_id: str
    message: str
    total: int = 0


class TaskCancelResponse(BaseModel):
    """Task cancel response."""

    message: str
    completed_count: int


class TaskListItemResponse(BaseModel):
    """Summary of a task returned by GET /api/tasks."""

    task_id: str
    task_type: str
    task_name: str
    status: str
    current: int
    total: int
    message: str
    error_message: str
    cancel_requested: bool = False


class BatchCrawlRequest(BaseModel):
    """Batch crawl request."""

    scholar_urls: List[str]


# ============= University Crawler Schemas =============


class UniversityCrawlerInfo(BaseModel):
    """Metadata for one registered university crawler (for frontend selector)."""

    university_id: str
    display_name: str


class UniversityCrawlRequest(BaseModel):
    """Request body for starting a university crawl task."""

    university_id: str


# ============= Common Schemas =============


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str
