from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.environment import (
    EnvironmentCreate,
    EnvironmentResponse,
    EnvironmentUpdate,
    HealthCheckResponse,
    SnapshotCreate,
    SnapshotResponse,
)
from app.services.environment_service import environment_service

router = APIRouter()


@router.get("", response_model=list[EnvironmentResponse])
async def list_environments(
    env_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await environment_service.list_environments(db, env_type=env_type, status=status)


@router.post("", response_model=EnvironmentResponse)
async def create_environment(
    data: EnvironmentCreate,
    db: AsyncSession = Depends(get_db),
):
    return await environment_service.create_environment(db, data.model_dump())


@router.get("/{env_id}", response_model=EnvironmentResponse)
async def get_environment(
    env_id: int,
    db: AsyncSession = Depends(get_db),
):
    env = await environment_service.get_environment(db, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env


@router.put("/{env_id}", response_model=EnvironmentResponse)
async def update_environment(
    env_id: int,
    data: EnvironmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    env = await environment_service.update_environment(db, env_id, data.model_dump(exclude_unset=True))
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env


@router.delete("/{env_id}")
async def delete_environment(
    env_id: int,
    db: AsyncSession = Depends(get_db),
):
    ok = await environment_service.delete_environment(db, env_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {"ok": True}


@router.post("/{env_id}/health-check", response_model=list[HealthCheckResponse])
async def check_health(
    env_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await environment_service.check_health(db, env_id)


@router.post("/{env_id}/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    env_id: int,
    data: SnapshotCreate,
    db: AsyncSession = Depends(get_db),
):
    snapshot = await environment_service.create_snapshot(
        db, env_id, data.name, data.snapshot_type, data.notes
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="Environment not found")
    return snapshot


@router.get("/{env_id}/snapshots", response_model=list[SnapshotResponse])
async def list_snapshots(
    env_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await environment_service.list_snapshots(db, env_id)


@router.post("/snapshots/{snapshot_id}/restore", response_model=EnvironmentResponse)
async def restore_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db),
):
    env = await environment_service.restore_snapshot(db, snapshot_id)
    if not env:
        raise HTTPException(status_code=404, detail="Snapshot or environment not found")
    return env
