"""Experience pool (信息池) API routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...llm.config import llm_not_configured_message, llm_provider_for_user_settings
from ...models.schema import (
    ExperienceCluster,
    ExperiencePool,
    ExperienceSeed,
    ExperienceStory,
    PoolComposition,
    User,
    UserProfile,
    UserSettings,
)
from ..deps import get_current_user, get_db_session
from ..errors import ErrorCode, raise_api_error
from ..experience_pool_service import (
    STORY_FIELDS,
    count_pool_stats,
    count_pool_stats_bulk,
    ensure_story_for_seed,
    format_story_text,
    get_cluster_for_pool,
    get_pool_for_user,
    list_detail_seeds,
    story_completion,
)
from ..schemas import (
    ExperienceClusterCreate,
    ExperienceClusterMergeRequest,
    ExperienceClusterResponse,
    ExperienceClusterUpdate,
    ExperiencePoolCreate,
    ExperiencePoolResponse,
    ExperiencePoolUpdate,
    ExperienceSeedBatchCreate,
    ExperienceSeedCreate,
    ExperienceSeedResponse,
    ExperienceSeedUpdate,
    ExperienceStoryResponse,
    ExperienceStoryUpdate,
    MessageResponse,
    PoolCompositionApplyRequest,
    PoolCompositionCreate,
    PoolCompositionGenerateRequest,
    PoolCompositionResponse,
    PoolCompositionUpdate,
)

router = APIRouter(prefix="/pools", tags=["信息池"])


def _pool_response(
    session: Session,
    pool: ExperiencePool,
    stats: Optional[tuple[int, int]] = None,
) -> ExperiencePoolResponse:
    seed_count, story_count = stats if stats is not None else count_pool_stats(session, pool)
    return ExperiencePoolResponse(
        id=pool.id,
        title=pool.title,
        description=pool.description,
        phase=pool.phase or "brainstorm",
        seed_count=seed_count,
        story_count=story_count,
        created_at=pool.created_at,
        updated_at=pool.updated_at,
    )


def _require_pool(session: Session, pool_id: int, user_id: int) -> ExperiencePool:
    pool = get_pool_for_user(session, pool_id, user_id)
    if not pool:
        raise_api_error(404, ErrorCode.EXPERIENCE_POOL_NOT_FOUND, "信息池不存在")
    return pool


def _require_seed(session: Session, seed_id: int, pool_id: int) -> ExperienceSeed:
    seed = (
        session.query(ExperienceSeed)
        .filter(ExperienceSeed.id == seed_id, ExperienceSeed.pool_id == pool_id)
        .first()
    )
    if not seed:
        raise_api_error(404, ErrorCode.EXPERIENCE_SEED_NOT_FOUND, "经历线索不存在")
    return seed


def _story_response(story: ExperienceStory, seed: ExperienceSeed) -> ExperienceStoryResponse:
    cluster_title = None
    if seed.cluster is not None:
        cluster_title = seed.cluster.title
    return ExperienceStoryResponse(
        id=story.id,
        seed_id=seed.id,
        seed_content=seed.content or "",
        cluster_id=seed.cluster_id,
        cluster_title=cluster_title,
        standalone=bool(seed.standalone),
        origin=story.origin,
        process=story.process,
        outcome=story.outcome,
        problems=story.problems,
        setbacks=story.setbacks,
        knowledge=story.knowledge,
        insights=story.insights,
        freeform=story.freeform,
        completion=story_completion(story),
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


# ---- Pools ----


@router.get("", response_model=List[ExperiencePoolResponse])
def list_pools(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pools = (
        session.query(ExperiencePool)
        .filter(ExperiencePool.user_id == current_user.id)
        .order_by(ExperiencePool.updated_at.desc())
        .all()
    )
    stats = count_pool_stats_bulk(session, [p.id for p in pools])
    return [_pool_response(session, p, stats.get(p.id)) for p in pools]


@router.post("", response_model=ExperiencePoolResponse, status_code=status.HTTP_201_CREATED)
def create_pool(
    data: ExperiencePoolCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = ExperiencePool(
        user_id=current_user.id,
        title=data.title.strip(),
        description=(data.description or "").strip() or None,
        phase="brainstorm",
    )
    session.add(pool)
    session.flush()
    session.refresh(pool)
    return _pool_response(session, pool)


@router.get("/{pool_id}", response_model=ExperiencePoolResponse)
def get_pool(
    pool_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    return _pool_response(session, pool)


@router.put("/{pool_id}", response_model=ExperiencePoolResponse)
def update_pool(
    pool_id: int,
    data: ExperiencePoolUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    if data.title is not None:
        pool.title = data.title.strip()
    if data.description is not None:
        pool.description = data.description.strip() or None
    if data.phase is not None:
        pool.phase = data.phase
    session.flush()
    session.refresh(pool)
    return _pool_response(session, pool)


@router.delete("/{pool_id}", response_model=MessageResponse)
def delete_pool(
    pool_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    session.query(UserProfile).filter(UserProfile.experience_pool_id == pool.id).update(
        {"experience_pool_id": None}
    )
    session.delete(pool)
    return MessageResponse(message="信息池已删除")


# ---- Seeds ----


@router.get("/{pool_id}/seeds", response_model=List[ExperienceSeedResponse])
def list_seeds(
    pool_id: int,
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    query = session.query(ExperienceSeed).filter(ExperienceSeed.pool_id == pool_id)
    if status_filter in ("active", "discarded"):
        query = query.filter(ExperienceSeed.status == status_filter)
    seeds = query.order_by(ExperienceSeed.sort_order.asc(), ExperienceSeed.id.asc()).all()
    return seeds


@router.post(
    "/{pool_id}/seeds",
    response_model=ExperienceSeedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_seed(
    pool_id: int,
    data: ExperienceSeedCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    max_order = (
        session.query(ExperienceSeed)
        .filter(ExperienceSeed.pool_id == pool.id)
        .count()
    )
    seed = ExperienceSeed(
        pool_id=pool.id,
        content=data.content.strip(),
        tags=data.tags or [],
        status="active",
        sort_order=max_order,
    )
    session.add(seed)
    session.flush()
    session.refresh(seed)
    return seed


@router.post(
    "/{pool_id}/seeds/batch",
    response_model=List[ExperienceSeedResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_seeds_batch(
    pool_id: int,
    data: ExperienceSeedBatchCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    base_order = (
        session.query(ExperienceSeed)
        .filter(ExperienceSeed.pool_id == pool.id)
        .count()
    )
    created: list[ExperienceSeed] = []
    offset = 0
    for raw in data.contents:
        text = (raw or "").strip()
        if not text:
            continue
        seed = ExperienceSeed(
            pool_id=pool.id,
            content=text,
            tags=[],
            status="active",
            sort_order=base_order + offset,
        )
        session.add(seed)
        created.append(seed)
        offset += 1
    session.flush()
    for seed in created:
        session.refresh(seed)
    return created


@router.put("/{pool_id}/seeds/{seed_id}", response_model=ExperienceSeedResponse)
def update_seed(
    pool_id: int,
    seed_id: int,
    data: ExperienceSeedUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    seed = _require_seed(session, seed_id, pool_id)
    if data.content is not None:
        seed.content = data.content.strip()
    if data.status is not None:
        seed.status = data.status
    if data.clear_cluster:
        seed.cluster_id = None
    elif data.cluster_id is not None:
        cluster = get_cluster_for_pool(session, data.cluster_id, pool_id)
        if not cluster:
            raise_api_error(404, ErrorCode.EXPERIENCE_CLUSTER_NOT_FOUND, "聚类不存在")
        seed.cluster_id = data.cluster_id
    if data.standalone is not None:
        seed.standalone = data.standalone
    if data.sort_order is not None:
        seed.sort_order = data.sort_order
    if data.tags is not None:
        seed.tags = data.tags
    session.flush()
    session.refresh(seed)
    return seed


@router.delete("/{pool_id}/seeds/{seed_id}", response_model=MessageResponse)
def delete_seed(
    pool_id: int,
    seed_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    seed = _require_seed(session, seed_id, pool_id)
    session.delete(seed)
    return MessageResponse(message="经历线索已删除")


# ---- Clusters ----


@router.get("/{pool_id}/clusters", response_model=List[ExperienceClusterResponse])
def list_clusters(
    pool_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    return (
        session.query(ExperienceCluster)
        .filter(ExperienceCluster.pool_id == pool_id)
        .order_by(ExperienceCluster.sort_order.asc(), ExperienceCluster.id.asc())
        .all()
    )


@router.post(
    "/{pool_id}/clusters",
    response_model=ExperienceClusterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_cluster(
    pool_id: int,
    data: ExperienceClusterCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    count = (
        session.query(ExperienceCluster)
        .filter(ExperienceCluster.pool_id == pool.id)
        .count()
    )
    cluster = ExperienceCluster(
        pool_id=pool.id,
        title=data.title.strip(),
        note=(data.note or "").strip() or None,
        color=data.color,
        sort_order=count,
    )
    session.add(cluster)
    session.flush()
    session.refresh(cluster)
    return cluster


@router.put("/{pool_id}/clusters/{cluster_id}", response_model=ExperienceClusterResponse)
def update_cluster(
    pool_id: int,
    cluster_id: int,
    data: ExperienceClusterUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    cluster = get_cluster_for_pool(session, cluster_id, pool_id)
    if not cluster:
        raise_api_error(404, ErrorCode.EXPERIENCE_CLUSTER_NOT_FOUND, "聚类不存在")
    if data.title is not None:
        cluster.title = data.title.strip()
    if data.note is not None:
        cluster.note = data.note.strip() or None
    if data.color is not None:
        cluster.color = data.color
    if data.sort_order is not None:
        cluster.sort_order = data.sort_order
    session.flush()
    session.refresh(cluster)
    return cluster


@router.delete("/{pool_id}/clusters/{cluster_id}", response_model=MessageResponse)
def delete_cluster(
    pool_id: int,
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    cluster = get_cluster_for_pool(session, cluster_id, pool_id)
    if not cluster:
        raise_api_error(404, ErrorCode.EXPERIENCE_CLUSTER_NOT_FOUND, "聚类不存在")
    session.query(ExperienceSeed).filter(ExperienceSeed.cluster_id == cluster.id).update(
        {"cluster_id": None}
    )
    session.delete(cluster)
    return MessageResponse(message="聚类已删除")


@router.post("/{pool_id}/clusters/merge", response_model=ExperienceClusterResponse)
def merge_clusters(
    pool_id: int,
    data: ExperienceClusterMergeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    source = get_cluster_for_pool(session, data.source_cluster_id, pool_id)
    target = get_cluster_for_pool(session, data.target_cluster_id, pool_id)
    if not source or not target:
        raise_api_error(404, ErrorCode.EXPERIENCE_CLUSTER_NOT_FOUND, "聚类不存在")
    if source.id == target.id:
        raise_api_error(400, ErrorCode.BAD_REQUEST, "不能将聚类合并到自身")
    session.query(ExperienceSeed).filter(ExperienceSeed.cluster_id == source.id).update(
        {"cluster_id": target.id}
    )
    session.delete(source)
    session.flush()
    session.refresh(target)
    return target


# ---- Stories ----


@router.get("/{pool_id}/stories", response_model=List[ExperienceStoryResponse])
def list_stories(
    pool_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    seeds = list_detail_seeds(session, pool_id)
    results: list[ExperienceStoryResponse] = []
    for seed in seeds:
        story = ensure_story_for_seed(session, seed)
        results.append(_story_response(story, seed))
    return results


@router.put("/{pool_id}/stories/{seed_id}", response_model=ExperienceStoryResponse)
def update_story(
    pool_id: int,
    seed_id: int,
    data: ExperienceStoryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    seed = _require_seed(session, seed_id, pool_id)
    if seed.status != "active" or (seed.cluster_id is None and not seed.standalone):
        raise_api_error(
            400,
            ErrorCode.BAD_REQUEST,
            "仅可对已聚类或独立保留的活跃线索撰写细节",
        )
    story = ensure_story_for_seed(session, seed)
    for field in STORY_FIELDS:
        value = getattr(data, field)
        if value is not None:
            setattr(story, field, value)
    session.flush()
    session.refresh(story)
    return _story_response(story, seed)


# ---- Compositions ----


@router.get("/{pool_id}/compositions", response_model=List[PoolCompositionResponse])
def list_compositions(
    pool_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    return (
        session.query(PoolComposition)
        .filter(PoolComposition.pool_id == pool_id)
        .order_by(PoolComposition.updated_at.desc())
        .all()
    )


@router.post(
    "/{pool_id}/compositions",
    response_model=PoolCompositionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_composition(
    pool_id: int,
    data: PoolCompositionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    composition = PoolComposition(
        pool_id=pool.id,
        doc_type=data.doc_type,
        title=data.title.strip(),
        body=data.body or "",
        source_story_ids=data.source_story_ids or [],
    )
    session.add(composition)
    session.flush()
    session.refresh(composition)
    return composition


@router.put(
    "/{pool_id}/compositions/{composition_id}",
    response_model=PoolCompositionResponse,
)
def update_composition(
    pool_id: int,
    composition_id: int,
    data: PoolCompositionUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    composition = (
        session.query(PoolComposition)
        .filter(PoolComposition.id == composition_id, PoolComposition.pool_id == pool_id)
        .first()
    )
    if not composition:
        raise_api_error(404, ErrorCode.POOL_COMPOSITION_NOT_FOUND, "文书片段不存在")
    if data.doc_type is not None:
        composition.doc_type = data.doc_type
    if data.title is not None:
        composition.title = data.title.strip()
    if data.body is not None:
        composition.body = data.body
    if data.source_story_ids is not None:
        composition.source_story_ids = data.source_story_ids
    session.flush()
    session.refresh(composition)
    return composition


@router.delete(
    "/{pool_id}/compositions/{composition_id}",
    response_model=MessageResponse,
)
def delete_composition(
    pool_id: int,
    composition_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    _require_pool(session, pool_id, current_user.id)
    composition = (
        session.query(PoolComposition)
        .filter(PoolComposition.id == composition_id, PoolComposition.pool_id == pool_id)
        .first()
    )
    if not composition:
        raise_api_error(404, ErrorCode.POOL_COMPOSITION_NOT_FOUND, "文书片段不存在")
    session.delete(composition)
    return MessageResponse(message="文书片段已删除")


@router.post(
    "/{pool_id}/compositions/generate",
    response_model=PoolCompositionResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_composition_draft(
    pool_id: int,
    data: PoolCompositionGenerateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Explicit LLM draft from selected stories (does not auto-run elsewhere)."""
    pool = _require_pool(session, pool_id, current_user.id)
    user_settings = (
        session.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    )
    provider = llm_provider_for_user_settings(user_settings)
    if not provider.enabled:
        raise_api_error(503, ErrorCode.LLM_NOT_CONFIGURED, llm_not_configured_message())

    stories = (
        session.query(ExperienceStory, ExperienceSeed)
        .join(ExperienceSeed, ExperienceStory.seed_id == ExperienceSeed.id)
        .filter(
            ExperienceStory.id.in_(data.story_ids),
            ExperienceSeed.pool_id == pool.id,
        )
        .all()
    )
    if not stories:
        raise_api_error(400, ErrorCode.BAD_REQUEST, "请选择至少一条细化经历")

    lang = data.language if data.language in ("zh", "en") else "zh"
    blocks = [
        format_story_text(story, seed.content or "", language=lang)
        for story, seed in stories
    ]
    source_text = "\n\n---\n\n".join(b for b in blocks if b)

    doc_labels = {
        "resume_bullet": ("简历条目", "resume bullet points"),
        "personal_statement": ("个人陈述片段", "personal statement excerpt"),
        "research_plan": ("研究计划片段", "research plan excerpt"),
        "letter_snippet": ("联系信素材", "contact letter snippet"),
    }
    label_zh, label_en = doc_labels[data.doc_type]
    if lang == "zh":
        system = (
            "你是学术文书写作助手。根据用户提供的经历细节，起草指定类型的文书片段。"
            "只基于给定素材，不要编造经历。输出纯正文，不要前言。"
        )
        user_prompt = (
            f"文书类型：{label_zh}\n\n经历素材：\n{source_text}\n\n请起草正文。"
        )
        default_title = f"{label_zh}草稿"
    else:
        system = (
            "You help draft academic application writing from the user's experience notes. "
            "Use only the provided material; do not invent facts. Output the draft body only."
        )
        user_prompt = (
            f"Document type: {label_en}\n\nSource experiences:\n{source_text}\n\n"
            "Draft the body."
        )
        default_title = f"{label_en} draft"

    body = provider.chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )

    composition = PoolComposition(
        pool_id=pool.id,
        doc_type=data.doc_type,
        title=(data.title or default_title).strip(),
        body=(body or "").strip(),
        source_story_ids=list(data.story_ids),
    )
    session.add(composition)
    session.flush()
    session.refresh(composition)
    return composition


