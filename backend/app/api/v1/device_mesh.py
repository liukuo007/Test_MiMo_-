from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.device_pool import (
    AssignDevicesRequest,
    DeviceHealthScoreResponse,
    DevicePoolCreate,
    DevicePoolResponse,
    DevicePoolUpdate,
    DeviceTagCreate,
    DeviceTagResponse,
    ScheduleRequest,
)
from app.services.device_mesh_service import device_mesh_service

router = APIRouter()


# --- Pool CRUD ---
@router.get("/pools", response_model=list[DevicePoolResponse])
async def list_pools(db: AsyncSession = Depends(get_db)):
    pools = await device_mesh_service.list_pools(db)
    result = []
    for p in pools:
        data = DevicePoolResponse.model_validate(p)
        data.device_count = len(p.members) if p.members else 0
        result.append(data)
    return result


@router.post("/pools", response_model=DevicePoolResponse)
async def create_pool(data: DevicePoolCreate, db: AsyncSession = Depends(get_db)):
    pool = await device_mesh_service.create_pool(db, data.model_dump())
    resp = DevicePoolResponse.model_validate(pool)
    resp.device_count = 0
    return resp


@router.get("/pools/{pool_id}", response_model=DevicePoolResponse)
async def get_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    pool = await device_mesh_service.get_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    resp = DevicePoolResponse.model_validate(pool)
    resp.device_count = len(pool.members) if pool.members else 0
    return resp


@router.put("/pools/{pool_id}", response_model=DevicePoolResponse)
async def update_pool(pool_id: int, data: DevicePoolUpdate, db: AsyncSession = Depends(get_db)):
    pool = await device_mesh_service.update_pool(db, pool_id, data.model_dump(exclude_unset=True))
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    resp = DevicePoolResponse.model_validate(pool)
    resp.device_count = len(pool.members) if pool.members else 0
    return resp


@router.delete("/pools/{pool_id}")
async def delete_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    ok = await device_mesh_service.delete_pool(db, pool_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Pool not found")
    return {"ok": True}


# --- Pool Members ---
@router.post("/pools/{pool_id}/assign")
async def assign_devices(pool_id: int, data: AssignDevicesRequest, db: AsyncSession = Depends(get_db)):
    members = await device_mesh_service.assign_devices(db, pool_id, data.device_ids)
    return {"assigned": len(members)}


@router.delete("/pools/{pool_id}/devices/{device_id}")
async def remove_device(pool_id: int, device_id: int, db: AsyncSession = Depends(get_db)):
    ok = await device_mesh_service.remove_device(db, pool_id, device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"ok": True}


@router.get("/pools/{pool_id}/devices")
async def get_pool_devices(pool_id: int, db: AsyncSession = Depends(get_db)):
    return await device_mesh_service.get_pool_devices(db, pool_id)


# --- Tags ---
@router.post("/devices/{device_id}/tags", response_model=list[DeviceTagResponse])
async def add_tags(device_id: int, data: list[DeviceTagCreate], db: AsyncSession = Depends(get_db)):
    return await device_mesh_service.add_tags(db, device_id, [t.model_dump() for t in data])


@router.get("/devices/{device_id}/tags", response_model=list[DeviceTagResponse])
async def get_device_tags(device_id: int, db: AsyncSession = Depends(get_db)):
    return await device_mesh_service.get_device_tags(db, device_id)


@router.delete("/tags/{tag_id}")
async def remove_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    ok = await device_mesh_service.remove_tag(db, tag_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"ok": True}


@router.get("/devices/by-tags")
async def get_devices_by_tags(tags: str = "", db: AsyncSession = Depends(get_db)):
    """Query by tags as key=value pairs, e.g. ?tags=region=SG,os=android"""
    tag_dict = {}
    for pair in tags.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            tag_dict[k.strip()] = v.strip()
    if not tag_dict:
        return []
    return await device_mesh_service.get_devices_by_tags(db, tag_dict)


# --- Health Score ---
@router.get("/devices/{device_id}/health", response_model=DeviceHealthScoreResponse)
async def get_health_score(device_id: int, db: AsyncSession = Depends(get_db)):
    return await device_mesh_service.compute_health_score(db, device_id)


# --- Scheduling ---
@router.post("/pools/{pool_id}/schedule")
async def auto_schedule(pool_id: int, data: ScheduleRequest, db: AsyncSession = Depends(get_db)):
    devices = await device_mesh_service.auto_schedule(db, pool_id, data.strategy, data.count)
    return {"devices": devices}
