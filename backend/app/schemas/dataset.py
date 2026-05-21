from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.dataset import DatasetType


class DatasetCreate(BaseModel):
    name: str
    type: DatasetType = DatasetType.SKU_IMAGES
    description: str | None = None
    sample_count: int = 0
    class_count: int = 0
    size_bytes: int = 0
    annotation_format: str = "coco"
    project_id: int | None = None


class DatasetUpdate(BaseModel):
    name: str | None = None
    type: DatasetType | None = None
    description: str | None = None
    sample_count: int | None = None
    class_count: int | None = None
    size_bytes: int | None = None
    annotation_format: str | None = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    type: DatasetType
    description: str | None
    sample_count: int
    class_count: int
    size_bytes: int
    annotation_format: str
    project_id: int | None
    created_by: int | None
    created_at: datetime

    class Config:
        from_attributes = True
