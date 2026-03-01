"""Professor management API routes."""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ...models.schema import User, Professor, SourceInput
from ...crawler.scholar import ScholarCrawler
from ...llm import PaperSummarizer
from ..deps import get_db_session, get_current_user
from ..schemas import (
    ProfessorCreate,
    ProfessorUpdate,
    ProfessorScholarAdd,
    ProfessorSearchRequest,
    ProfessorResponse,
    ProfessorListResponse,
    ScholarSearchResult,
    ProfessorEditPreviewRequest,
    ProfessorEditApplyRequest,
    ProfessorSourceSummaryRequest,
    ProfessorEditPreviewResponse,
    BatchDeleteRequest,
    MessageResponse,
    PaginatedResponse,
    TaskStartResponse,
    UniversityCrawlerInfo,
    UniversityCrawlRequest,
)
from ..task_manager import (
    create_task,
    cleanup_old_tasks,
    extract_scholar_id_from_url,
    execute_single_crawl,
    execute_university_crawl,
    execute_professor_source_summary,
)
from ..source_input_service import build_paper_summary_from_source

router = APIRouter(prefix="/professors", tags=["教授管理"])


def get_professor_list_response(professor: Professor) -> dict:
    """Convert Professor to list response format."""
    return {
        "id": professor.id,
        "name": professor.name,
        "affiliation": professor.affiliation,
        "research_interests": professor.research_interests or [],
        "h_index": professor.h_index,
        "publication_count": len(professor.publications or []),
        "created_at": professor.created_at,
    }


@router.get("", response_model=PaginatedResponse)
def list_professors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    affiliation: Optional[str] = None,
    interest: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List professors with pagination and filtering.
    
    Args:
        page: Page number (1-indexed).
        page_size: Items per page.
        affiliation: Filter by affiliation (partial match).
        interest: Filter by research interest (partial match).
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        Paginated list of professors.
    """
    query = session.query(Professor).filter(Professor.user_id == current_user.id)
    
    # Apply filters
    if affiliation:
        query = query.filter(Professor.affiliation.ilike(f"%{affiliation}%"))
    if interest:
        # SQLite JSON query - search in research_interests array
        query = query.filter(Professor.research_interests.cast(str).ilike(f"%{interest}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    professors = (
        query
        .order_by(Professor.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return PaginatedResponse(
        items=[get_professor_list_response(p) for p in professors],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


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
        affiliation=data.affiliation,
        email=data.email,
        homepage=data.homepage,
        research_interests=data.research_interests,
        manual_notes=data.manual_notes,
        publications=[],
        paper_summaries=data.paper_summaries or [],
    )
    session.add(professor)
    session.flush()
    session.refresh(professor)
    
    return professor


@router.post("/scholar", response_model=TaskStartResponse)
async def add_professor_by_scholar(
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="single-crawl",
        task_name="爬取教授",
        user_id=current_user.id,
        total=1,
    )
    asyncio.create_task(execute_single_crawl(task, data.url))

    return TaskStartResponse(task_id=task.task_id, message="爬取任务已启动")


@router.post("/search", response_model=List[ScholarSearchResult])
def search_scholar(
    data: ProfessorSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search Google Scholar for professors.
    
    Args:
        data: Search query and limit.
        current_user: Authenticated user.
        
    Returns:
        List of search results (not saved to database).
    """
    crawler = ScholarCrawler()
    
    try:
        results = crawler.search_author(data.query, limit=data.limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}",
        )
    
    return [
        ScholarSearchResult(
            name=r["name"],
            affiliation=r.get("affiliation"),
            scholar_id=r["scholar_id"],
            scholar_url=f"https://scholar.google.com/citations?user={r['scholar_id']}",
            interests=r.get("interests", []),
            citations=r.get("citedby"),
        )
        for r in results
    ]


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
async def crawl_university(
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持该院校: {data.university_id}",
        )

    crawler_cls = REGISTRY[data.university_id]
    display_name = crawler_cls.display_name

    cleanup_old_tasks()
    task = create_task(
        task_type="university-crawl",
        task_name=f"爬取 {display_name}",
        user_id=current_user.id,
        total=0,
    )
    asyncio.create_task(execute_university_crawl(task, data.university_id))

    return TaskStartResponse(task_id=task.task_id, message=f"已启动爬取任务：{display_name}")


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教授不存在",
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教授不存在",
        )
    
    # Update fields
    if data.name is not None:
        professor.name = data.name
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


