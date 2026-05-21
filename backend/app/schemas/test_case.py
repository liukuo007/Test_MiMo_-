from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.test_case import Priority, TestType


class TestCaseCreate(BaseModel):
    name: str
    description: str | None = None
    test_type: TestType
    priority: Priority = Priority.P1
    module: str | None = None
    steps: dict | None = None
    expected_result: str | None = None
    tags: list[str] | None = None
    project_id: int


class TestCaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: Priority | None = None
    module: str | None = None
    steps: dict | None = None
    expected_result: str | None = None
    tags: list[str] | None = None


class TestCaseResponse(BaseModel):
    id: int
    name: str
    description: str | None
    test_type: TestType
    priority: Priority
    module: str | None
    steps: dict | None
    expected_result: str | None
    tags: list | None
    project_id: int
    created_by: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
