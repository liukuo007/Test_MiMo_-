from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.test_result import TestResult
from app.schemas.test_result import TestResultResponse

router = APIRouter()


class TestResultCreate(BaseModel):
    task_id: int
    test_case_id: int | None = None
    status: str
    duration_ms: int | None = None
    error_message: str | None = None
    trace_id: str | None = None
    device_sn: str | None = None
    screenshot_url: str | None = None
    video_url: str | None = None
    ai_result: dict | None = None


@router.post("", response_model=TestResultResponse)
async def create_test_result(req: TestResultCreate, db: AsyncSession = Depends(get_db)):
    result = TestResult(**req.model_dump())
    db.add(result)
    await db.flush()
    await db.refresh(result)
    return result


@router.get("", response_model=list[TestResultResponse])
async def list_test_results(
    db: AsyncSession = Depends(get_db),
    task_id: int | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(TestResult)
    if task_id:
        query = query.where(TestResult.task_id == task_id)
    if status:
        query = query.where(TestResult.status == status)
    query = query.offset(skip).limit(limit).order_by(TestResult.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{result_id}", response_model=TestResultResponse)
async def get_test_result(result_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestResult).where(TestResult.id == result_id))
    test_result = result.scalar_one_or_none()
    if not test_result:
        raise NotFoundError("TestResult", result_id)
    return test_result
