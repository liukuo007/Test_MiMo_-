from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DevicePoolBase(BaseModel):
    name: str
    pool_type: str = "manual"
    auto_assign: bool = False
    max_devices: int = 0
    description: Optional[str] = None
    config: Optional[dict] = None


class DevicePoolCreate(DevicePoolBase):
    pass


class DevicePoolUpdate(BaseModel):
    name: Optional[str] = None
    pool_type: Optional[str] = None
    auto_assign: Optional[bool] = None
    max_devices: Optional[int] = None
    description: Optional[str] = None
    config: Optional[dict] = None


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
    device_name: Optional[str] = None
    device_sn: Optional[str] = None
    device_status: Optional[str] = None
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
    factors: Optional[dict] = None
    computed_at: datetime


class AssignDevicesRequest(BaseModel):
    device_ids: list[int]


class ScheduleRequest(BaseModel):
    strategy: str = "least_busy"  # least_busy / most_stable / least_recently_checked
    count: int = 1
