from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DatasetType(str, enum.Enum):
    SKU_IMAGES = "sku_images"
    FACE_IMAGES = "face_images"
    GESTURE_VIDEOS = "gesture_videos"
    MIXED = "mixed"


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    type: Mapped[DatasetType] = mapped_column(Enum(DatasetType), default=DatasetType.SKU_IMAGES)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    class_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    annotation_format: Mapped[str] = mapped_column(String(32), default="coco")
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
