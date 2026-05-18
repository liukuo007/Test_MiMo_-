from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.health_score import HealthScoreSnapshot
from app.services.health_score_service import health_score_service, RELEASE_THRESHOLD
from app.schemas.health_score import (
    HealthScoreResponse,
    DimensionDetail,
    HealthScoreTrend,
    HealthScoreTrendItem,
    ReleaseGateResponse,
)

router = APIRouter()


@router.get("", response_model=HealthScoreResponse)
async def get_health_score(
    project_id: Optional[int] = None,
    region: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await health_score_service.compute_health_score(db, project_id, region)
    return HealthScoreResponse(
        overall_score=result.overall_score,
        release_allowed=result.release_allowed,
        release_threshold=RELEASE_THRESHOLD,
        computed_at=datetime.utcnow(),
        dimensions=[
            DimensionDetail(
                name=d.name, key=d.key, weight=d.weight,
                value=d.value, score=round(d.score, 2), status=d.status,
            )
            for d in result.dimensions
        ],
    )


@router.get("/trend", response_model=HealthScoreTrend)
async def get_health_score_trend(
    days: int = Query(7, ge=1, le=90),
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)

    query = select(HealthScoreSnapshot).where(HealthScoreSnapshot.computed_at >= since)
    if project_id:
        query = query.where(HealthScoreSnapshot.project_id == project_id)

    query = query.order_by(HealthScoreSnapshot.computed_at)
    result = await db.execute(query)
    snapshots = result.scalars().all()

    return HealthScoreTrend(
        items=[
            HealthScoreTrendItem(
                overall_score=s.overall_score,
                release_allowed=s.release_allowed,
                computed_at=s.computed_at,
            )
            for s in snapshots
        ]
    )


@router.get("/release-gate", response_model=ReleaseGateResponse)
async def get_release_gate(
    project_id: Optional[int] = None,
    region: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    result = await health_score_service.compute_health_score(db, project_id, region)
    failing = [d.name for d in result.dimensions if d.status == "bad"]

    return ReleaseGateResponse(
        release_allowed=result.release_allowed,
        overall_score=result.overall_score,
        threshold=RELEASE_THRESHOLD,
        failing_dimensions=failing,
    )
