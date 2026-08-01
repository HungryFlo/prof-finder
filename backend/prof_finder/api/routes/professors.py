"""Professor management API routes."""

import asyncio
import hashlib
import json
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, defer
from sqlalchemy.orm.attributes import flag_modified

from ...crawler.dblp import DblpClient, dblp_profile_url, extract_dblp_pid_from_url
from ...crawler.scholar import ScholarCrawler
from ...llm import PaperSummarizer
from ...models.schema import (
    Professor,
    SourceInput,
    University,
    UniversityCrawlerConfig,
    User,
    UserSettings,
)
from ...utils.publication_merge import merge_publications
from ...utils.scholar_match_context import resolve_scholar_match_params
from ...utils.time import utc_now
from ..deps import get_current_user, get_db_session
from ..enrichment_prefs import (
    flags_from_user_settings_row,
    planned_enrichment_step_count_for_professor,
)
from ..errors import ErrorCode, raise_api_error
from ..schemas import (
    BatchDeleteRequest,
    CrawlerConfigCreate,
    CrawlerConfigResponse,
    CrawlerConfigUpdate,
    CrawlerConfiguredCrawlRequest,
    CrawlerTestRequest,
    CrawlerTestResponse,
    DblpCandidateConfirm,
    DblpSearchResult,
    MessageResponse,
    PaginatedResponse,
    ProfessorCreate,
    ProfessorDblpAdd,
    ProfessorEditApplyRequest,
    ProfessorEditPreviewRequest,
    ProfessorEditPreviewResponse,
    ProfessorNameCollision,
    ProfessorResponse,
    ProfessorScholarAdd,
    ProfessorSearchRequest,
    ProfessorSourceSummaryRequest,
    ProfessorUpdate,
    TaskStartResponse,
    UniversityCrawlerInfo,
    UniversityCrawlRequest,
)
from ..source_input_service import (
    build_paper_summary_from_source,
    keep_non_scholar_paper_summaries,
    keep_paper_summaries_excluding,
)
from ..task_manager import (
    cleanup_old_tasks,
    create_task,
    enqueue_task,
    extract_scholar_id_from_url,
)

router = APIRouter(prefix="/professors", tags=["教授管理"])

# Cache for test crawl results, keyed by config hash.
# Allows formal crawl to reuse test results without re-fetching pages.
# Structure: {config_hash: {"results": [...], "timestamp": float}}
_test_crawl_cache: dict[str, dict] = {}
_TEST_CRAWL_CACHE_TTL = 1800  # 30 minutes

_PROFESSOR_SORT_COLUMNS = {
    "name": Professor.name,
    "affiliation": Professor.affiliation,
    "h_index": Professor.h_index,
    "created_at": Professor.created_at,
}


_PROFESSOR_LIST_DEFER = (
    Professor.publications,
    Professor.embedding,
    Professor.paper_summaries,
    Professor.research_profile,
    Professor.research_profile_analysis,
    Professor.research_profile_sources,
    Professor.research_profile_evidence,
    Professor.research_profile_conflicts,
    Professor.scholar_candidates,
    Professor.dblp_candidates,
    Professor.manual_notes,
)


def get_professor_list_response(professor: Professor, publication_count: int) -> dict:
    """Convert Professor to list response format."""
    return {
        "id": professor.id,
        "name": professor.name,
        "affiliation": professor.affiliation,
        "research_interests": professor.research_interests or [],
        "h_index": professor.h_index,
        "publication_count": publication_count,
        "source": professor.source,
        "enrichment_status": professor.enrichment_status,
        "google_scholar_id": professor.google_scholar_id,
        "dblp_pid": professor.dblp_pid,
        "dblp_enrichment_status": professor.dblp_enrichment_status,
        "created_at": professor.created_at,
    }


@router.get("", response_model=PaginatedResponse)
def list_professors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    affiliation: Optional[str] = None,
    interest: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List professors with pagination, filtering, search, and sorting."""
    query = session.query(Professor).filter(Professor.user_id == current_user.id)

    # Apply filters
    if affiliation:
        query = query.filter(Professor.affiliation.ilike(f"%{affiliation}%"))
    if interest:
        query = query.filter(Professor.research_interests.cast(str).ilike(f"%{interest}%"))
    if search:
        query = query.filter(
            or_(
                Professor.name.ilike(f"%{search}%"),
                Professor.affiliation.ilike(f"%{search}%"),
            )
        )

    # Get total count
    total = query.count()

    # Apply sorting
    order_col = _PROFESSOR_SORT_COLUMNS.get(sort_by, Professor.created_at)
    order_func = order_col.asc if sort_order == "asc" else order_col.desc
    publication_count = func.coalesce(func.json_array_length(Professor.publications), 0)

    # Apply pagination — defer heavy JSON/BLOB columns; count pubs in SQL.
    rows = (
        query.options(*(defer(col) for col in _PROFESSOR_LIST_DEFER))
        .add_columns(publication_count)
        .order_by(order_func())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse(
        items=[get_professor_list_response(p, int(pub_count or 0)) for p, pub_count in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/affiliations", response_model=List[str])
def list_affiliations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Return distinct non-null affiliations for the current user."""
    rows = (
        session.query(Professor.affiliation)
        .filter(Professor.user_id == current_user.id, Professor.affiliation.isnot(None), Professor.affiliation != "")
        .distinct()
        .all()
    )
    return sorted({r[0] for r in rows if r[0]})