def _build_source_suggestions(source_inputs: List[SourceInput], summarizer: PaperSummarizer) -> dict:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教授不存在")

    sources: List[SourceInput] = []
    summarizer = _get_paper_summarizer(current_user)
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
            raise HTTPException(status_code=400, detail="存在无效的来源输入 ID")

    manual_preview = {
        "name": professor.name,
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

    suggestions = _build_source_suggestions(sources, summarizer=summarizer)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教授不存在")

    if data.manual_patch is not None:
        _apply_manual_patch(professor, data.manual_patch)

    summarizer = _get_paper_summarizer(current_user)
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
            raise HTTPException(status_code=400, detail="存在无效的来源输入 ID")

        suggestions = _build_source_suggestions(sources, summarizer=summarizer)
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
async def summarize_professor_sources(
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="教授不存在")
    if not data.source_input_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先选择来源输入")

    sources = (
        session.query(SourceInput)
        .filter(SourceInput.id.in_(data.source_input_ids), SourceInput.user_id == current_user.id)
        .all()
    )
    if len(sources) != len(set(data.source_input_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="存在无效的来源输入 ID")

    summarized_source_ids = {
        item.get("source_input_id")
        for item in (professor.paper_summaries or [])
        if isinstance(item, dict) and item.get("source_input_id") is not None
    }
    pending_source_ids = [
        source_id for source_id in data.source_input_ids if source_id not in summarized_source_ids
    ]
    if not pending_source_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前来源均已总结，无需重复处理")

    cleanup_old_tasks()
    task = create_task(
        task_type="paper-summary",
        task_name=f"论文总结 · {professor.name}",
        user_id=current_user.id,
        total=len(pending_source_ids),
    )
    asyncio.create_task(
        execute_professor_source_summary(task, professor_id=professor_id, source_input_ids=pending_source_ids)
    )
    return TaskStartResponse(task_id=task.task_id, message="论文总结任务已启动")


def _get_paper_summarizer(current_user: User) -> PaperSummarizer:
    """Build summarizer from user settings if available."""
    user_settings = getattr(current_user, "settings", None)
    api_key = getattr(user_settings, "deepseek_api_key", None)
    base_url = getattr(user_settings, "deepseek_base_url", None)
    return PaperSummarizer(api_key=api_key, base_url=base_url)


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教授不存在",
        )
    
    session.delete(professor)
    
    return MessageResponse(message="教授已删除")


@router.post("/{professor_id}/refresh", response_model=ProfessorResponse)
def refresh_professor(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教授不存在",
        )
    
    if not professor.google_scholar_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该教授没有关联的 Google Scholar ID",
        )
    
    crawler = ScholarCrawler()
    
    try:
        author_data = crawler.get_author(professor.google_scholar_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"爬取失败: {str(e)}",
        )
    
    if not author_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该学者信息",
        )
    
    # Update professor data
    professor.name = author_data["name"]
    professor.affiliation = author_data.get("affiliation")
    professor.email = author_data.get("email") or professor.email
    professor.homepage = author_data.get("homepage") or professor.homepage
    professor.research_interests = author_data.get("interests", [])
    professor.publications = author_data.get("publications", [])
    professor.paper_summaries = []
    professor.h_index = author_data.get("h_index")
    professor.total_citations = author_data.get("citations")
    professor.embedding = None
    
    session.flush()
    session.refresh(professor)
    
    return professor


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
