from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from celery import shared_task
import structlog

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=3)
def execute_test_task(self, task_id: int, dag_config: dict):
    """异步执行测试任务 - 通过 DAG 编排器调度"""
    logger.info("task_started", task_id=task_id)

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_run_and_finalize(task_id, dag_config))
        loop.close()
        logger.info("task_completed", task_id=task_id, status=result.get("status"))
        return {"task_id": task_id, **result}
    except Exception as exc:
        logger.error("task_failed", task_id=task_id, error=str(exc))
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_mark_failed(task_id))
            loop.close()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)


async def _run_and_finalize(task_id: int, dag_config: dict) -> dict:
    """执行 DAG 并完成后续处理（状态更新、缺陷创建、CI 回调）"""
    from app.orchestrator.dag import DAG
    from app.orchestrator.scheduler import TaskScheduler
    from app.orchestrator.executor import step_executor
    from app.database import async_session
    from app.models.test_task import TestTask, TaskStatus

    dag = DAG.from_config(dag_config)
    scheduler = TaskScheduler(step_executor)

    start_time = datetime.now()
    await scheduler.execute_dag(dag)
    end_time = datetime.now()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    if dag.has_failed():
        status = "failed"
    elif dag.is_complete():
        status = "passed"
    else:
        status = "timeout"

    # 更新任务状态
    async with async_session() as db:
        res = await db.execute(select(TestTask).where(TestTask.id == task_id))
        task = res.scalar_one_or_none()
        if task:
            final_status = TaskStatus.PASSED if status == "passed" else TaskStatus.FAILED
            task.status = final_status
            task.finished_at = end_time
            await db.commit()

            # 自动创建缺陷
            if final_status == TaskStatus.FAILED:
                await _auto_create_defects(db, task)

            # CI 回调
            config = task.config or {}
            if config.get("callback_url"):
                await _notify_ci_callback(config["callback_url"], task, config.get("commit_sha"), db)

    return {"status": status, "duration_ms": duration_ms}


async def _mark_failed(task_id: int):
    """异常时标记任务失败"""
    from app.database import async_session
    from app.models.test_task import TestTask, TaskStatus

    async with async_session() as db:
        res = await db.execute(select(TestTask).where(TestTask.id == task_id))
        task = res.scalar_one_or_none()
        if task:
            task.status = TaskStatus.FAILED
            task.finished_at = datetime.now()
            await db.commit()

            config = task.config or {}
            if config.get("callback_url"):
                await _notify_ci_callback(config["callback_url"], task, config.get("commit_sha"), db)


async def _auto_create_defects(db, task):
    """任务失败时自动创建缺陷"""
    from sqlalchemy import select
    from app.models.defect import Defect, DefectPriority, DefectSource
    from app.models.test_result import TestResult

    results = await db.execute(
        select(TestResult).where(TestResult.task_id == task.id, TestResult.status == "failed")
    )
    failed_results = results.scalars().all()

    for tr in failed_results:
        defect = Defect(
            title=f"Auto defect: Task #{task.id} - {tr.error_message or 'Test failed'}",
            description=f"Automatically created from failed test result #{tr.id}.\n"
                       f"Task: {task.name}\n"
                       f"Device: {tr.device_sn or 'N/A'}\n"
                       f"Error: {tr.error_message or 'No error message'}",
            status="new",
            priority=DefectPriority.P1,
            source=DefectSource.AUTO,
            device_sn=tr.device_sn,
            test_case_id=tr.test_case_id,
            test_result_id=tr.id,
            screenshot_url=tr.screenshot_url,
        )
        db.add(defect)

    await db.flush()

    # MeterSphere 同步所有新创建的缺陷
    from app.config import get_settings
    if get_settings().ms_sync_enabled:
        try:
            from integrations.metersphere.sync_to_ms import metersphere_sync
            for d in [obj for obj in db.new if isinstance(obj, Defect)]:
                await metersphere_sync.push_defect(d)
        except Exception:
            pass

    await db.commit()


async def _notify_ci_callback(callback_url: str, task, commit_sha: Optional[str], db):
    """任务完成后回调 CI 系统"""
    import httpx
    from sqlalchemy import select
    from app.models.test_result import TestResult

    results = await db.execute(
        select(TestResult).where(TestResult.task_id == task.id)
    )
    all_results = results.scalars().all()
    total = len(all_results)
    passed = sum(1 for r in all_results if r.status == "passed")
    failed = sum(1 for r in all_results if r.status == "failed")
    pass_rate = round(passed / total * 100, 2) if total > 0 else 0

    payload = {
        "task_id": task.id,
        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
        "pass_rate": pass_rate,
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "duration_ms": int((task.finished_at - task.started_at).total_seconds() * 1000)
            if task.finished_at and task.started_at else 0,
        "commit_sha": commit_sha,
        "branch": task.branch,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(callback_url, json=payload)
    except Exception:
        pass
