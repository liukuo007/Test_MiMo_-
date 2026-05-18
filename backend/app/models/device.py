from __future__ import annotations
from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import String, Integer, Float, Enum, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeviceStatus(str, enum.Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    FAULT = "fault"


class DeviceType(str, enum.Enum):
    REAL = "real"
    VIRTUAL_L1 = "virtual_l1"
    VIRTUAL_L2 = "virtual_l2"
    VIRTUAL_L3 = "virtual_l3"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    device_sn: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    device_type: Mapped[DeviceType] = mapped_column(Enum(DeviceType))
    status: Mapped[DeviceStatus] = mapped_column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE)
    region: Mapped[str] = mapped_column(String(32), default="cn")
    firmware_version: Mapped[Optional[str]] = mapped_column(String(32))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    occupied_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="devices")
    events: Mapped[list["DeviceEvent"]] = relationship(back_populates="device")
