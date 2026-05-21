from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.defect import DefectPriority, DefectSource, DefectStatus


class DefectCreate(BaseModel):
    title: str
    description: str | None = None
    priority: DefectPriority = DefectPriority.P2
    test_case_id: int | None = None
    test_result_id: int | None = None
    device_sn: str | None = None
    assigned_to: int | None = None
    screenshot_url: str | None = None
    tags: dict | None = None


class DefectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: DefectPriority | None = None
    assigned_to: int | None = None
    screenshot_url: str | None = None
    tags: dict | None = None


class DefectStatusTransition(BaseModel):
    status: DefectStatus


class DefectAssign(BaseModel):
    assigned_to: int


class DefectResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: DefectStatus
    priority: DefectPriority
    source: DefectSource
    device_sn: str | None
    test_case_id: int | None
    test_result_id: int | None
    assigned_to: int | None
    created_by: int | None
    screenshot_url: str | None
    tags: dict | None
    resolved_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DefectDetailResponse(DefectResponse):
    assignee_name: str | None = None
    creator_name: str | None = None
