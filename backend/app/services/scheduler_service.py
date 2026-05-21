from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional

from croniter import croniter

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Scheduler service started")

    async def stop(self):
        """停止调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler service stopped")

    async def _run_loop(self):
        """主循环：每分钟检查一次到期的定时任务"""
        while self._running:
            try:
                await self._check_and_execute()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)

    async def _check_and_execute(self):
        """检查并执行到期的定时任务"""
        from sqlalchemy import select

        from app.database import async_session
        from app.models.schedule import Schedule

        async with async_session() as db:
            now = datetime.now()
            result = await db.execute(
                select(Schedule).where(
                    Schedule.is_active == True,
                    Schedule.next_run_at <= now,
                )
            )
            schedules = result.scalars().all()

            for schedule in schedules:
                try:
                    await self._execute_schedule(db, schedule)
                except Exception as e:
                    logger.error(f"Failed to execute schedule {schedule.id}: {e}")

    async def _execute_schedule(self, db, schedule):
        """执行单个定时任务"""
        from sqlalchemy import select

        from app.celery_app import celery_app
        from app.models.test_task import TaskStatus, TestTask, TriggerType

        task_result = await db.execute(
            select(TestTask).where(TestTask.id == schedule.task_id)
        )
        template_task = task_result.scalar_one_or_none()
        if not template_task:
            schedule.is_active = False
            await db.commit()
            return

        new_task = TestTask(
            name=f"{template_task.name} (cron #{schedule.id})",
            description=f"Scheduled by cron: {schedule.cron_expression}",
            status=TaskStatus.RUNNING,
            trigger_type=TriggerType.CRON,
            environment=template_task.environment,
            branch=template_task.branch,
            dag_config=template_task.dag_config,
            config=template_task.config,
            project_id=template_task.project_id,
            created_by=schedule.created_by or 1,
            started_at=datetime.now(),
        )
        db.add(new_task)
        await db.flush()
        await db.refresh(new_task)

        schedule.last_run_at = datetime.now()
        schedule.next_run_at = self._calculate_next_run(schedule.cron_expression)
        await db.commit()

        dag_config = new_task.dag_config or {"steps": []}
        celery_app.send_task(
            "app.tasks.test_execution.execute_test_task",
            args=[new_task.id, dag_config],
            queue="test",
        )

        logger.info(f"Schedule {schedule.id} triggered task {new_task.id}")

    @staticmethod
    def _calculate_next_run(cron_expression: str) -> datetime:
        try:
            return croniter(cron_expression, datetime.now()).get_next(datetime)
        except Exception:
            from datetime import timedelta
            return datetime.now() + timedelta(hours=1)


scheduler_service = SchedulerService()
