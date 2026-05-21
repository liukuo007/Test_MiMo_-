from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.defect import DefectPriority, DefectSource, DefectStatus


class DefectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: DefectPriority = DefectPriority.P2
    test_case_id: Optional[int] = None
    test_result_id: Optional[int] = None
    device_sn: Optional[str] = None
    assigned_to: Optional[int] = None
    screenshot_url: Optional[str] = None
    tags: Optional[dict] = None


class DefectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[DefectPriority] = None
    assigned_to: Optional[int] = None
    screenshot_url: Optional[str] = None
    tags: Optional[dict] = None


class DefectStatusTransition(BaseModel):
    status: DefectStatus


class DefectAssign(BaseModel):
    assigned_to: int


class DefectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: DefectStatus
    priority: DefectPriority
    source: DefectSource
    device_sn: Optional[str]
    test_case_id: Optional[int]
    test_result_id: Optional[int]
    assigned_to: Optional[int]
    created_by: Optional[int]
    screenshot_url: Optional[str]
    tags: Optional[dict]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DefectDetailResponse(DefectResponse):
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None
