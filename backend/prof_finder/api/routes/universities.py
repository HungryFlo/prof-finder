"""University CRUD routes and LLM-based name variant generation."""

import asyncio
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ..deps import get_current_user, get_db_session
from ...models.schema import University, UniversityCrawlerConfig, User
from ..schemas import (
    MessageResponse,
    UniversityCreate,
    UniversityResponse,
    UniversityUpdate,
)

router = APIRouter(prefix="/universities", tags=["universities"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[UniversityResponse])
def list_universities(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """List all universities for the current user."""
    rows = (
        session.query(University)
        .filter(University.user_id == current_user.id)
        .order_by(University.created_at.desc())
        .all()
    )
    return rows


@router.post("", response_model=UniversityResponse)
async def create_university(
    body: UniversityCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Create a university and generate name variants via LLM."""
    # Check duplicate
    existing = (
        session.query(University)
        .filter(
            University.user_id == current_user.id,
            University.full_name == body.full_name,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="该学校已存在")

    # Generate name variants via LLM
    variants = await _generate_name_variants(body.full_name)

    university = University(
        user_id=current_user.id,
        full_name=body.full_name,
        name_variants=variants,
    )
    session.add(university)
    session.flush()
    return university


@router.get("/{university_id}", response_model=UniversityResponse)
def get_university(
    university_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get a single university by ID."""
    university = (
        session.query(University)
        .filter(University.id == university_id, University.user_id == current_user.id)
        .first()
    )
    if not university:
        raise HTTPException(status_code=404, detail="学校不存在")
    return university


@router.put("/{university_id}", response_model=UniversityResponse)
def update_university(
    university_id: int,
    body: UniversityUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update a university (name or variants)."""
    university = (
        session.query(University)
        .filter(University.id == university_id, University.user_id == current_user.id)
        .first()
    )
    if not university:
        raise HTTPException(status_code=404, detail="学校不存在")

    if body.full_name is not None:
        university.full_name = body.full_name
    if body.name_variants is not None:
        university.name_variants = body.name_variants

    return university


@router.delete("/{university_id}", response_model=MessageResponse)
def delete_university(
    university_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Delete a university (only if no crawler configs reference it)."""
    university = (
        session.query(University)
        .filter(University.id == university_id, University.user_id == current_user.id)
        .first()
    )
    if not university:
        raise HTTPException(status_code=404, detail="学校不存在")

    # Check for referencing crawler configs
    ref_count = (
        session.query(UniversityCrawlerConfig)
        .filter(UniversityCrawlerConfig.university_id == university_id)
        .count()
    )
    if ref_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"仍有 {ref_count} 个爬虫配置引用此学校，请先解除关联",
        )

    session.delete(university)
    return MessageResponse(message="学校已删除")


# ---------------------------------------------------------------------------
# LLM name variant generation
# ---------------------------------------------------------------------------


async def _generate_name_variants(full_name: str) -> list[str]:
    """Use LLM to generate search keyword variants for a university name.

    Returns a list like ["XJTU", "Xi'an Jiaotong University", "西安交大", "西交"].
    """
    from ...ai_workflows.provider import LLMProvider
    from ...llm.config import resolve_llm_config

    try:
        config = resolve_llm_config()
        provider = LLMProvider(config=config)
        if not provider.enabled:
            logger.warning("No LLM API configured, returning empty variants")
            return []

        prompt = f"""你是一个大学名称变体生成器。给定一个大学的中文全名，请列出该大学在 Google Scholar 搜索中可能出现的所有名称变体。

要求：
1. 英文全称
2. 英文常用缩写
3. 中文简称
4. 其他常见变体（如有）

只返回 JSON 数组，不要其他文字。例如：
输入：西安交通大学
输出：["Xi'an Jiaotong University", "XJTU", "西安交大", "西交", "Xi'an Jiaotong Univ"]

输入：{full_name}
输出："""

        def _call_llm() -> list[str]:
            content = provider.chat_completion(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            return _parse_variants_response(content)

        # Run blocking LLM call in thread pool
        variants = await asyncio.to_thread(_call_llm)
        return variants

    except Exception as e:
        logger.warning("Failed to generate name variants for '%s': %s", full_name, e)
        return []


def _parse_variants_response(content: str) -> list[str]:
    """Parse JSON array from LLM response."""
    import json

    content = content.strip()
    # Remove markdown fences
    if content.startswith("```"):
        lines = content.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []

    try:
        result = json.loads(content[start : end + 1])
        if isinstance(result, list):
            return [str(v).strip() for v in result if v]
    except json.JSONDecodeError:
        pass

    return []
