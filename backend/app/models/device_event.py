from __future__ import annotations

import enum
from datetime import datetime

from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.device import Device


class DeviceEventType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    CONTROL = "control"
    FAULT = "fault"
    DOOR_OPEN = "door_open"
    DOOR_CLOSE = "door_close"
    ITEM_DETECTED = "item_detected"
    PAYMENT = "payment"
    AI_RECOGNITION = "ai_recognition"


class DeviceEvent(Base):
    __tablename__ = "device_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    event_type: Mapped[DeviceEventType] = mapped_column(Enum(DeviceEventType))
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    device: Mapped[Device] = relationship(back_populates="events")
