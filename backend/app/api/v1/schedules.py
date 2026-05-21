from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.schedule import Schedule
from app.models.test_task import TaskStatus, TestTask, TriggerType
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate

router = APIRouter()


@router.get("")
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(Schedule)
    count_query = select(func.count(Schedule.id))
    if is_active is not None:
        query = query.where(Schedule.is_active == is_active)
        count_query = count_query.where(Schedule.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit).order_by(Schedule.id.desc())
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("", response_model=ScheduleResponse)
async def create_schedule(req: ScheduleCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    # 验证任务存在
    task_result = await db.execute(select(TestTask).where(TestTask.id == req.task_id))
    if not task_result.scalar_one_or_none():
        raise NotFoundError("TestTask", req.task_id)

    # 计算下次执行时间
    next_run = _calculate_next_run(req.cron_expression)

    schedule = Schedule(
        name=req.name,
        task_id=req.task_id,
        cron_expression=req.cron_expression,
        is_active=True,
        next_run_at=next_run,
        created_by=int(current_user["sub"]),
    )
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    return schedule


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise NotFoundError("Schedule", schedule_id)
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: int, req: ScheduleUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise NotFoundError("Schedule", schedule_id)

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)

    # 如果更新了 cron 表达式，重新计算下次执行时间
    if req.cron_expression:
        schedule.next_run_at = _calculate_next_run(req.cron_expression)

    await db.flush()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise NotFoundError("Schedule", schedule_id)

    await db.delete(schedule)
    await db.flush()
    return {"message": f"Schedule '{schedule.name}' deleted"}


@router.post("/{schedule_id}/trigger")
async def trigger_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """立即触发一次定时任务"""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise NotFoundError("Schedule", schedule_id)

    # 获取关联的任务
    task_result = await db.execute(select(TestTask).where(TestTask.id == schedule.task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise NotFoundError("TestTask", schedule.task_id)

    # 创建一个新任务副本执行
    new_task = TestTask(
        name=f"{task.name} (scheduled)",
        description=f"Scheduled execution from schedule #{schedule.id}",
        status=TaskStatus.RUNNING,
        trigger_type=TriggerType.CRON,
        environment=task.environment,
        branch=task.branch,
        dag_config=task.dag_config,
        config=task.config,
        project_id=task.project_id,
        created_by=schedule.created_by or 1,
        started_at=datetime.now(),
    )
    db.add(new_task)
    await db.flush()
    await db.refresh(new_task)

    # 更新调度记录
    schedule.last_run_at = datetime.now()
    schedule.next_run_at = _calculate_next_run(schedule.cron_expression)
    await db.flush()

    # 通过 Celery 异步执行
    dag_config = new_task.dag_config or {"steps": []}
    celery_app.send_task(
        "app.tasks.test_execution.execute_test_task",
        args=[new_task.id, dag_config],
        queue="test",
    )

    return {
        "message": f"Schedule '{schedule.name}' triggered",
        "task_id": new_task.id,
        "status": "running",
    }


def _calculate_next_run(cron_expression: str) -> datetime:
    """计算下次执行时间"""
    try:
        from croniter import croniter
        return croniter(cron_expression, datetime.now()).get_next(datetime)
    except Exception:
        # 如果 croniter 不可用或表达式无效，默认 1 小时后
        from datetime import timedelta
        return datetime.now() + timedelta(hours=1)
