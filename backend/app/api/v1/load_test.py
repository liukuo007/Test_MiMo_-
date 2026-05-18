from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.load_test import (
    TrafficProfileCreate,
    TrafficProfileResponse,
    LoadTestRunResponse,
    LoadTestMetricResponse,
    RunLoadTestRequest,
)
from app.services.load_test_service import load_test_service
from app.models.load_test import TrafficProfile

router = APIRouter()


async def _enrich_run(run, db: AsyncSession):
    """Add profile_name to run response."""
    resp = LoadTestRunResponse.model_validate(run)
    if run.profile_id:
        from sqlalchemy import select
        result = await db.execute(select(TrafficProfile.name).where(TrafficProfile.id == run.profile_id))
        name = result.scalar_one_or_none()
        resp.profile_name = name
    return resp


@router.get("/profiles", response_model=list[TrafficProfileResponse])
async def list_profiles(db: AsyncSession = Depends(get_db)):
    return await load_test_service.list_profiles(db)


@router.post("/profiles", response_model=TrafficProfileResponse)
async def create_profile(data: TrafficProfileCreate, db: AsyncSession = Depends(get_db)):
    return await load_test_service.create_profile(db, data.model_dump())


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    ok = await load_test_service.delete_profile(db, profile_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"ok": True}


@router.get("/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    return await load_test_service.list_runs(db)


@router.post("/runs")
async def create_run(data: RunLoadTestRequest, db: AsyncSession = Depends(get_db)):
    run = await load_test_service.create_run(db, data.profile_id, data.device_count, data.virtual_device_count)
    return await _enrich_run(run, db)


@router.get("/runs/{run_id}")
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await load_test_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return await _enrich_run(run, db)


@router.get("/runs/{run_id}/metrics", response_model=list[LoadTestMetricResponse])
async def get_run_metrics(run_id: int, db: AsyncSession = Depends(get_db)):
    return await load_test_service.get_run_metrics(db, run_id)


@router.post("/runs/{run_id}/execute")
async def execute_run(run_id: int, db: AsyncSession = Depends(get_db)):
    try:
        run = await load_test_service.simulate_run(db, run_id)
        return await _enrich_run(run, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