@router.get("/name-collisions", response_model=List[ProfessorNameCollision])
def list_professor_name_collisions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List groups of professors with the same name at the same university.

    Uses university name variants (and pinyin for Chinese/English names) to
    cluster likely duplicates for manual review.
    """
    from ...utils.professor_dedup import find_name_collision_groups

    professors = (
        session.query(Professor)
        .filter(Professor.user_id == current_user.id)
        .order_by(Professor.name)
        .all()
    )
    universities = (
        session.query(University)
        .filter(University.user_id == current_user.id)
        .all()
    )
    groups = find_name_collision_groups(professors, universities)
    return [ProfessorNameCollision(**g) for g in groups]


@router.post("", response_model=ProfessorResponse, status_code=status.HTTP_201_CREATED)
def create_professor(
    data: ProfessorCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Create a professor manually.

    Args:
        data: Professor data.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Created professor.
    """
    professor = Professor(
        user_id=current_user.id,
        name=data.name,
        name_locales=data.name_locales or {},
        affiliation=data.affiliation,
        email=data.email,
        homepage=data.homepage,
        research_interests=data.research_interests,
        manual_notes=data.manual_notes,
        publications=[],
        paper_summaries=data.paper_summaries or [],
    )
    if not (data.name_locales or {}):
        from ...utils.name_locales import apply_inferred_locales_from_name

        apply_inferred_locales_from_name(professor)
    session.add(professor)
    session.flush()
    session.refresh(professor)

    settings_row = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )
    flags = flags_from_user_settings_row(settings_row)
    enrich_planned = planned_enrichment_step_count_for_professor(professor, flags)

    extra: dict = {}
    if enrich_planned > 0:
        enrich_task = create_task(
            "professor-enrichment",
            "教授信息增强",
            current_user.id,
            total=enrich_planned,
        )
        enqueue_task("professor-enrichment", enrich_task.task_id, professor_id=professor.id)
        extra["enrichment_task_id"] = enrich_task.task_id
        extra["enrichment_task_total"] = enrich_planned

    base = ProfessorResponse.model_validate(professor)
    return base.model_copy(update=extra)


@router.post("/scholar", response_model=TaskStartResponse)
def add_professor_by_scholar(
    data: ProfessorScholarAdd,
    current_user: User = Depends(get_current_user),
):
    """Start an async task to add a professor by Google Scholar URL.

    Args:
        data: Scholar URL.
        current_user: Authenticated user.

    Returns:
        Task ID for SSE progress tracking.
    """
    try:
        extract_scholar_id_from_url(data.url)
    except ValueError as e:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.BAD_REQUEST, str(e))

    cleanup_old_tasks()
    task = create_task(
        task_type="single-crawl",
        task_name="爬取教授",
        user_id=current_user.id,
        total=1,
    )
    enqueue_task("single-crawl", task.task_id, data.url)

    return TaskStartResponse(task_id=task.task_id, message="爬取任务已启动")


_dblp_cache: dict = {}
_DBLP_CACHE_TTL = 300


