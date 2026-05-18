from __future__ import annotations
from typing import Optional

from datetime import datetime

from pydantic import BaseModel

from app.models.test_case import TestType, Priority


class TestCaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    test_type: TestType
    priority: Priority = Priority.P1
    module: Optional[str] = None
    steps: Optional[dict] = None
    expected_result: Optional[str] = None
    tags: Optional[list[str]] = None
    project_id: int


class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    module: Optional[str] = None
    steps: Optional[dict] = None
    expected_result: Optional[str] = None
    tags: Optional[list[str]] = None


class TestCaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    test_type: TestType
    priority: Priority
    module: Optional[str]
    steps: Optional[dict]
    expected_result: Optional[str]
    tags: Optional[list]
    project_id: int
    created_by: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
