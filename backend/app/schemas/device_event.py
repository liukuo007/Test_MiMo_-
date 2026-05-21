from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.device_event import DeviceEventType


class DeviceEventResponse(BaseModel):
    id: int
    device_id: int
    event_type: DeviceEventType
    message: str
    details: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
