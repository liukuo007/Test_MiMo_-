from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.device import DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    name: str
    device_sn: str
    device_type: DeviceType = DeviceType.REAL
    region: str = "cn"
    firmware_version: Optional[str] = None
    project_id: Optional[int] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[DeviceStatus] = None
    firmware_version: Optional[str] = None
    project_id: Optional[int] = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    device_sn: str
    device_type: DeviceType
    status: DeviceStatus
    region: str
    firmware_version: Optional[str]
    ip_address: Optional[str]
    temperature: Optional[float]
    project_id: Optional[int]
    occupied_by: Optional[int]
    last_heartbeat: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceControlRequest(BaseModel):
    action: str  # open_door, close_door, restart, upgrade_firmware, set_light
    payload: Optional[dict] = None


class VirtualDeviceCreate(BaseModel):
    count: int = 1
    device_type: DeviceType = DeviceType.VIRTUAL_L2
    region: str = "cn"
    project_id: Optional[int] = None
