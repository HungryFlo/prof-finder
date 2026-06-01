"""Source input API routes (PDF + ArXiv)."""

import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ...config import settings
from ...models.schema import SourceInput, User
from ..deps import get_current_user, get_db_session
from ..schemas import MessageResponse, PaginatedResponse, SourceInputArxivCreate, SourceInputResponse
from ..source_input_service import (
    download_to_temp_file,
    extract_markdown_from_pdf,
    fetch_arxiv_metadata,
    normalize_arxiv_id,
    safe_delete_file,
)

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


@router.post("/pdf", response_model=SourceInputResponse, status_code=status.HTTP_201_CREATED)
async def create_pdf_source_input(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Upload a PDF and extract markdown preview."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    raw_bytes = file.file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="PDF 文件为空")

    temp_path = None
    try:
        temp_dir = Path(settings.database_path).parent / "source_inputs_tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"user{current_user.id}_upload_{file.filename or 'source'}.pdf"
        temp_path.write_bytes(raw_bytes)
        markdown = await asyncio.to_thread(extract_markdown_from_pdf, temp_path)

        source_input = SourceInput(
            user_id=current_user.id,
            source_type="pdf",
            original_name=file.filename,
            status="succeeded",
            extracted_markdown=markdown,
        )
        session.add(source_input)
        session.flush()
        session.refresh(source_input)
        return source_input
    except HTTPException:
        raise
    except Exception as exc:
        source_input = SourceInput(
            user_id=current_user.id,
            source_type="pdf",
            original_name=file.filename,
            status="failed",
            error_message=f"PDF 解析失败: {exc}",
        )
        session.add(source_input)
        session.flush()
        session.refresh(source_input)
        return source_input
    finally:
        safe_delete_file(str(temp_path) if temp_path else None)


@router.post("/arxiv", response_model=SourceInputResponse, status_code=status.HTTP_201_CREATED)
async def create_arxiv_source_input(
    data: SourceInputArxivCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Create source input from ArXiv URL, with metadata-only fallback."""
    try:
        canonical_id = normalize_arxiv_id(data.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        metadata = await asyncio.to_thread(fetch_arxiv_metadata, canonical_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"ArXiv 元数据获取失败: {exc}")

    source_input = SourceInput(
        user_id=current_user.id,
        source_type="arxiv",
        source_url=data.url,
        canonical_id=canonical_id,
        title=metadata.get("title"),
        abstract=metadata.get("abstract"),
        pdf_url=metadata.get("pdf_url"),
        status="pending",
        metadata_only=False,
    )
    session.add(source_input)
    session.flush()

    try:
        if not source_input.pdf_url:
            raise ValueError("ArXiv 返回结果缺少 PDF 链接")

        def _download_and_parse():
            pdf = download_to_temp_file(source_input.pdf_url)
            try:
                md = extract_markdown_from_pdf(pdf)
                return pdf, md
            except Exception:
                safe_delete_file(str(pdf))
                raise

        temp_pdf, markdown = await asyncio.to_thread(_download_and_parse)
        source_input.downloaded_pdf_path = str(temp_pdf)
        source_input.extracted_markdown = markdown
        source_input.status = "succeeded"
        source_input.error_message = None
        source_input.metadata_only = False
    except Exception as exc:
        source_input.status = "failed"
        source_input.metadata_only = True
        source_input.error_message = f"PDF 下载或解析失败，可稍后重试: {exc}"
    finally:
        safe_delete_file(source_input.downloaded_pdf_path)
        source_input.downloaded_pdf_path = None

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
        raise HTTPException(status_code=404, detail="来源输入不存在")
    return source_input


@router.post("/{source_input_id}/retry-pdf-parse", response_model=SourceInputResponse)
async def retry_arxiv_pdf_parse(
    source_input_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Retry PDF parse for metadata-only ArXiv records."""
    source_input = (
        session.query(SourceInput)
        .filter(SourceInput.id == source_input_id, SourceInput.user_id == current_user.id)
        .first()
    )
    if not source_input:
        raise HTTPException(status_code=404, detail="来源输入不存在")
    if source_input.source_type != "arxiv":
        raise HTTPException(status_code=400, detail="仅支持 ArXiv 来源重试")
    if not source_input.metadata_only:
        raise HTTPException(status_code=400, detail="该来源无需重试 PDF 解析")
    if not source_input.pdf_url:
        raise HTTPException(status_code=400, detail="该来源缺少 PDF 地址，无法重试")

    try:

        def _download_and_parse():
            pdf = download_to_temp_file(source_input.pdf_url)
            try:
                md = extract_markdown_from_pdf(pdf)
                return pdf, md
            except Exception:
                safe_delete_file(str(pdf))
                raise

        temp_pdf, markdown = await asyncio.to_thread(_download_and_parse)
        source_input.downloaded_pdf_path = str(temp_pdf)
        source_input.extracted_markdown = markdown
        source_input.status = "succeeded"
        source_input.metadata_only = False
        source_input.error_message = None
    except Exception as exc:
        source_input.status = "failed"
        source_input.metadata_only = True
        source_input.error_message = f"PDF 下载或解析失败，可稍后重试: {exc}"
    finally:
        safe_delete_file(source_input.downloaded_pdf_path)
        source_input.downloaded_pdf_path = None

    session.flush()
    session.refresh(source_input)
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
        raise HTTPException(status_code=404, detail="来源输入不存在")

    session.delete(source_input)
    return MessageResponse(message="来源输入已删除")
