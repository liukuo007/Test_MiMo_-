from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.test_task import TaskStatus


class WebhookTriggerRequest(BaseModel):
    project_id: int
    branch: str = "main"
    environment: str = "staging"
    commit_sha: str | None = None
    callback_url: str | None = None


class CICallbackConfig(BaseModel):
    task_id: int
    callback_url: str


class PipelineStatus(BaseModel):
    task_id: int
    status: TaskStatus
    branch: str | None
    commit_sha: str | None
    pass_rate: float | None
    total_cases: int | None
    passed_cases: int | None
    failed_cases: int | None
    triggered_at: datetime
    finished_at: datetime | None

    class Config:
        from_attributes = True
