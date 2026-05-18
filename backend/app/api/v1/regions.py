from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.region import (
    RegionCreate,
    RegionUpdate,
    RegionResponse,
    RegionHealthSummary,
)
from app.services.region_service import region_service

router = APIRouter()


@router.get("", response_model=list[RegionResponse])
async def list_regions(db: AsyncSession = Depends(get_db)):
    return await region_service.list_regions(db)


@router.post("", response_model=RegionResponse)
async def create_region(data: RegionCreate, db: AsyncSession = Depends(get_db)):
    existing = await region_service.get_region_by_code(db, data.code)
    if existing:
        raise HTTPException(status_code=400, detail="Region code already exists")
    return await region_service.create_region(db, data.model_dump())


@router.get("/global-map")
async def global_quality_map(db: AsyncSession = Depends(get_db)):
    return await region_service.get_global_quality_map(db)


@router.get("/{region_id}", response_model=RegionResponse)
async def get_region(region_id: int, db: AsyncSession = Depends(get_db)):
    region = await region_service.get_region(db, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.put("/{region_id}", response_model=RegionResponse)
async def update_region(region_id: int, data: RegionUpdate, db: AsyncSession = Depends(get_db)):
    region = await region_service.update_region(db, region_id, data.model_dump(exclude_unset=True))
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@router.get("/{region_id}/health")
async def get_region_health(region_id: int, db: AsyncSession = Depends(get_db)):
    region = await region_service.get_region(db, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    return await region_service.get_region_health(db, region.code)
