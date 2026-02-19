"""Professor management API routes."""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...models.schema import User, Professor
from ...crawler.scholar import ScholarCrawler
from ..deps import get_db_session, get_current_user
from ..schemas import (
    ProfessorCreate,
    ProfessorUpdate,
    ProfessorScholarAdd,
    ProfessorSearchRequest,
    ProfessorResponse,
    ProfessorListResponse,
    ScholarSearchResult,
    BatchDeleteRequest,
    MessageResponse,
    PaginatedResponse,
    TaskStartResponse,
)
from ..task_manager import (
    create_task,
    cleanup_old_tasks,
    extract_scholar_id_from_url,
    execute_single_crawl,
)

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
        publications=[],
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
    if data.affiliation is not None:
        professor.affiliation = data.affiliation
    if data.email is not None:
        professor.email = data.email
    if data.homepage is not None:
        professor.homepage = data.homepage
    if data.research_interests is not None:
        professor.research_interests = data.research_interests
    
    session.flush()
    session.refresh(professor)
    
    return professor


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
    professor.h_index = author_data.get("h_index")
    professor.total_citations = author_data.get("citations")
    
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
