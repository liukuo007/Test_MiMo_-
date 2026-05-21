from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DevicePoolBase(BaseModel):
    name: str
    pool_type: str = "manual"
    auto_assign: bool = False
    max_devices: int = 0
    description: str | None = None
    config: dict | None = None


class DevicePoolCreate(DevicePoolBase):
    pass


class DevicePoolUpdate(BaseModel):
    name: str | None = None
    pool_type: str | None = None
    auto_assign: bool | None = None
    max_devices: int | None = None
    description: str | None = None
    config: dict | None = None


class DevicePoolResponse(DevicePoolBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_count: int = 0
    created_at: datetime
    updated_at: datetime


class DevicePoolMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    pool_id: int
    device_id: int
    device_name: str | None = None
    device_sn: str | None = None
    device_status: str | None = None
    added_at: datetime


class DeviceTagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int
    tag_key: str
    tag_value: str
    created_at: datetime


class DeviceTagCreate(BaseModel):
    tag_key: str
    tag_value: str


class DeviceHealthScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: int
    score: float
    factors: dict | None = None
    computed_at: datetime


class AssignDevicesRequest(BaseModel):
    device_ids: list[int]


class ScheduleRequest(BaseModel):
    strategy: str = "least_busy"  # least_busy / most_stable / least_recently_checked
    count: int = 1
