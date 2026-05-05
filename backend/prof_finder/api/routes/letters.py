"""Letter generation API routes."""

from datetime import datetime, timezone
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...models.schema import User, UserProfile, Professor, MatchRecord, UserSettings
from ...llm.letter_generator import LetterGenerator
from ...config import settings as app_settings
from ..deps import get_db_session, get_current_user
from ..schemas import (
    LetterUpdate,
    LetterResponse,
    MessageResponse,
    PaginatedResponse,
    TaskStartResponse,
)
from ..task_manager import create_task, cleanup_old_tasks, enqueue_task

router = APIRouter(prefix="/letters", tags=["邮件生成"])


def get_user_api_key(user: User, session: Session) -> str:
    """Get the DeepSeek API key for a user.
    
    Checks user settings first, then falls back to global settings.
    
    Args:
        user: User to get API key for.
        session: Database session.
        
    Returns:
        API key string.
        
    Raises:
        HTTPException: If no API key configured.
    """
    # Check user settings
    user_settings = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == user.id)
        .first()
    )
    
    if user_settings and user_settings.deepseek_api_key:
        return user_settings.deepseek_api_key
    
    # Fall back to global settings
    if app_settings.deepseek_api_key:
        return app_settings.deepseek_api_key
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="请先在设置中配置 DeepSeek API Key",
    )


@router.get("", response_model=PaginatedResponse)
def list_letters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List all letters for current active profile.
    
    Args:
        page: Page number.
        page_size: Items per page.
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        Paginated list of letters.
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
            detail="请先激活一份简历",
        )
    
    # Get match records with professors
    query = (
        session.query(MatchRecord, Professor)
        .join(Professor, MatchRecord.professor_id == Professor.id)
        .filter(MatchRecord.user_profile_id == active_profile.id)
        .order_by(MatchRecord.score.desc())
    )
    
    total = query.count()
    
    results = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    items = [
        {
            "professor_id": professor.id,
            "professor_name": professor.name,
            "content": match_record.letter_content,
            "generated_at": match_record.letter_generated_at,
            "is_generated": match_record.letter_content is not None,
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


@router.post("/generate/{professor_id}", response_model=TaskStartResponse)
async def generate_letter(
    professor_id: int,
    language: Literal["zh", "en"],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start an async task to generate a letter for one professor.

    Validates prerequisites synchronously, then delegates the LLM call to a
    background asyncio coroutine.

    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for SSE progress tracking.
    """
    api_key = get_user_api_key(current_user, session)

    active_profile = (
        session.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id, UserProfile.is_active == True)
        .first()
    )
    if not active_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先激活一份简历",
        )

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

    _, professor = result
    cleanup_old_tasks()
    task = create_task(
        task_type="single-letter",
        task_name=f"生成邮件 · {professor.name}",
        user_id=current_user.id,
        total=1,
    )
    enqueue_task(
        "single-letter", task.task_id, professor_id, active_profile.id, api_key, language,
    )

    return TaskStartResponse(task_id=task.task_id, message="邮件生成任务已启动")


@router.get("/{professor_id}", response_model=LetterResponse)
def get_letter(
    professor_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get a letter for a specific professor.
    
    Args:
        professor_id: Professor ID.
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        Letter content.
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
            detail="请先激活一份简历",
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
            detail="未找到匹配记录",
        )
    
    match_record, professor = result
    
    return LetterResponse(
        professor_id=professor.id,
        professor_name=professor.name,
        content=match_record.letter_content,
        generated_at=match_record.letter_generated_at,
        is_generated=match_record.letter_content is not None,
    )


@router.put("/{professor_id}", response_model=LetterResponse)
def update_letter(
    professor_id: int,
    data: LetterUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update a letter (user edits after generation).
    
    Args:
        professor_id: Professor ID.
        data: Updated letter content.
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        Updated letter.
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
            detail="请先激活一份简历",
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
            detail="未找到匹配记录",
        )
    
    match_record, professor = result
    
    # Update letter
    match_record.letter_content = data.content
    if not match_record.letter_generated_at:
        match_record.letter_generated_at = datetime.now(timezone.utc)
    
    session.flush()
    
    return LetterResponse(
        professor_id=professor.id,
        professor_name=professor.name,
        content=match_record.letter_content,
        generated_at=match_record.letter_generated_at,
        is_generated=True,
    )
