from __future__ import annotations
from typing import Optional

from datetime import datetime

from pydantic import BaseModel

from app.models.dataset import DatasetType


class DatasetCreate(BaseModel):
    name: str
    type: DatasetType = DatasetType.SKU_IMAGES
    description: Optional[str] = None
    sample_count: int = 0
    class_count: int = 0
    size_bytes: int = 0
    annotation_format: str = "coco"
    project_id: Optional[int] = None


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[DatasetType] = None
    description: Optional[str] = None
    sample_count: Optional[int] = None
    class_count: Optional[int] = None
    size_bytes: Optional[int] = None
    annotation_format: Optional[str] = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    type: DatasetType
    description: Optional[str]
    sample_count: int
    class_count: int
    size_bytes: int
    annotation_format: str
    project_id: Optional[int]
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