@router.post(
    "/{pool_id}/compositions/{composition_id}/apply",
    response_model=MessageResponse,
)
def apply_composition_to_profile(
    pool_id: int,
    composition_id: int,
    data: PoolCompositionApplyRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    pool = _require_pool(session, pool_id, current_user.id)
    composition = (
        session.query(PoolComposition)
        .filter(PoolComposition.id == composition_id, PoolComposition.pool_id == pool.id)
        .first()
    )
    if not composition:
        raise_api_error(404, ErrorCode.POOL_COMPOSITION_NOT_FOUND, "文书片段不存在")

    profile = (
        session.query(UserProfile)
        .filter(UserProfile.id == data.profile_id, UserProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise_api_error(404, ErrorCode.PROFILE_NOT_FOUND, "画像不存在")

    if profile.experience_pool_id != pool.id:
        profile.experience_pool_id = pool.id

    manual = dict(profile.manual_inputs or {})
    doc_type = composition.doc_type
    if doc_type == "personal_statement":
        existing = (manual.get("personal_statement") or "").strip()
        manual["personal_statement"] = (
            f"{existing}\n\n{composition.body}".strip() if existing else composition.body
        )
    elif doc_type == "research_plan":
        existing = (manual.get("research_plan") or "").strip()
        manual["research_plan"] = (
            f"{existing}\n\n{composition.body}".strip() if existing else composition.body
        )
    elif doc_type == "letter_snippet":
        existing = (manual.get("notes") or "").strip()
        note_block = f"[联系信素材 · {composition.title}]\n{composition.body}"
        manual["notes"] = f"{existing}\n\n{note_block}".strip() if existing else note_block
    else:
        # resume_bullet → append research_experience entry
        experiences = list(profile.research_experience or [])
        experiences.append(
            {
                "title": composition.title,
                "organization": "",
                "description": composition.body,
                "period": "",
            }
        )
        profile.research_experience = experiences

    profile.manual_inputs = manual
    session.flush()
    return MessageResponse(message="已应用到学生画像")
