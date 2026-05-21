from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.test_task import TaskStatus, TriggerType


class TestTaskCreate(BaseModel):
    name: str
    description: str | None = None
    environment: str
    branch: str | None = None
    dag_config: dict | None = None
    config: dict | None = None
    project_id: int


class TestTaskUpdate(BaseModel):
    name: str | None = None
    status: TaskStatus | None = None
    dag_config: dict | None = None
    config: dict | None = None


class TestTaskStepResponse(BaseModel):
    id: int
    name: str
    step_type: str
    status: TaskStatus
    order: int
    config: dict | None
    result: dict | None
    started_at: datetime | None
    finished_at: datetime | None

    class Config:
        from_attributes = True


class TestTaskResponse(BaseModel):
    id: int
    name: str
    description: str | None
    status: TaskStatus
    trigger_type: TriggerType
    environment: str
    branch: str | None
    project_id: int
    created_by: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class TestTaskDetailResponse(TestTaskResponse):
    steps: list[TestTaskStepResponse] = []
