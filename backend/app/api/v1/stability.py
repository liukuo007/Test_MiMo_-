from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.stability import (
    FlakyTestCaseResponse,
    FailureClusterResponse,
    StabilityTrendResponse,
    StabilitySummary,
)
from app.services.stability_service import stability_service

router = APIRouter()


@router.get("/summary", response_model=StabilitySummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    data = await stability_service.get_summary(db)
    return StabilitySummary(
        total_flaky=data["total_flaky"],
        active_flaky=data["active_flaky"],
        resolved_flaky=data["resolved_flaky"],
        overall_stability_score=data["overall_stability_score"],
        clusters=[FailureClusterResponse.model_validate(c) for c in data["clusters"]],
        trends=[StabilityTrendResponse.model_validate(t) for t in data["trends"]],
    )


@router.get("/flaky", response_model=list[FlakyTestCaseResponse])
async def get_flaky_list(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await stability_service.get_flaky_list(db, status=status)


@router.post("/flaky/{flaky_id}/resolve")
async def resolve_flaky(flaky_id: int, db: AsyncSession = Depends(get_db)):
    ok = await stability_service.mark_resolved(db, flaky_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Flaky test not found")
    return {"ok": True}


@router.post("/detect")
async def trigger_detection(db: AsyncSession = Depends(get_db)):
    flaky = await stability_service.detect_flaky_tests(db)
    clusters = await stability_service.cluster_failures(db)
    trends = await stability_service.compute_stability_trends(db)
    return {
        "flaky_detected": len(flaky),
        "clusters_found": len(clusters),
        "trends_computed": len(trends),
    }


@router.get("/clusters", response_model=list[FailureClusterResponse])
async def get_clusters(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, desc
    from app.models.stability import FailureCluster
    result = await db.execute(select(FailureCluster).order_by(desc(FailureCluster.percentage)))
    return list(result.scalars().all())


@router.get("/trends", response_model=list[StabilityTrendResponse])
async def get_trends(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.stability import StabilityTrend
    result = await db.execute(select(StabilityTrend))
    return list(result.scalars().all())
