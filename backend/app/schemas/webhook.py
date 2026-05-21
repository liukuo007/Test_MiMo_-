from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.test_task import TaskStatus


class WebhookTriggerRequest(BaseModel):
    project_id: int
    branch: str = "main"
    environment: str = "staging"
    commit_sha: Optional[str] = None
    callback_url: Optional[str] = None


class CICallbackConfig(BaseModel):
    task_id: int
    callback_url: str


class PipelineStatus(BaseModel):
    task_id: int
    status: TaskStatus
    branch: Optional[str]
    commit_sha: Optional[str]
    pass_rate: Optional[float]
    total_cases: Optional[int]
    passed_cases: Optional[int]
    failed_cases: Optional[int]
    triggered_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True
