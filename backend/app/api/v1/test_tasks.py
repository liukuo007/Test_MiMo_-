from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.test_task import TaskStatus, TestTask
from app.schemas.test_task import TestTaskCreate, TestTaskDetailResponse, TestTaskResponse, TestTaskUpdate

router = APIRouter()


@router.get("")
async def list_test_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
    project_id: int | None = None,
    status: TaskStatus | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(TestTask)
    count_query = select(func.count(TestTask.id))
    if project_id:
        query = query.where(TestTask.project_id == project_id)
        count_query = count_query.where(TestTask.project_id == project_id)
    if status:
        query = query.where(TestTask.status == status)
        count_query = count_query.where(TestTask.status == status)
    if search:
        search_filter = TestTask.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit).order_by(TestTask.id.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=TestTaskResponse)
async def create_test_task(req: TestTaskCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    task = TestTask(
        **req.model_dump(),
        created_by=int(current_user["sub"]),
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TestTaskDetailResponse)
async def get_test_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id).options(selectinload(TestTask.steps))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("TestTask", task_id)
    return task


@router.put("/{task_id}", response_model=TestTaskResponse)
async def update_test_task(task_id: int, req: TestTaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestTask).where(TestTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("TestTask", task_id)

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    await db.flush()
    await db.refresh(task)
    return task


@router.post("/{task_id}/execute")
async def execute_test_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestTask).where(TestTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("TestTask", task_id)

    task.status = TaskStatus.RUNNING
    task.started_at = datetime.now()
    await db.flush()

    dag_config = task.dag_config or {"steps": []}
    celery_app.send_task(
        "app.tasks.test_execution.execute_test_task",
        args=[task_id, dag_config],
        queue="test",
    )

    return {"message": f"Task '{task.name}' execution started", "task_id": task_id, "status": "running"}


@router.post("/{task_id}/cancel")
async def cancel_test_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestTask).where(TestTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("TestTask", task_id)

    task.status = TaskStatus.CANCELLED
    await db.flush()
    return {"message": f"Task '{task.name}' cancelled", "task_id": task_id}


@router.delete("/{task_id}")
async def delete_test_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestTask).where(TestTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundError("TestTask", task_id)

    await db.delete(task)
    await db.flush()
    return {"message": f"TestTask {task_id} deleted"}
