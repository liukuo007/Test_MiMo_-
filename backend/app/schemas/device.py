from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.device import DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    name: str
    device_sn: str
    device_type: DeviceType = DeviceType.REAL
    region: str = "cn"
    firmware_version: str | None = None
    project_id: int | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    status: DeviceStatus | None = None
    firmware_version: str | None = None
    project_id: int | None = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    device_sn: str
    device_type: DeviceType
    status: DeviceStatus
    region: str
    firmware_version: str | None
    ip_address: str | None
    temperature: float | None
    project_id: int | None
    occupied_by: int | None
    last_heartbeat: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceControlRequest(BaseModel):
    action: str  # open_door, close_door, restart, upgrade_firmware, set_light
    payload: dict | None = None


class VirtualDeviceCreate(BaseModel):
    count: int = 1
    device_type: DeviceType = DeviceType.VIRTUAL_L2
    region: str = "cn"
    project_id: int | None = None
