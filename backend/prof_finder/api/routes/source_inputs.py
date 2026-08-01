"""Source input API routes (ArXiv)."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...models.schema import SourceInput, User
from ..deps import get_current_user, get_db_session
from ..errors import ErrorCode, raise_api_error
from ..schemas import (
    MessageResponse,
    PaginatedResponse,
    SourceInputArxivCreate,
    SourceInputResponse,
)
from ..source_input_service import fetch_arxiv_metadata, normalize_arxiv_id

router = APIRouter(prefix="/source-inputs", tags=["来源输入"])


@router.get("", response_model=PaginatedResponse)
def list_source_inputs(
    professor_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List source inputs, optionally filtered by professor_id."""
    query = session.query(SourceInput).filter(SourceInput.user_id == current_user.id)
    if professor_id is not None:
        query = query.filter(SourceInput.professor_id == professor_id)
    total = query.count()
    results = (
        query.order_by(SourceInput.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1
    items = [SourceInputResponse.model_validate(r) for r in results]
    return PaginatedResponse(
        items=[item.model_dump() for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/arxiv", response_model=SourceInputResponse, status_code=status.HTTP_201_CREATED)
def create_arxiv_source_input(
    data: SourceInputArxivCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Create source input from ArXiv URL (metadata via official API)."""
    try:
        canonical_id = normalize_arxiv_id(data.url)
    except ValueError as exc:
        raise_api_error(400, ErrorCode.BAD_REQUEST, str(exc))

    try:
        metadata = fetch_arxiv_metadata(canonical_id)
    except Exception as exc:
        raise_api_error(400, ErrorCode.ARXIV_FETCH_FAILED, f"ArXiv 元数据获取失败: {exc}")

    source_input = SourceInput(
        user_id=current_user.id,
        source_type="arxiv",
        source_url=data.url,
        canonical_id=canonical_id,
        title=metadata.get("title"),
        abstract=metadata.get("abstract"),
        pdf_url=metadata.get("pdf_url"),
        status="succeeded",
        metadata_only=False,
        error_message=None,
    )
    session.add(source_input)
    session.flush()
    session.refresh(source_input)
    return source_input


@router.get("/{source_input_id}", response_model=SourceInputResponse)
def get_source_input(
    source_input_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get source input detail."""
    source_input = (
        session.query(SourceInput)
        .filter(SourceInput.id == source_input_id, SourceInput.user_id == current_user.id)
        .first()
    )
    if not source_input:
        raise_api_error(404, ErrorCode.SOURCE_INPUT_NOT_FOUND, "来源输入不存在")
    return source_input


@router.delete("/{source_input_id}", response_model=MessageResponse)
def delete_source_input(
    source_input_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Delete one source input."""
    source_input = (
        session.query(SourceInput)
        .filter(SourceInput.id == source_input_id, SourceInput.user_id == current_user.id)
        .first()
    )
    if not source_input:
        raise_api_error(404, ErrorCode.SOURCE_INPUT_NOT_FOUND, "来源输入不存在")

    session.delete(source_input)
    return MessageResponse(message="来源输入已删除")
