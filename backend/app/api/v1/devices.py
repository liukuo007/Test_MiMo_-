from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.device import Device, DeviceStatus
from app.models.device_event import DeviceEvent, DeviceEventType
from app.schemas.device import DeviceControlRequest, DeviceCreate, DeviceResponse, DeviceUpdate, VirtualDeviceCreate
from app.schemas.device_event import DeviceEventResponse
from app.services.device_service import device_service

router = APIRouter()


@router.get("")
async def list_devices(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
    status: Optional[DeviceStatus] = None,
    region: Optional[str] = None,
    project_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(Device)
    count_query = select(func.count(Device.id))
    if status:
        query = query.where(Device.status == status)
        count_query = count_query.where(Device.status == status)
    if region:
        query = query.where(Device.region == region)
        count_query = count_query.where(Device.region == region)
    if project_id:
        query = query.where(Device.project_id == project_id)
        count_query = count_query.where(Device.project_id == project_id)
    if search:
        search_filter = or_(Device.name.ilike(f"%{search}%"), Device.device_sn.ilike(f"%{search}%"))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit).order_by(Device.id.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=DeviceResponse)
async def create_device(req: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device = Device(**req.model_dump())
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device


@router.post("/virtual", response_model=list[DeviceResponse])
async def create_virtual_devices(req: VirtualDeviceCreate, db: AsyncSession = Depends(get_db)):
    devices = await device_service.create_virtual_batch(
        db, req.count, req.device_type, req.region, req.project_id
    )
    for d in devices:
        await db.refresh(d)
    return devices


class VirtualHeartbeat(BaseModel):
    device_sn: str
    state: str
    temperature: float = 25.0


class VirtualEvent(BaseModel):
    device_sn: str
    event_type: str
    details: Optional[dict] = None


@router.post("/virtual/heartbeat")
async def virtual_heartbeat(req: VirtualHeartbeat, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.device_sn == req.device_sn))
    device = result.scalar_one_or_none()
    if not device:
        return {"status": "ignored", "reason": "device_not_found"}

    from datetime import datetime
    device.last_heartbeat = datetime.now()
    device.temperature = req.temperature
    if req.state == "offline":
        device.status = DeviceStatus.OFFLINE
    else:
        device.status = DeviceStatus.ONLINE
    await db.flush()
    return {"status": "ok"}


@router.post("/virtual/event")
async def virtual_event(req: VirtualEvent, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.device_sn == req.device_sn))
    device = result.scalar_one_or_none()
    if not device:
        return {"status": "ignored", "reason": "device_not_found"}

    event = DeviceEvent(
        device_id=device.id,
        event_type=DeviceEventType.STATE_CHANGE,
        message=f"Event: {req.event_type}",
        details=req.details or {},
    )
    db.add(event)
    await db.flush()
    return {"status": "ok"}


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundError("Device", device_id)
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: int, req: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundError("Device", device_id)

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    await db.flush()
    await db.refresh(device)
    return device


@router.post("/{device_id}/occupy", response_model=DeviceResponse)
async def occupy_device(device_id: int, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    device = await device_service.occupy(db, device_id, int(current_user["sub"]))
    return device


@router.post("/{device_id}/release", response_model=DeviceResponse)
async def release_device(device_id: int, db: AsyncSession = Depends(get_db)):
    device = await device_service.release(db, device_id)
    return device


@router.post("/{device_id}/control")
async def control_device(device_id: int, req: DeviceControlRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise NotFoundError("Device", device_id)

    # 通过 MQTT 下发真实设备指令
    from app.iot.mqtt_client import mqtt_client
    mqtt_client.publish_command(device.device_sn, req.action, req.payload or {})

    event = DeviceEvent(
        device_id=device_id,
        event_type=DeviceEventType.CONTROL,
        message=f"Control action '{req.action}' sent via MQTT",
        details={"action": req.action, "mqtt": mqtt_client.is_connected},
    )
    db.add(event)
    await db.flush()

    return {"message": f"Action '{req.action}' sent to device '{device.device_sn}'", "status": "accepted"}


@router.get("/{device_id}/events", response_model=list[DeviceEventResponse])
async def get_device_events(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    if not device_result.scalar_one_or_none():
        raise NotFoundError("Device", device_id)

    result = await db.execute(
        select(DeviceEvent)
        .where(DeviceEvent.device_id == device_id)
        .order_by(DeviceEvent.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
