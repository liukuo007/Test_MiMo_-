from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.defect import VALID_TRANSITIONS, Defect, DefectPriority, DefectSource, DefectStatus
from app.models.user import User
from app.schemas.defect import (
    DefectAssign,
    DefectCreate,
    DefectDetailResponse,
    DefectResponse,
    DefectStatusTransition,
    DefectUpdate,
)

router = APIRouter()


@router.get("/statistics")
async def get_defect_statistics(db: AsyncSession = Depends(get_db)):
    # 按状态分组
    status_result = await db.execute(
        select(Defect.status, func.count(Defect.id)).group_by(Defect.status)
    )
    by_status = {row[0].value: row[1] for row in status_result.all()}

    # 按优先级分组
    priority_result = await db.execute(
        select(Defect.priority, func.count(Defect.id)).group_by(Defect.priority)
    )
    by_priority = {row[0].value: row[1] for row in priority_result.all()}

    # 按来源分组
    source_result = await db.execute(
        select(Defect.source, func.count(Defect.id)).group_by(Defect.source)
    )
    by_source = {row[0].value: row[1] for row in source_result.all()}

    total = sum(by_status.values())

    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_source": by_source,
    }


@router.get("")
async def list_defects(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
    status: DefectStatus | None = None,
    priority: DefectPriority | None = None,
    source: DefectSource | None = None,
    assigned_to: int | None = None,
    device_sn: str | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(Defect)
    count_query = select(func.count(Defect.id))
    filters = []
    if status:
        filters.append(Defect.status == status)
    if priority:
        filters.append(Defect.priority == priority)
    if source:
        filters.append(Defect.source == source)
    if assigned_to:
        filters.append(Defect.assigned_to == assigned_to)
    if device_sn:
        filters.append(Defect.device_sn == device_sn)
    if search:
        filters.append(Defect.title.ilike(f"%{search}%"))
    for f in filters:
        query = query.where(f)
        count_query = count_query.where(f)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit).order_by(Defect.id.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=DefectResponse)
async def create_defect(req: DefectCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    defect = Defect(
        **req.model_dump(),
        source=DefectSource.USER,
        created_by=int(current_user["sub"]),
    )
    db.add(defect)
    await db.flush()
    await db.refresh(defect)

    # MeterSphere 自动同步
    from app.config import get_settings
    if get_settings().ms_sync_enabled:
        try:
            from integrations.metersphere.sync_to_ms import metersphere_sync
            await metersphere_sync.push_defect(defect)
        except Exception:
            pass

    return defect


@router.get("/{defect_id}", response_model=DefectDetailResponse)
async def get_defect(defect_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Defect).where(Defect.id == defect_id)
        .options(selectinload(Defect.assignee), selectinload(Defect.creator))
    )
    defect = result.scalar_one_or_none()
    if not defect:
        raise NotFoundError("Defect", defect_id)

    resp = DefectDetailResponse.model_validate(defect)
    if defect.assignee:
        resp.assignee_name = defect.assignee.username
    if defect.creator:
        resp.creator_name = defect.creator.username
    return resp


@router.put("/{defect_id}", response_model=DefectResponse)
async def update_defect(defect_id: int, req: DefectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise NotFoundError("Defect", defect_id)

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(defect, field, value)

    await db.flush()
    await db.refresh(defect)
    return defect


@router.put("/{defect_id}/status", response_model=DefectResponse)
async def update_defect_status(defect_id: int, req: DefectStatusTransition, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise NotFoundError("Defect", defect_id)

    current_status = defect.status
    target_status = req.status
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise BadRequestError(
            f"Invalid status transition: {current_status.value} -> {target_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )

    defect.status = target_status
    if target_status == DefectStatus.FIXED:
        defect.resolved_at = datetime.now()
    elif target_status == DefectStatus.CLOSED:
        defect.closed_at = datetime.now()

    await db.flush()
    await db.refresh(defect)
    return defect


@router.post("/{defect_id}/assign", response_model=DefectResponse)
async def assign_defect(defect_id: int, req: DefectAssign, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise NotFoundError("Defect", defect_id)

    # 验证用户存在
    user_result = await db.execute(select(User).where(User.id == req.assigned_to))
    if not user_result.scalar_one_or_none():
        raise NotFoundError("User", req.assigned_to)

    defect.assigned_to = req.assigned_to
    if defect.status == DefectStatus.NEW:
        defect.status = DefectStatus.IN_PROGRESS

    await db.flush()
    await db.refresh(defect)
    return defect
