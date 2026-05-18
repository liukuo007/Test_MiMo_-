from __future__ import annotations

import asyncio
from datetime import datetime

from celery import shared_task
import structlog

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=1)
def generate_report_task(self, project_id: int):
    """异步生成质量报告"""
    logger.info("report_generation_started", project_id=project_id)

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_build_report(project_id))
        loop.close()
        logger.info("report_generation_completed", project_id=project_id)
        return result
    except Exception as exc:
        logger.error("report_generation_failed", project_id=project_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)


async def _build_report(project_id: int) -> dict:
    from sqlalchemy import select, func
    from app.database import async_session
    from app.models.test_result import TestResult
    from app.models.test_task import TestTask, TaskStatus
    from app.models.device import Device, DeviceStatus
    from app.models.ai_model import AIEvaluation
    from app.models.quality_report import QualityReport

    async with async_session() as db:
        # 测试指标
        total_results = (await db.execute(
            select(func.count(TestResult.id)).where(TestResult.project_id == project_id)
        )).scalar() or 0
        passed_results = (await db.execute(
            select(func.count(TestResult.id)).where(TestResult.project_id == project_id, TestResult.status == "passed")
        )).scalar() or 0
        failed_results = (await db.execute(
            select(func.count(TestResult.id)).where(TestResult.project_id == project_id, TestResult.status == "failed")
        )).scalar() or 0
        pass_rate = round(passed_results / total_results * 100, 2) if total_results > 0 else 0

        # 任务指标
        completed_tasks = (await db.execute(
            select(func.count(TestTask.id)).where(
                TestTask.project_id == project_id,
                TestTask.status.in_([TaskStatus.PASSED, TaskStatus.FAILED]),
            )
        )).scalar() or 0
        passed_tasks = (await db.execute(
            select(func.count(TestTask.id)).where(
                TestTask.project_id == project_id, TestTask.status == TaskStatus.PASSED
            )
        )).scalar() or 0
        release_rate = round(passed_tasks / completed_tasks * 100, 1) if completed_tasks > 0 else 0

        # AI 指标
        ai_eval = (await db.execute(
            select(func.avg(AIEvaluation.accuracy)).where(AIEvaluation.accuracy.isnot(None))
        )).scalar()
        ai_acc = round((ai_eval or 0) * 100, 1)

        # 设备指标
        total_devices = (await db.execute(select(func.count(Device.id)))).scalar() or 0
        online_devices = (await db.execute(
            select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
        )).scalar() or 0
        device_online = round(online_devices / total_devices * 100, 1) if total_devices > 0 else 0

        defect_rate = round(failed_results / total_results * 100, 1) if total_results > 0 else 0
        overall_score = round(
            pass_rate * 0.3 + ai_acc * 0.25 + release_rate * 0.2 + device_online * 0.15 + max(0, 100 - defect_rate * 5) * 0.1,
            1,
        )

        now = datetime.now()
        week_num = now.isocalendar()[1]

        report = QualityReport(
            name=f"{now.year}-W{week_num:02d} 周质量报告",
            report_type="weekly",
            overall_score=overall_score,
            pass_rate=pass_rate,
            defect_escape_rate=defect_rate,
            release_success_rate=release_rate,
            device_online_rate=device_online,
            ai_accuracy=ai_acc,
            dimensions=[
                {"name": "自动化覆盖率", "score": round(pass_rate * 0.9, 1), "trend": "up", "detail": f"通过率 {pass_rate}%"},
                {"name": "AI 识别准确率", "score": ai_acc, "trend": "up", "detail": f"准确率 {ai_acc}%"},
                {"name": "缺陷逃逸率", "score": round(max(0, 100 - defect_rate * 5), 1), "trend": "down" if defect_rate > 2 else "up", "detail": f"逃逸率 {defect_rate}%"},
                {"name": "发布成功率", "score": release_rate, "trend": "stable", "detail": f"成功率 {release_rate}%"},
                {"name": "设备稳定性", "score": device_online, "trend": "stable", "detail": f"在线率 {device_online}%"},
            ],
            summary={
                "overall_score": overall_score,
                "pass_rate": pass_rate,
                "ai_accuracy": ai_acc,
                "defect_escape_rate": defect_rate,
                "release_success_rate": release_rate,
                "device_online_rate": device_online,
            },
        )
        db.add(report)
        await db.commit()

    return {
        "task_id": project_id,
        "status": "completed",
        "generated_at": now.isoformat(),
        "overall_score": overall_score,
    }
