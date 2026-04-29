"""Match API routes."""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from ..task_manager import create_task, cleanup_old_tasks, execute_match

router = APIRouter(prefix="/match", tags=["匹配"])


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
    asyncio.create_task(execute_match(task, active_profile.id))

    return TaskStartResponse(
        task_id=task.task_id,
        message=f"匹配任务已启动，共 {professor_count} 位教授",
    )


@router.get("/results", response_model=PaginatedResponse)
def get_match_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get match results for current active profile.
    
    Args:
        page: Page number.
        page_size: Items per page.
        min_score: Minimum match score filter.
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        Paginated match results.
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
    
    # Build query
    query = (
        session.query(MatchRecord, Professor)
        .join(Professor, MatchRecord.professor_id == Professor.id)
        .filter(MatchRecord.user_profile_id == active_profile.id)
    )
    
    if min_score is not None:
        query = query.filter(MatchRecord.score >= min_score)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and sorting
    results = (
        query
        .order_by(MatchRecord.score.desc())
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
