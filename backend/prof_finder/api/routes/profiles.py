"""Profile management API routes."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from ...models.schema import User, UserProfile
from ..deps import get_db_session, get_current_user
from ..schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileChatRequest,
    ProfileChatResponse,
    ProfileChatRefineRequest,
    TaskStartResponse,
    BatchDeleteRequest,
    MessageResponse,
)
from ..task_manager import (
    MAX_PROFILE_MATERIAL_CHARS,
    cleanup_old_tasks,
    create_task,
    enqueue_task,
)
from ...llm.student_profile_generator import StudentProfileGenerator

router = APIRouter(prefix="/profiles", tags=["学生画像"])

SUPPORTED_PROFILE_MATERIAL_EXTENSIONS = {".md", ".markdown", ".txt", ".tex", ".latex"}


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
        name_locales=data.name_locales or {},
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
    file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File(default=[]),
    title: str = Form(...),
    use_llm: bool = Form(True),
    research_interests: str = Form(""),
    personal_statement: str = Form(""),
    research_plan: str = Form(""),
    notes: str = Form(""),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Upload profile materials and start a background generation/save task.

    Args:
        file: Legacy single resume/material file.
        files: Multiple profile material files.
        title: Profile title.
        use_llm: Whether to use LLM for legacy resume field extraction.
        research_interests: Directly entered research interests.
        personal_statement: Directly entered personal statement.
        research_plan: Directly entered research plan.
        notes: Directly entered free-form notes.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for progress tracking via SSE.
    """
    uploaded_files: List[UploadFile] = []
    if file and file.filename:
        uploaded_files.append(file)
    uploaded_files.extend(item for item in files if item.filename)

    manual_inputs = {
        "research_interests": research_interests.strip(),
        "personal_statement": personal_statement.strip(),
        "research_plan": research_plan.strip(),
        "notes": notes.strip(),
    }
    has_manual_input = any(manual_inputs.values())
    if not uploaded_files and not has_manual_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少上传一个材料文件或填写一项画像材料",
        )

    materials = []
    for upload in uploaded_files:
        filename = upload.filename or ""
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_PROFILE_MATERIAL_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仅支持 .md/.markdown/.txt/.tex/.latex 格式的文件",
            )

        content = await upload.read()
        try:
            text_content = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件编码错误，请使用 UTF-8 编码：{filename}",
            )

        if not text_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件内容为空：{filename}",
            )

        materials.append(
            {
                "source_type": "file",
                "filename": filename,
                "extension": ext,
                "content": text_content,
            }
        )

    total_chars = sum(len(item["content"]) for item in materials) + sum(
        len(value) for value in manual_inputs.values()
    )
    if total_chars > MAX_PROFILE_MATERIAL_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"画像材料过长，请控制在 {MAX_PROFILE_MATERIAL_CHARS} 字符以内",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="profile-generate",
        task_name=f"生成学生画像 · {title}",
        user_id=current_user.id,
        total=3,
    )
    enqueue_task(
        "profile-generate",
        task.task_id,
        title=title,
        materials=materials,
        manual_inputs=manual_inputs,
        use_llm=use_llm,
    )

    return TaskStartResponse(
        task_id=task.task_id,
        message="已启动学生画像生成任务，完成后会自动保存到列表",
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
            detail="画像不存在",
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
            detail="画像不存在",
        )

    # Update fields
    if data.title is not None:
        profile.title = data.title
    if data.name is not None:
        profile.name = data.name
    if data.name_locales is not None:
        profile.name_locales = data.name_locales
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
            detail="画像不存在",
        )

    session.delete(profile)

    return MessageResponse(message="画像已删除")


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
            detail="画像不存在",
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

    return MessageResponse(message=f"已删除 {deleted_count} 份画像")


@router.post("/{profile_id}/chat", response_model=ProfileChatResponse)
def profile_chat(
    profile_id: int,
    data: ProfileChatRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """AI interviewer chat: send a message and get the next AI question.

    Args:
        profile_id: Profile ID.
        data: User message + full chat history.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        AI interviewer reply.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="画像不存在",
        )

    generator = StudentProfileGenerator()
    if not generator.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="请先配置 DeepSeek API Key",
        )

    analysis = profile.profile_analysis or {}
    academic_profile = profile.academic_profile or ""

    try:
        reply = generator.interview(
            profile_analysis=analysis,
            academic_profile=academic_profile,
            history=data.history,
            message=data.message,
            locale=data.locale,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return ProfileChatResponse(reply=reply)


@router.post("/{profile_id}/chat/refine", response_model=TaskStartResponse)
async def profile_chat_refine(
    profile_id: int,
    data: ProfileChatRefineRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Start a background task to regenerate the profile from chat Q&A.

    Args:
        profile_id: Profile ID.
        data: Full chat history.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Task ID for progress tracking via SSE.
    """
    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == profile_id, UserProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="画像不存在",
        )

    generator = StudentProfileGenerator()
    if not generator.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="请先配置 DeepSeek API Key",
        )

    if not data.history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先与 AI 进行至少一轮对话",
        )

    cleanup_old_tasks()
    task = create_task(
        task_type="profile-refine",
        task_name=f"优化学生画像 · {profile.title}",
        user_id=current_user.id,
        total=4,
    )
    task.total = 4
    enqueue_task(
        "profile-refine",
        task.task_id,
        profile_id=profile_id,
        chat_history=data.history,
    )

    return TaskStartResponse(
        task_id=task.task_id,
        message="画像优化任务已启动，完成后自动更新",
    )