@router.post("/dblp/search", response_model=List[DblpSearchResult])
async def search_dblp(
    data: ProfessorSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search DBLP for authors."""
    cache_key = f"dblp:{data.query}:{data.limit}"
    cached = _dblp_cache.get(cache_key)
    if cached and (time.time() - cached[0]) < _DBLP_CACHE_TTL:
        return cached[1]

    client = DblpClient()
    try:
        results = await asyncio.to_thread(client.search_author, data.query, data.limit)
    except Exception as e:
        raise_api_error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.DBLP_SEARCH_FAILED, f"DBLP 搜索失败: {str(e)}")

    result_list = [
        DblpSearchResult(
            name=r["name"],
            pid=r["pid"],
            url=r["url"],
            affiliations=r.get("affiliations") or [],
        )
        for r in results
    ]
    _dblp_cache[cache_key] = (time.time(), result_list)
    return result_list


@router.post("/dblp", response_model=TaskStartResponse)
def add_professor_by_dblp(
    data: ProfessorDblpAdd,
    current_user: User = Depends(get_current_user),
):
    """Start async task to add/link professor from DBLP profile URL."""
    try:
        extract_dblp_pid_from_url(data.url)
    except ValueError as e:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.BAD_REQUEST, str(e))

    cleanup_old_tasks()
    task = create_task(
        task_type="single-dblp-crawl",
        task_name="爬取 DBLP 教授",
        user_id=current_user.id,
        total=1,
    )
    enqueue_task("single-dblp-crawl", task.task_id, data.url)
    return TaskStartResponse(task_id=task.task_id, message="DBLP 爬取任务已启动")


@router.get("/university-crawlers", response_model=List[UniversityCrawlerInfo])
def list_university_crawlers(
    current_user: User = Depends(get_current_user),
):
    """Return metadata for all registered university crawlers.

    Used by the frontend to populate the university selector modal.
    """
    from ...crawler.universities.registry import get_crawler_info_list

    return [
        UniversityCrawlerInfo(university_id=item["university_id"], display_name=item["display_name"])
        for item in get_crawler_info_list()
    ]


@router.post("/crawl-university", response_model=TaskStartResponse)
def crawl_university(
    data: UniversityCrawlRequest,
    current_user: User = Depends(get_current_user),
):
    """Start a background task to crawl professors from a university department website.

    Args:
        data: Request body containing the ``university_id``.
        current_user: Authenticated user.

    Returns:
        Task ID for SSE progress tracking.
    """
    from ...crawler.universities.registry import REGISTRY

    if data.university_id not in REGISTRY:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.UNIVERSITY_UNSUPPORTED, f"不支持该院校: {data.university_id}")

    crawler_cls = REGISTRY[data.university_id]
    display_name = crawler_cls.display_name

    cleanup_old_tasks()
    task = create_task(
        task_type="university-crawl",
        task_name=f"爬取 {display_name}",
        user_id=current_user.id,
        total=0,
    )
    enqueue_task("university-crawl", task.task_id, data.university_id)

    return TaskStartResponse(task_id=task.task_id, message=f"已启动爬取任务：{display_name}")


# ---- Crawler Config CRUD ----


@router.get("/crawler-configs", response_model=List[CrawlerConfigResponse])
def list_crawler_configs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List all crawler configs (user-defined + built-in)."""
    # User-defined configs
    user_configs = (
        session.query(UniversityCrawlerConfig)
        .filter(UniversityCrawlerConfig.user_id == current_user.id)
        .order_by(UniversityCrawlerConfig.created_at.desc())
        .all()
    )

    # Built-in configs from registry
    from ...crawler.universities.registry import REGISTRY

    builtin_configs = []
    for uid, crawler_cls in REGISTRY.items():
        existing = (
            session.query(UniversityCrawlerConfig)
            .filter(
                UniversityCrawlerConfig.user_id == current_user.id,
                UniversityCrawlerConfig.is_builtin.is_(True),
                UniversityCrawlerConfig.builtin_crawler_id == uid,
            )
            .first()
        )
        if not existing:
            builtin_configs.append(
                CrawlerConfigResponse(
                    id=-1,  # sentinel for built-in
                    name=crawler_cls.display_name,
                    university=crawler_cls.university,
                    department=crawler_cls.department,
                    list_url="",
                    extraction_mode="css",
                    css_selectors=None,
                    affiliation=crawler_cls.university,
                    is_builtin=True,
                    builtin_crawler_id=uid,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
            )

    return [CrawlerConfigResponse.model_validate(c) for c in user_configs] + builtin_configs


@router.post("/crawler-configs", response_model=CrawlerConfigResponse, status_code=status.HTTP_201_CREATED)
def create_crawler_config(
    data: CrawlerConfigCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Create a new custom university crawler configuration.

    If ``university_id`` is not provided, automatically finds or creates a
    University record from the ``university`` text field so that Scholar
    matching can work out of the box.
    """
    university_id = data.university_id

    # Auto-link to a University record when not explicitly provided
    if not university_id and data.university:
        uni = (
            session.query(University)
            .filter(
                University.user_id == current_user.id,
                University.full_name == data.university,
            )
            .first()
        )
        if not uni:
            uni = University(
                user_id=current_user.id,
                full_name=data.university,
                name_variants=[],
            )
            session.add(uni)
            session.flush()
        university_id = uni.id

        # Generate name variants in background if missing
        if not uni.name_variants:
            _generate_variants_background(uni.id, data.university)

    config = UniversityCrawlerConfig(
        user_id=current_user.id,
        name=data.name,
        university=data.university,
        department=data.department,
        list_url=data.list_url,
        extraction_mode=data.extraction_mode,
        css_selectors=data.css_selectors or {},
        affiliation=data.affiliation,
        university_id=university_id,
    )
    session.add(config)
    session.flush()
    session.refresh(config)
    return config


def _generate_variants_background(university_id: int, full_name: str):
    """Generate university name variants via LLM in a background thread."""
    import threading

    from ...db.database import get_db
    from .universities import _generate_name_variants

    def _run():
        try:
            loop = asyncio.new_event_loop()
            variants = loop.run_until_complete(_generate_name_variants(full_name))
            loop.close()

            if variants:
                db = get_db()
                with db.session() as session:
                    uni = session.query(University).filter(University.id == university_id).first()
                    if uni:
                        uni.name_variants = variants
                        session.commit()
        except Exception:
            pass  # best-effort; variants can be set manually later

    threading.Thread(target=_run, daemon=True).start()


@router.put("/crawler-configs/{config_id}", response_model=CrawlerConfigResponse)
def update_crawler_config(
    config_id: int,
    data: CrawlerConfigUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update an existing crawler configuration."""
    config = (
        session.query(UniversityCrawlerConfig)
        .filter(
            UniversityCrawlerConfig.id == config_id,
            UniversityCrawlerConfig.user_id == current_user.id,
        )
        .first()
    )
    if not config:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.CONFIG_NOT_FOUND, "配置不存在")

    if data.name is not None:
        config.name = data.name
    if data.university is not None:
        config.university = data.university
    if data.department is not None:
        config.department = data.department
    if data.list_url is not None:
        config.list_url = data.list_url
    if data.extraction_mode is not None:
        config.extraction_mode = data.extraction_mode
    if data.css_selectors is not None:
        config.css_selectors = data.css_selectors
    if data.affiliation is not None:
        config.affiliation = data.affiliation
    if data.university_id is not None:
        config.university_id = data.university_id

    session.flush()
    session.refresh(config)
    return config


@router.delete("/crawler-configs/{config_id}", response_model=MessageResponse)
def delete_crawler_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Delete a crawler configuration."""
    config = (
        session.query(UniversityCrawlerConfig)
        .filter(
            UniversityCrawlerConfig.id == config_id,
            UniversityCrawlerConfig.user_id == current_user.id,
        )
        .first()
    )
    if not config:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.CONFIG_NOT_FOUND, "配置不存在")

    session.delete(config)
    return MessageResponse(message="爬虫配置已删除")


def _compute_crawl_cache_key(user_id: int, list_url: str, extraction_mode: str,
                              css_selectors: dict | None, affiliation: str | None) -> str:
    """Compute a deterministic cache key from crawl parameters."""
    raw = json.dumps({
        "user_id": user_id,
        "list_url": list_url,
        "extraction_mode": extraction_mode,
        "css_selectors": css_selectors or {},
        "affiliation": affiliation or "",
    }, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached_test_results(cache_key: str) -> list[dict] | None:
    """Return cached test crawl results if still valid, else None."""
    entry = _test_crawl_cache.get(cache_key)
    if not entry:
        return None
    if time.time() - entry["timestamp"] > _TEST_CRAWL_CACHE_TTL:
        del _test_crawl_cache[cache_key]
        return None
    return entry["results"]


@router.post("/crawler-configs/test", response_model=CrawlerTestResponse)
async def test_crawler_config(
    data: CrawlerTestRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Test a crawler configuration by extracting a sample without saving.

    Only crawls the first page and returns up to 5 results for preview.
    """
    from ...config import settings as app_settings
    from ...crawler.crawl4ai_engine.generic_crawler import GenericUniversityCrawler
    from ...llm.config import resolve_llm_config

    user_settings = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )
    llm_config = resolve_llm_config(user_settings, app_settings)

    crawler = GenericUniversityCrawler.from_dict({
        "name": data.name or "Test",
        "university": data.university or "",
        "department": data.department or "",
        "list_url": data.list_url,
        "extraction_mode": data.extraction_mode,
        "css_selectors": data.css_selectors,
        "affiliation": data.affiliation,
    })
    crawler.api_key = llm_config.api_key
    crawler.base_url = llm_config.base_url
    crawler.model = llm_config.model
    crawler.llm_provider = llm_config.provider

    try:
        results = await asyncio.to_thread(
            crawler.crawl_all,
            delay=0,
        )
        # Cache the full results so formal crawl can reuse them
        cache_key = _compute_crawl_cache_key(
            current_user.id, data.list_url, data.extraction_mode,
            data.css_selectors, data.affiliation,
        )
        _test_crawl_cache[cache_key] = {
            "results": results,
            "timestamp": time.time(),
        }
        return CrawlerTestResponse(
            success=True,
            sample_results=results[:5],
            total_found=len(results),
            cache_key=cache_key,
        )
    except Exception as e:
        return CrawlerTestResponse(
            success=False,
            sample_results=[],
            total_found=0,
            error_message=str(e),
        )


@router.post("/crawl-configured", response_model=TaskStartResponse)
def crawl_with_config(
    data: CrawlerConfiguredCrawlRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a crawl using a saved crawler configuration.

    If config_id is negative, falls back to built-in crawlers.
    """
    config = (
        session.query(UniversityCrawlerConfig)
        .filter(
            UniversityCrawlerConfig.id == data.config_id,
            UniversityCrawlerConfig.user_id == current_user.id,
        )
        .first()
    )

    if not config:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.CRAWLER_CONFIG_NOT_FOUND, "爬虫配置不存在")

    cleanup_old_tasks()
    task = create_task(
        task_type="generic-university-crawl",
        task_name=f"爬取 {config.name}",
        user_id=current_user.id,
        total=0,
    )
    enqueue_task(
        "generic-university-crawl", task.task_id,
        config_id=config.id, cache_key=data.cache_key,
    )

    return TaskStartResponse(task_id=task.task_id, message=f"已启动爬取任务：{config.name}")


@router.get("/{professor_id}", response_model=ProfessorResponse)
def get_professor(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get a specific professor.

    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Professor details.
    """
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )

    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    return professor


@router.put("/{professor_id}", response_model=ProfessorResponse)
def update_professor(
    professor_id: int,
    data: ProfessorUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update a professor.

    Args:
        professor_id: Professor ID.
        data: Update data.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Updated professor.
    """
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )

    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    # Update fields
    if data.name is not None:
        professor.name = data.name
    if data.name_locales is not None:
        professor.name_locales = data.name_locales
    invalidate_embedding = False
    if data.affiliation is not None:
        professor.affiliation = data.affiliation
        invalidate_embedding = True
    if data.email is not None:
        professor.email = data.email
    if data.homepage is not None:
        professor.homepage = data.homepage
    if data.research_interests is not None:
        professor.research_interests = data.research_interests
        invalidate_embedding = True
    if data.paper_summaries is not None:
        professor.paper_summaries = data.paper_summaries
        invalidate_embedding = True
    if data.manual_notes is not None:
        professor.manual_notes = data.manual_notes
    if invalidate_embedding:
        professor.embedding = None

    session.flush()
    session.refresh(professor)

    return professor


def _apply_manual_patch(professor: Professor, patch: ProfessorUpdate) -> None:
    invalidate_embedding = False
    if patch.name is not None:
        professor.name = patch.name
    if patch.name_locales is not None:
        professor.name_locales = patch.name_locales
    if patch.affiliation is not None:
        professor.affiliation = patch.affiliation
        invalidate_embedding = True
    if patch.email is not None:
        professor.email = patch.email
    if patch.homepage is not None:
        professor.homepage = patch.homepage
    if patch.research_interests is not None:
        professor.research_interests = patch.research_interests
        invalidate_embedding = True
    if patch.manual_notes is not None:
        professor.manual_notes = patch.manual_notes
    if invalidate_embedding:
        professor.embedding = None


def _build_source_suggestions(source_inputs: List[SourceInput], summarizer: PaperSummarizer, language: str = "en") -> dict:
    publications = []
    paper_summaries = []
    for source in source_inputs:
        if source.source_type == "arxiv" and source.title:
            publications.append(
                {
                    "title": source.title,
                    "year": None,
                    "citations": None,
                    "authors": None,
                }
            )
        summary = build_paper_summary_from_source(
            {
                "id": source.id,
                "source_type": source.source_type,
                "title": source.title,
                "original_name": source.original_name,
                "canonical_id": source.canonical_id,
                "abstract": source.abstract,
                "extracted_markdown": source.extracted_markdown,
                "extracted_text": source.extracted_text,
            },
            summarizer=summarizer,
            language=language,
        )
        if summary:
            paper_summaries.append(summary)

    return {
        "publications": publications,
        "manual_notes_append": None,
        "paper_summaries": paper_summaries,
    }


@router.post("/{professor_id}/edit-preview", response_model=ProfessorEditPreviewResponse)
def preview_professor_edits(
    professor_id: int,
    data: ProfessorEditPreviewRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Preview professor updates from manual patch + source inputs."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    sources: List[SourceInput] = []
    summarizer = _get_paper_summarizer(session, current_user.id)
    if data.source_input_ids:
        sources = (
            session.query(SourceInput)
            .filter(
                SourceInput.id.in_(data.source_input_ids),
                SourceInput.user_id == current_user.id,
            )
            .all()
        )
        if len(sources) != len(set(data.source_input_ids)):
            raise_api_error(400, ErrorCode.INVALID_SOURCE_INPUT_IDS, "存在无效的来源输入 ID")

    manual_preview = {
        "name": professor.name,
        "name_locales": professor.name_locales or {},
        "affiliation": professor.affiliation,
        "email": professor.email,
        "homepage": professor.homepage,
        "research_interests": professor.research_interests or [],
        "paper_summaries": professor.paper_summaries or [],
        "manual_notes": professor.manual_notes,
    }
    if data.manual_patch is not None:
        if data.manual_patch.name is not None:
            manual_preview["name"] = data.manual_patch.name
        if data.manual_patch.name_locales is not None:
            manual_preview["name_locales"] = data.manual_patch.name_locales
        if data.manual_patch.affiliation is not None:
            manual_preview["affiliation"] = data.manual_patch.affiliation
        if data.manual_patch.email is not None:
            manual_preview["email"] = data.manual_patch.email
        if data.manual_patch.homepage is not None:
            manual_preview["homepage"] = data.manual_patch.homepage
        if data.manual_patch.research_interests is not None:
            manual_preview["research_interests"] = data.manual_patch.research_interests
        if data.manual_patch.paper_summaries is not None:
            manual_preview["paper_summaries"] = data.manual_patch.paper_summaries
        if data.manual_patch.manual_notes is not None:
            manual_preview["manual_notes"] = data.manual_patch.manual_notes

    suggestions = _build_source_suggestions(sources, summarizer=summarizer, language="en")
    return ProfessorEditPreviewResponse(
        manual_patch_applied=manual_preview,
        source_suggestions=suggestions,
    )


@router.post("/{professor_id}/apply-edits", response_model=ProfessorResponse)
def apply_professor_edits(
    professor_id: int,
    data: ProfessorEditApplyRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Apply professor updates from manual patch + source inputs."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    if data.manual_patch is not None:
        _apply_manual_patch(professor, data.manual_patch)

    summarizer = _get_paper_summarizer(session, current_user.id)
    if data.source_input_ids:
        sources = (
            session.query(SourceInput)
            .filter(
                SourceInput.id.in_(data.source_input_ids),
                SourceInput.user_id == current_user.id,
            )
            .all()
        )
        if len(sources) != len(set(data.source_input_ids)):
            raise_api_error(400, ErrorCode.INVALID_SOURCE_INPUT_IDS, "存在无效的来源输入 ID")

        suggestions = _build_source_suggestions(sources, summarizer=summarizer, language="en")
        if suggestions["publications"]:
            existing_titles = {p.get("title") for p in (professor.publications or [])}
            merged = list(professor.publications or [])
            for pub in suggestions["publications"]:
                if pub.get("title") not in existing_titles:
                    merged.append(pub)
            professor.publications = merged
            flag_modified(professor, "publications")

        if suggestions["paper_summaries"]:
            existing = list(professor.paper_summaries or [])
            existing_source_ids = {item.get("source_input_id") for item in existing}
            for summary in suggestions["paper_summaries"]:
                if summary.get("source_input_id") not in existing_source_ids:
                    existing.append(summary)
            professor.paper_summaries = existing
            flag_modified(professor, "paper_summaries")

        for source in sources:
            source.professor_id = professor.id

        # Professor text features changed; force recompute embedding in next match run.
        professor.embedding = None

    session.flush()
    session.refresh(professor)
    return professor


@router.post("/{professor_id}/summarize-sources", response_model=TaskStartResponse)
def summarize_professor_sources(
    professor_id: int,
    data: ProfessorSourceSummaryRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start background paper summarization for selected source inputs."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")
    if not data.source_input_ids:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.SOURCE_INPUT_REQUIRED, "请先选择来源输入")

    sources = (
        session.query(SourceInput)
        .filter(SourceInput.id.in_(data.source_input_ids), SourceInput.user_id == current_user.id)
        .all()
    )
    if len(sources) != len(set(data.source_input_ids)):
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.INVALID_SOURCE_INPUT_IDS, "存在无效的来源输入 ID")

    summarized_source_ids = {
        item.get("source_input_id")
        for item in (professor.paper_summaries or [])
        if isinstance(item, dict) and item.get("source_input_id") is not None
    }
    pending_source_ids = [
        source_id for source_id in data.source_input_ids if source_id not in summarized_source_ids
    ]
    if not pending_source_ids:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.SOURCES_ALREADY_SUMMARIZED, "当前来源均已总结，无需重复处理")

    cleanup_old_tasks()
    task = create_task(
        task_type="paper-summary",
        task_name=f"论文总结 · {professor.name}",
        user_id=current_user.id,
        total=len(pending_source_ids),
    )
    enqueue_task(
        "paper-summary", task.task_id, professor_id=professor_id, source_input_ids=pending_source_ids,
    )
    return TaskStartResponse(task_id=task.task_id, message="论文总结任务已启动")


@router.post("/{professor_id}/generate-profile", response_model=TaskStartResponse)
def generate_professor_profile(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a background task to generate a research profile for one professor.

    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for SSE progress tracking.
    """
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    cleanup_old_tasks()
    task = create_task(
        task_type="professor-profile",
        task_name=f"生成教授科研画像 · {professor.name}",
        user_id=current_user.id,
        total=3,
    )
    enqueue_task(
        "professor-profile", task.task_id, professor_id=professor_id,
    )
    return TaskStartResponse(task_id=task.task_id, message="教授科研画像生成任务已启动")


@router.post("/{professor_id}/crawl-homepage", response_model=TaskStartResponse)
def crawl_professor_homepage(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a background task to crawl the professor's homepage and merge fields."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    if not (professor.homepage or "").strip():
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.HOMEPAGE_URL_REQUIRED, "请先填写个人主页 URL")

    cleanup_old_tasks()
    task = create_task(
        task_type="professor-homepage-crawl",
        task_name=f"爬取个人主页 · {professor.name}",
        user_id=current_user.id,
        total=1,
    )
    enqueue_task(
        "professor-homepage-crawl",
        task.task_id,
        professor_id=professor_id,
    )
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动个人主页爬取：{professor.name}",
        total=1,
    )


@router.post("/{professor_id}/fill-publications", response_model=TaskStartResponse)
def fill_publications(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a background task to fetch full publication details from Google Scholar.

    Iterates over publications that have an ``author_pub_id`` but no abstract
    yet, opening each citation detail page to extract abstracts, external links,
    journal info, and more.

    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for SSE progress tracking.
    """
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    publications = professor.publications or []
    to_fill = [
        p for p in publications
        if p.get("author_pub_id") and not p.get("abstract")
    ]
    if not to_fill:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.NO_PAPERS_TO_FETCH, "没有需要获取详情的论文")

    cleanup_old_tasks()
    task = create_task(
        task_type="fill-publications",
        task_name=f"获取论文详情 · {professor.name}",
        user_id=current_user.id,
        total=len(to_fill),
    )
    enqueue_task(
        "fill-publications", task.task_id, professor_id=professor_id,
    )
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动论文详情获取任务，共 {len(to_fill)} 篇",
        total=len(to_fill),
    )


@router.post("/batch-generate-profiles", response_model=TaskStartResponse)
def batch_generate_professor_profiles(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a background task to generate research profiles for multiple professors.

    Args:
        data: List of professor IDs.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for SSE progress tracking.
    """
    if not data.ids:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PROFESSORS_REQUIRED, "请选择至少一位教授")

    professors = (
        session.query(Professor)
        .filter(Professor.id.in_(data.ids), Professor.user_id == current_user.id)
        .all()
    )
    if len(professors) != len(data.ids):
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.INVALID_PROFESSOR_IDS, "存在无效的教授 ID")

    cleanup_old_tasks()
    task = create_task(
        task_type="batch-professor-profiles",
        task_name=f"批量生成教授科研画像 · {len(data.ids)} 位",
        user_id=current_user.id,
        total=len(data.ids),
    )
    enqueue_task(
        "batch-professor-profiles", task.task_id, professor_ids=list(data.ids),
    )
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动 {len(data.ids)} 位教授科研画像生成任务",
    )


