"""Profile management API routes."""

import asyncio
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session, sessionmaker

from ...models.schema import User, UserProfile
from ..deps import get_db_session, get_current_user
from ..schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    TaskStartResponse,
    BatchDeleteRequest,
    MessageResponse,
)
from ..task_manager import cleanup_old_tasks, create_task, execute_profile_parse

router = APIRouter(prefix="/profiles", tags=["简历管理"])


@router.get("", response_model=List[ProfileResponse])
def list_profiles(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List all profiles for current user.

    Args:
        current_user: Authenticated user.
        session: Database session.

    Returns:
        List of user's profiles.
    """
    profiles = (
        session.query(UserProfile)
        .filter(UserProfile.user_id == current_user.id)
        .order_by(UserProfile.updated_at.desc())
        .all()
    )
    return profiles


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Create a new profile manually.

    Args:
        data: Profile data.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Created profile.
    """
    # Deactivate other profiles
    session.query(UserProfile).filter(
        UserProfile.user_id == current_user.id,
        UserProfile.is_active == True,
    ).update({"is_active": False})

    # Create new profile
    profile = UserProfile(
        user_id=current_user.id,
        title=data.title,
        name=data.name,
        education=[e.model_dump() for e in data.education],
        research_experience=[r.model_dump() for r in data.research_experience],
        projects=[p.model_dump() for p in data.projects],
        skills=data.skills,
        raw_content=data.raw_content,
        source_format=data.source_format,
        is_active=True,
    )
    session.add(profile)
    session.flush()
    session.refresh(profile)

    return profile


@router.post("/upload", response_model=TaskStartResponse)
async def upload_profile(
    file: UploadFile = File(...),
    title: str = Form(...),
    use_llm: bool = Form(True),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Upload a resume file and start a background parse/save task.

    Args:
        file: Resume file (markdown or latex).
        title: Profile title.
        use_llm: Whether to use LLM for parsing.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for progress tracking via SSE.
    """
    # Validate file extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()

    if ext not in [".md", ".markdown", ".tex", ".latex"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 .md/.markdown/.tex/.latex 格式的文件",
        )

    # Read file content
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件编码错误，请使用 UTF-8 编码",
        )

    if not text_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件内容为空",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="profile-parse",
        task_name=f"解析简历 · {title}",
        user_id=current_user.id,
        total=1,
    )
    task_session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=session.get_bind(),
    )
    asyncio.create_task(
        execute_profile_parse(
            task,
            title=title,
            text_content=text_content,
            extension=ext,
            use_llm=use_llm,
            session_factory=task_session_factory,
        )
    )

    return TaskStartResponse(
        task_id=task.task_id,
        message="已启动简历解析任务，完成后会自动保存到列表",
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get a specific profile.

    Args:
        profile_id: Profile ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Profile details.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )

    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update a profile.

    Args:
        profile_id: Profile ID.
        data: Update data.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Updated profile.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )

    # Update fields
    if data.title is not None:
        profile.title = data.title
    if data.name is not None:
        profile.name = data.name
    if data.education is not None:
        profile.education = [e.model_dump() for e in data.education]
    if data.research_experience is not None:
        profile.research_experience = [r.model_dump() for r in data.research_experience]
    if data.projects is not None:
        profile.projects = [p.model_dump() for p in data.projects]
    if data.skills is not None:
        profile.skills = data.skills

    session.flush()
    session.refresh(profile)

    return profile


@router.delete("/{profile_id}", response_model=MessageResponse)
def delete_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Delete a profile.

    Args:
        profile_id: Profile ID.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Success message.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )

    session.delete(profile)

    return MessageResponse(message="简历已删除")


@router.post("/{profile_id}/activate", response_model=ProfileResponse)
def activate_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Activate a profile (deactivate others).

    Args:
        profile_id: Profile ID to activate.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Activated profile.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="简历不存在",
        )

    # Deactivate all profiles
    session.query(UserProfile).filter(
        UserProfile.user_id == current_user.id,
    ).update({"is_active": False})

    # Activate selected profile
    profile.is_active = True
    session.flush()
    session.refresh(profile)

    return profile


@router.post("/batch-delete", response_model=MessageResponse)
def batch_delete_profiles(
    data: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Batch delete profiles.

    Args:
        data: List of profile IDs to delete.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Success message with count.
    """
    deleted_count = (
        session.query(UserProfile)
        .filter(UserProfile.id.in_(data.ids), UserProfile.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    return MessageResponse(message=f"已删除 {deleted_count} 份简历")
