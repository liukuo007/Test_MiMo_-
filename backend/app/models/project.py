from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.test_case import TestCase
    from app.models.test_task import TestTask


class Environment(str, enum.Enum):
    DEV = "dev"
    STAGING = "staging"
    PRE_PROD = "pre_prod"
    PROD = "prod"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    environment: Mapped[Environment] = mapped_column(Enum(Environment), default=Environment.DEV)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    devices: Mapped[list[Device]] = relationship(back_populates="project")
    test_cases: Mapped[list[TestCase]] = relationship(back_populates="project")
    test_tasks: Mapped[list[TestTask]] = relationship(back_populates="project")