@router.post("/batch-refresh", response_model=TaskStartResponse)
def batch_refresh_professors(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a background task to refresh multiple professors from Google Scholar.

    Args:
        data: List of professor IDs.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for SSE progress tracking.
    """
    if not data.ids:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.PROFESSORS_REQUIRED, "请选择至少一位教授")

    professors = (
        session.query(Professor)
        .filter(Professor.id.in_(data.ids), Professor.user_id == current_user.id)
        .all()
    )
    if len(professors) != len(data.ids):
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.INVALID_PROFESSOR_IDS, "存在无效的教授 ID")

    cleanup_old_tasks()
    task = create_task(
        task_type="batch-refresh",
        task_name=f"批量更新教授 · {len(data.ids)} 位",
        user_id=current_user.id,
        total=len(data.ids),
    )
    enqueue_task(
        "batch-refresh", task.task_id, professor_ids=list(data.ids),
    )
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动批量更新任务，共 {len(data.ids)} 位教授",
    )


def _get_paper_summarizer(session: Session, user_id: int) -> PaperSummarizer:
    """Build summarizer from user LLM settings."""
    from ...llm.config import llm_provider_for_user_settings

    user_settings = (
        session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    )
    return PaperSummarizer(provider=llm_provider_for_user_settings(user_settings))


@router.delete("/{professor_id}", response_model=MessageResponse)
def delete_professor(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Delete a professor.

    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Success message.
    """
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )

    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    session.delete(professor)

    return MessageResponse(message="教授已删除")


