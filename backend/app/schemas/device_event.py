from __future__ import annotations
from typing import Optional

from datetime import datetime

from pydantic import BaseModel

from app.models.device_event import DeviceEventType


class DeviceEventResponse(BaseModel):
    id: int
    device_id: int
    event_type: DeviceEventType
    message: str
    details: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True
