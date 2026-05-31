"""Match API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...models.schema import User, UserProfile, Professor, MatchRecord
from ...matcher.keyword_matcher import KeywordMatcher
from ..deps import get_db_session, get_current_user
from ..schemas import (
    MatchResultResponse,
    MatchDetailResponse,
    PaginatedResponse,
    MessageResponse,
    TaskStartResponse,
)
from ..task_manager import create_task, cleanup_old_tasks, enqueue_task
from ...runtime import model_dir

router = APIRouter(prefix="/match", tags=["匹配"])

_MATCH_SORT_COLUMNS = {
    "score": MatchRecord.score,
    "professor_name": Professor.name,
    "professor_affiliation": Professor.affiliation,
}


@router.get("/model-status")
def get_model_status():
    """Check if the embedding model is available locally."""
    return {"ready": model_dir().exists()}


@router.post("/download-model", response_model=TaskStartResponse)
async def download_model(
    current_user: User = Depends(get_current_user),
):
    """Start a background task to download the embedding model from ModelScope."""
    if model_dir().exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模型已存在，无需重复下载",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="download-model",
        task_name="下载语义匹配模型",
        user_id=current_user.id,
        total=100,
    )
    enqueue_task("download-model", task.task_id)

    return TaskStartResponse(
        task_id=task.task_id,
        message="模型下载任务已启动",
    )


@router.post("/run", response_model=TaskStartResponse)
async def run_matching(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start an async task to run the matching algorithm.

    Validates prerequisites synchronously, then delegates execution to a
    background asyncio coroutine so the caller gets a task_id immediately.

    Args:
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for SSE progress tracking.
    """
    if not model_dir().exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MODEL_NOT_DOWNLOADED",
        )

    active_profile = (
        session.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id, UserProfile.is_active == True)
        .first()
    )
    if not active_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先激活一份画像",
        )

    professor_count = (
        session.query(Professor)
        .filter(Professor.user_id == current_user.id)
        .count()
    )
    if professor_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先添加教授",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="match",
        task_name="运行匹配算法",
        user_id=current_user.id,
        total=professor_count,
    )
    enqueue_task("match", task.task_id, active_profile.id)

    return TaskStartResponse(
        task_id=task.task_id,
        message=f"匹配任务已启动，共 {professor_count} 位教授",
    )


@router.get("/results", response_model=PaginatedResponse)
def get_match_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get match results for current active profile."""
    # Get active profile
    active_profile = (
        session.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id, UserProfile.is_active == True)
        .first()
    )

    if not active_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先激活一份画像",
        )

    # Build query
    query = (
        session.query(MatchRecord, Professor)
        .join(Professor, MatchRecord.professor_id == Professor.id)
        .filter(MatchRecord.user_profile_id == active_profile.id)
    )

    if min_score is not None:
        query = query.filter(MatchRecord.score >= min_score)
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
    order_col = _MATCH_SORT_COLUMNS.get(sort_by, MatchRecord.score)
    order_func = order_col.asc if sort_order == "asc" else order_col.desc

    # Apply pagination
    results = (
        query
        .order_by(order_func())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    items = [
        {
            "professor_id": professor.id,
            "professor_name": professor.name,
            "professor_affiliation": professor.affiliation,
            "score": match_record.score,
            "match_reasons": match_record.match_reasons or [],
            "letter_generated": match_record.letter_content is not None,
        }
        for match_record, professor in results
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/results/{professor_id}", response_model=MatchDetailResponse)
def get_match_detail(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get detailed match result for a specific professor.
    
    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        Detailed match result.
    """
    # Get active profile
    active_profile = (
        session.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id, UserProfile.is_active == True)
        .first()
    )
    
    if not active_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先激活一份画像",
        )
    
    # Get match record
    result = (
        session.query(MatchRecord, Professor)
        .join(Professor, MatchRecord.professor_id == Professor.id)
        .filter(
            MatchRecord.user_profile_id == active_profile.id,
            MatchRecord.professor_id == professor_id,
        )
        .first()
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到匹配记录，请先运行匹配",
        )
    
    match_record, professor = result
    
    return MatchDetailResponse(
        professor_id=professor.id,
        professor_name=professor.name,
        professor_affiliation=professor.affiliation,
        professor_interests=professor.research_interests or [],
        score=match_record.score,
        match_reasons=match_record.match_reasons or [],
        letter_content=match_record.letter_content,
        letter_generated_at=match_record.letter_generated_at,
    )
