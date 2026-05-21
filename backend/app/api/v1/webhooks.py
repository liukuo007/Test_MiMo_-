from __future__ import annotations

from typing import Optional

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.test_task import TestTask, TaskStatus, TriggerType
from app.models.test_result import TestResult
from app.schemas.webhook import WebhookTriggerRequest, PipelineStatus
from app.dependencies import CurrentUser
from app.core.exceptions import NotFoundError
from app.celery_app import celery_app
from app.config import get_settings

router = APIRouter()


@router.post("/trigger")
async def webhook_trigger(
    req: WebhookTriggerRequest,
    db: AsyncSession = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(default=None),
):
    """外部 CI 系统通过 webhook 触发测试执行"""
    settings = get_settings()
    if settings.webhook_secret:
        if x_webhook_secret != settings.webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook secret",
            )

    task = TestTask(
        name=f"Webhook trigger - {req.branch}",
        description=f"Triggered by webhook. Commit: {req.commit_sha or 'N/A'}",
        status=TaskStatus.PENDING,
        trigger_type=TriggerType.WEBHOOK,
        environment=req.environment,
        branch=req.branch,
        project_id=req.project_id,
        created_by=1,  # system user (webhook fallback)
        config={"commit_sha": req.commit_sha, "callback_url": req.callback_url},
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    # 异步执行任务
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.now()
    await db.flush()

    dag_config = task.dag_config or {"steps": []}
    celery_app.send_task(
        "app.tasks.test_execution.execute_test_task",
        args=[task.id, dag_config],
        queue="test",
    )

    return {
        "message": "Test execution triggered",
        "task_id": task.id,
        "status": "running",
        "branch": req.branch,
    }


@router.get("/pipelines", response_model=list[PipelineStatus])
async def list_pipelines(
    db: AsyncSession = Depends(get_db),
    project_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
):
    query = select(TestTask).where(TestTask.trigger_type == TriggerType.WEBHOOK)
    if project_id:
        query = query.where(TestTask.project_id == project_id)
    query = query.order_by(TestTask.id.desc()).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    pipelines = []
    for task in tasks:
        # 统计结果
        total_result = await db.execute(
            select(TestResult).where(TestResult.task_id == task.id)
        )
        results = total_result.scalars().all()
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        pass_rate = round(passed / total * 100, 2) if total > 0 else 0

        config = task.config or {}
        pipelines.append(PipelineStatus(
            task_id=task.id,
            status=task.status,
            branch=task.branch,
            commit_sha=config.get("commit_sha"),
            pass_rate=pass_rate,
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            triggered_at=task.created_at,
            finished_at=task.finished_at,
        ))

    return pipelines