@router.post("/{professor_id}/refresh", response_model=ProfessorResponse)
async def refresh_professor(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Refresh professor data from Google Scholar.

    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Updated professor with fresh data.
    """
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )

    if not professor:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    if not professor.google_scholar_id:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.SCHOLAR_ID_MISSING, "该教授没有关联的 Google Scholar ID")

    crawler = ScholarCrawler()

    try:
        author_data = await asyncio.to_thread(crawler.get_author, professor.google_scholar_id)
    except Exception as e:
        raise_api_error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.CRAWL_FAILED, f"爬取失败: {str(e)}")

    if not author_data:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.SCHOLAR_NOT_FOUND, "未找到该学者信息")

    from ...utils.name_locales import apply_scholar_name_update
    from ...utils.profile_merge import apply_external_affiliation

    # Update professor data
    apply_scholar_name_update(professor, author_data.get("name"))
    apply_external_affiliation(professor, author_data.get("affiliation"))
    professor.email = author_data.get("email") or professor.email
    professor.homepage = author_data.get("homepage") or professor.homepage
    professor.research_interests = author_data.get("interests", [])
    professor.publications = merge_publications(
        professor.publications,
        author_data.get("publications", []),
        "scholar",
    )
    professor.paper_summaries = keep_non_scholar_paper_summaries(professor.paper_summaries or [])
    professor.h_index = author_data.get("h_index")
    professor.total_citations = author_data.get("citations")
    professor.embedding = None

    session.flush()
    session.refresh(professor)

    settings_row = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )
    flags = flags_from_user_settings_row(settings_row)
    enrich_planned = planned_enrichment_step_count_for_professor(professor, flags)

    extra: dict = {}
    if enrich_planned > 0:
        enrich_task = create_task(
            "professor-enrichment",
            "教授信息增强",
            current_user.id,
            total=enrich_planned,
        )
        enqueue_task("professor-enrichment", enrich_task.task_id, professor_id=professor.id)
        extra["enrichment_task_id"] = enrich_task.task_id
        extra["enrichment_task_total"] = enrich_planned

    base = ProfessorResponse.model_validate(professor)
    return base.model_copy(update=extra)


@router.post("/batch-delete", response_model=MessageResponse)
def batch_delete_professors(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Batch delete professors.

    Args:
        data: List of professor IDs to delete.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Success message with count.
    """
    deleted_count = (
        session.query(Professor)
        .filter(Professor.id.in_(data.ids), Professor.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    return MessageResponse(message=f"已删除 {deleted_count} 位教授")


@router.post("/{professor_id}/set-scholar", response_model=TaskStartResponse)
def set_scholar_id_manually(
    professor_id: int,
    body: ProfessorScholarAdd,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Manually set a Scholar ID for a professor (by URL or ID).

    Triggers a full Scholar crawl + enrichment.
    """
    professor = (
        session.query(Professor)
        .filter(
            Professor.id == professor_id,
            Professor.user_id == current_user.id,
        )
        .first()
    )
    if not professor:
        raise_api_error(404, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    try:
        scholar_id = extract_scholar_id_from_url(body.url)
    except ValueError:
        raise_api_error(400, ErrorCode.SCHOLAR_ID_EXTRACT_FAILED, "无法从 URL 中提取 Scholar ID")

    professor.google_scholar_id = scholar_id
    professor.google_scholar_url = body.url
    professor.enrichment_status = "user_confirmed"
    professor.scholar_candidates = None

    task = create_task(
        "single-crawl",
        f"爬取教授 Scholar 主页: {professor.name}",
        current_user.id,
        total=1,
    )
    enqueue_task(
        "single-crawl",
        task.task_id,
        scholar_url=body.url,
    )

    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已设置 Scholar ID，正在爬取 {professor.name} 的完整信息...",
        total=1,
    )


@router.post("/{professor_id}/match-dblp", response_model=TaskStartResponse)
def match_professor_dblp_route(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Search DBLP for one professor and link when confident."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(404, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")
    if professor.dblp_pid:
        raise_api_error(400, ErrorCode.DBLP_ALREADY_LINKED, "该教授已关联 DBLP")

    universities = (
        session.query(University).filter(University.user_id == current_user.id).all()
    )
    university_variants, department_affiliation = resolve_scholar_match_params(
        professor, universities
    )
    if not university_variants and not department_affiliation:
        raise_api_error(400, ErrorCode.UNIVERSITY_AFFILIATION_REQUIRED, "请填写教授单位，或在设置中配置大学名称变体")

    professor.dblp_enrichment_status = "pending"
    professor.dblp_candidates = None

    task = create_task(
        "batch-dblp-match",
        f"DBLP 匹配: {professor.name}",
        current_user.id,
        total=1,
    )
    enqueue_task(
        "batch-dblp-match",
        task.task_id,
        professor_ids=[professor.id],
        university_variants=university_variants,
        department_affiliation=department_affiliation,
    )
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已开始为 {professor.name} 搜索 DBLP",
        total=1,
    )


@router.post("/{professor_id}/match-external", response_model=TaskStartResponse)
def match_professor_external(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start DBLP matching for one professor (Scholar must be linked manually)."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(404, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    if professor.dblp_pid:
        raise_api_error(400, ErrorCode.DBLP_ALREADY_LINKED, "该教授已关联 DBLP")

    universities = (
        session.query(University).filter(University.user_id == current_user.id).all()
    )
    university_variants, department_affiliation = resolve_scholar_match_params(
        professor, universities
    )
    if not university_variants and not department_affiliation:
        raise_api_error(400, ErrorCode.UNIVERSITY_AFFILIATION_REQUIRED, "请填写教授单位，或在设置中配置大学名称变体")

    professor.dblp_enrichment_status = "pending"
    professor.dblp_candidates = None
    dblp_task = create_task(
        "batch-dblp-match",
        f"DBLP 匹配: {professor.name}",
        current_user.id,
        total=1,
    )
    enqueue_task(
        "batch-dblp-match",
        dblp_task.task_id,
        professor_ids=[professor.id],
        university_variants=university_variants,
        department_affiliation=department_affiliation,
    )

    return TaskStartResponse(
        task_id=dblp_task.task_id,
        message=f"已开始为 {professor.name} 搜索 DBLP",
        total=1,
    )


@router.post("/{professor_id}/refresh-dblp", response_model=ProfessorResponse)
async def refresh_professor_dblp(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Refresh DBLP publications only (does not touch Scholar metrics)."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(404, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")
    if not professor.dblp_pid:
        raise_api_error(400, ErrorCode.DBLP_PID_MISSING, "该教授没有关联的 DBLP pid")

    client = DblpClient()
    try:
        author_data = await asyncio.to_thread(client.get_author, professor.dblp_pid)
    except Exception as e:
        raise_api_error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.DBLP_REFRESH_FAILED, f"DBLP 刷新失败: {str(e)}")
    if not author_data:
        raise_api_error(404, ErrorCode.DBLP_SCHOLAR_NOT_FOUND, "未找到 DBLP 学者信息")

    from ...utils.profile_merge import apply_external_affiliation

    apply_external_affiliation(professor, author_data.get("affiliation"))
    professor.publications = merge_publications(
        professor.publications,
        author_data.get("publications", []),
        "dblp",
    )
    professor.paper_summaries = keep_paper_summaries_excluding(
        professor.paper_summaries or [], {"dblp_pub"}
    )
    professor.dblp_url = author_data.get("dblp_url") or professor.dblp_url
    professor.embedding = None
    session.flush()
    session.refresh(professor)

    settings_row = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )
    flags = flags_from_user_settings_row(settings_row)
    enrich_planned = planned_enrichment_step_count_for_professor(professor, flags)
    extra: dict = {}
    if enrich_planned > 0:
        enrich_task = create_task(
            "professor-enrichment",
            "教授信息增强",
            current_user.id,
            total=enrich_planned,
        )
        enqueue_task("professor-enrichment", enrich_task.task_id, professor_id=professor.id)
        extra["enrichment_task_id"] = enrich_task.task_id
        extra["enrichment_task_total"] = enrich_planned

    base = ProfessorResponse.model_validate(professor)
    return base.model_copy(update=extra)


@router.post("/batch-refresh-dblp", response_model=TaskStartResponse)
def batch_refresh_dblp(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Batch refresh professors from DBLP."""
    if not data.ids:
        raise_api_error(400, ErrorCode.PROFESSORS_REQUIRED, "请选择至少一位教授")
    professors = (
        session.query(Professor)
        .filter(Professor.id.in_(data.ids), Professor.user_id == current_user.id)
        .all()
    )
    if len(professors) != len(data.ids):
        raise_api_error(400, ErrorCode.INVALID_PROFESSOR_IDS, "存在无效的教授 ID")

    cleanup_old_tasks()
    task = create_task(
        task_type="batch-refresh-dblp",
        task_name=f"批量更新 DBLP · {len(data.ids)} 位",
        user_id=current_user.id,
        total=len(data.ids),
    )
    enqueue_task("batch-refresh-dblp", task.task_id, professor_ids=list(data.ids))
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动 DBLP 批量更新，共 {len(data.ids)} 位教授",
    )


@router.post("/batch-refresh-external", response_model=TaskStartResponse)
def batch_refresh_external(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Batch refresh Scholar + DBLP sources for selected professors."""
    if not data.ids:
        raise_api_error(400, ErrorCode.PROFESSORS_REQUIRED, "请选择至少一位教授")
    professors = (
        session.query(Professor)
        .filter(Professor.id.in_(data.ids), Professor.user_id == current_user.id)
        .all()
    )
    if len(professors) != len(data.ids):
        raise_api_error(400, ErrorCode.INVALID_PROFESSOR_IDS, "存在无效的教授 ID")

    cleanup_old_tasks()
    task = create_task(
        task_type="batch-refresh-external",
        task_name=f"批量更新外部档案 · {len(data.ids)} 位",
        user_id=current_user.id,
        total=len(data.ids),
    )
    enqueue_task("batch-refresh-external", task.task_id, professor_ids=list(data.ids))
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已启动外部档案批量更新，共 {len(data.ids)} 位教授",
    )


@router.post("/confirm-dblp", response_model=TaskStartResponse)
def confirm_dblp_candidate(
    body: DblpCandidateConfirm,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Confirm DBLP candidate and crawl full profile."""
    professor = (
        session.query(Professor)
        .filter(
            Professor.id == body.professor_id,
            Professor.user_id == current_user.id,
        )
        .first()
    )
    if not professor:
        raise_api_error(404, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")

    professor.dblp_pid = body.dblp_pid
    professor.dblp_url = dblp_profile_url(body.dblp_pid)
    professor.dblp_enrichment_status = "user_confirmed"
    for cand in professor.dblp_candidates or []:
        if cand.get("pid") == body.dblp_pid and cand.get("name"):
            from ...utils.name_locales import apply_dblp_name_update

            apply_dblp_name_update(professor, cand["name"])
            break
    professor.dblp_candidates = None

    task = create_task(
        "single-dblp-crawl",
        f"爬取 DBLP: {professor.name}",
        current_user.id,
        total=1,
    )
    enqueue_task("single-dblp-crawl", task.task_id, professor.dblp_url)

    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已确认 DBLP 关联，正在爬取 {professor.name} 的论文列表...",
        total=1,
    )


@router.post("/{professor_id}/set-dblp", response_model=TaskStartResponse)
def set_dblp_manually(
    professor_id: int,
    body: ProfessorDblpAdd,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Manually set DBLP profile URL and crawl."""
    professor = (
        session.query(Professor)
        .filter(Professor.id == professor_id, Professor.user_id == current_user.id)
        .first()
    )
    if not professor:
        raise_api_error(404, ErrorCode.PROFESSOR_NOT_FOUND, "教授不存在")
    try:
        pid = extract_dblp_pid_from_url(body.url)
    except ValueError:
        raise_api_error(400, ErrorCode.DBLP_PID_EXTRACT_FAILED, "无法从 URL 中提取 DBLP pid")

    professor.dblp_pid = pid
    professor.dblp_url = dblp_profile_url(pid)
    professor.dblp_enrichment_status = "user_confirmed"
    professor.dblp_candidates = None

    task = create_task(
        "single-dblp-crawl",
        f"爬取 DBLP: {professor.name}",
        current_user.id,
        total=1,
    )
    enqueue_task("single-dblp-crawl", task.task_id, body.url)
    return TaskStartResponse(
        task_id=task.task_id,
        message=f"已设置 DBLP，正在爬取 {professor.name} 的论文列表...",
        total=1,
    )
