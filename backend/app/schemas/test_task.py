from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.test_task import TaskStatus, TriggerType


class TestTaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    environment: str
    branch: Optional[str] = None
    dag_config: Optional[dict] = None
    config: Optional[dict] = None
    project_id: int


class TestTaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TaskStatus] = None
    dag_config: Optional[dict] = None
    config: Optional[dict] = None


class TestTaskStepResponse(BaseModel):
    id: int
    name: str
    step_type: str
    status: TaskStatus
    order: int
    config: Optional[dict]
    result: Optional[dict]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


class TestTaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: TaskStatus
    trigger_type: TriggerType
    environment: str
    branch: Optional[str]
    project_id: int
    created_by: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TestTaskDetailResponse(TestTaskResponse):
    steps: list[TestTaskStepResponse] = []
