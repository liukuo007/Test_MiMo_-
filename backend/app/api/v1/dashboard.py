from __future__ import annotations

from typing import Optional

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device, DeviceStatus
from app.models.test_task import TestTask, TaskStatus
from app.models.test_result import TestResult

router = APIRouter()


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    # 设备统计
    total_devices = await db.execute(select(func.count(Device.id)))
    online_devices = await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
    )
    occupied_devices = await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatus.OCCUPIED)
    )

    # 任务统计
    total_tasks = await db.execute(select(func.count(TestTask.id)))
    running_tasks = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.status == TaskStatus.RUNNING)
    )
    passed_tasks = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.status == TaskStatus.PASSED)
    )
    failed_tasks = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.status == TaskStatus.FAILED)
    )

    # 测试结果统计
    total_results = await db.execute(select(func.count(TestResult.id)))
    passed_results = await db.execute(
        select(func.count(TestResult.id)).where(TestResult.status == "passed")
    )

    total = total_results.scalar() or 0
    passed = passed_results.scalar() or 0
    pass_rate = round(passed / total * 100, 2) if total > 0 else 0

    return {
        "devices": {
            "total": total_devices.scalar() or 0,
            "online": online_devices.scalar() or 0,
            "occupied": occupied_devices.scalar() or 0,
        },
        "tasks": {
            "total": total_tasks.scalar() or 0,
            "running": running_tasks.scalar() or 0,
            "passed": passed_tasks.scalar() or 0,
            "failed": failed_tasks.scalar() or 0,
        },
        "results": {
            "total": total,
            "pass_rate": pass_rate,
        },
    }


@router.get("/quality-score")
async def get_quality_score(db: AsyncSession = Depends(get_db)):
    from app.models.test_case import TestCase, TestType
    from app.models.ai_model import AIEvaluation

    # 1. 自动化覆盖率: 有自动化类型的用例占总用例比例
    total_cases = await db.execute(select(func.count(TestCase.id)))
    auto_types = [TestType.IOT, TestType.AI, TestType.WEB, TestType.APP, TestType.E2E]
    auto_cases = await db.execute(
        select(func.count(TestCase.id)).where(TestCase.test_type.in_(auto_types))
    )
    total_c = total_cases.scalar() or 0
    auto_c = auto_cases.scalar() or 0
    automation_coverage = round(auto_c / total_c * 100, 1) if total_c > 0 else 0

    # 2. AI 识别准确率: 最近评测记录的平均 accuracy
    ai_eval_result = await db.execute(
        select(func.avg(AIEvaluation.accuracy)).where(AIEvaluation.accuracy.isnot(None))
    )
    ai_accuracy = round((ai_eval_result.scalar() or 0) * 100, 1)

    # 3. 缺陷逃逸率: failed result 占总 result 的比例
    total_results = await db.execute(select(func.count(TestResult.id)))
    failed_results = await db.execute(
        select(func.count(TestResult.id)).where(TestResult.status == "failed")
    )
    total_r = total_results.scalar() or 0
    failed_r = failed_results.scalar() or 0
    defect_escape_rate = round(failed_r / total_r * 100, 1) if total_r > 0 else 0

    # 4. 发布成功率: PASSED 任务占已完成任务的比例
    completed_tasks = await db.execute(
        select(func.count(TestTask.id)).where(
            TestTask.status.in_([TaskStatus.PASSED, TaskStatus.FAILED])
        )
    )
    passed_tasks = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.status == TaskStatus.PASSED)
    )
    completed = completed_tasks.scalar() or 0
    passed = passed_tasks.scalar() or 0
    release_success_rate = round(passed / completed * 100, 1) if completed > 0 else 0

    # 5. 设备在线率
    total_devices = await db.execute(select(func.count(Device.id)))
    online_devices = await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
    )
    td = total_devices.scalar() or 0
    od = online_devices.scalar() or 0
    device_online_rate = round(od / td * 100, 1) if td > 0 else 0

    # 综合质量分: 加权平均
    weights = {
        "automation_coverage": 0.2,
        "ai_accuracy": 0.25,
        "defect_escape_rate": 0.2,
        "release_success_rate": 0.2,
        "device_online_rate": 0.15,
    }
    defect_score = max(0, 100 - defect_escape_rate * 5)
    overall = round(
        automation_coverage * weights["automation_coverage"]
        + ai_accuracy * weights["ai_accuracy"]
        + defect_score * weights["defect_escape_rate"]
        + release_success_rate * weights["release_success_rate"]
        + device_online_rate * weights["device_online_rate"],
        1,
    )

    return {
        "overall_score": overall,
        "dimensions": {
            "automation_coverage": automation_coverage,
            "ai_accuracy": ai_accuracy,
            "defect_escape_rate": defect_escape_rate,
            "release_success_rate": release_success_rate,
            "device_online_rate": device_online_rate,
        },
    }


@router.get("/trend")
async def get_trend(days: int = Query(7, ge=1, le=90), db: AsyncSession = Depends(get_db)):
    """获取最近 N 天的测试趋势数据"""
    today = datetime.now().date()
    dates = []
    passed_data = []
    failed_data = []

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        dates.append(day.strftime("%m-%d"))

        day_passed = await db.execute(
            select(func.count(TestResult.id)).where(
                TestResult.status == "passed",
                cast(TestResult.created_at, Date) == day,
            )
        )
        day_failed = await db.execute(
            select(func.count(TestResult.id)).where(
                TestResult.status == "failed",
                cast(TestResult.created_at, Date) == day,
            )
        )
        passed_data.append(day_passed.scalar() or 0)
        failed_data.append(day_failed.scalar() or 0)

    return {
        "dates": dates,
        "passed": passed_data,
        "failed": failed_data,
    }


@router.get("/radar")
async def get_radar(db: AsyncSession = Depends(get_db)):
    """获取质量维度雷达图数据（复用 quality-score 逻辑）"""
    from app.models.test_case import TestCase, TestType
    from app.models.ai_model import AIEvaluation

    # 1. 自动化覆盖率
    total_cases = await db.execute(select(func.count(TestCase.id)))
    auto_types = [TestType.IOT, TestType.AI, TestType.WEB, TestType.APP, TestType.E2E]
    auto_cases = await db.execute(
        select(func.count(TestCase.id)).where(TestCase.test_type.in_(auto_types))
    )
    total_c = total_cases.scalar() or 0
    auto_c = auto_cases.scalar() or 0
    automation_coverage = round(auto_c / total_c * 100, 1) if total_c > 0 else 0

    # 2. AI 准确率
    ai_eval_result = await db.execute(
        select(func.avg(AIEvaluation.accuracy)).where(AIEvaluation.accuracy.isnot(None))
    )
    ai_accuracy = round((ai_eval_result.scalar() or 0) * 100, 1)

    # 3. 发布成功率
    completed_tasks = await db.execute(
        select(func.count(TestTask.id)).where(
            TestTask.status.in_([TaskStatus.PASSED, TaskStatus.FAILED])
        )
    )
    passed_tasks = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.status == TaskStatus.PASSED)
    )
    completed = completed_tasks.scalar() or 0
    passed = passed_tasks.scalar() or 0
    release_success_rate = round(passed / completed * 100, 1) if completed > 0 else 0

    # 4. 缺陷逃逸率 (反向: 100 - 逃逸率)
    total_results = await db.execute(select(func.count(TestResult.id)))
    failed_results = await db.execute(
        select(func.count(TestResult.id)).where(TestResult.status == "failed")
    )
    total_r = total_results.scalar() or 0
    failed_r = failed_results.scalar() or 0
    defect_escape_rate = round(failed_r / total_r * 100, 1) if total_r > 0 else 0
    defect_score = max(0, 100 - defect_escape_rate * 5)

    # 5. 设备在线率
    total_devices = await db.execute(select(func.count(Device.id)))
    online_devices = await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
    )
    td = total_devices.scalar() or 0
    od = online_devices.scalar() or 0
    device_online_rate = round(od / td * 100, 1) if td > 0 else 0

    return {
        "indicators": [
            {"name": "自动化覆盖", "max": 100},
            {"name": "AI准确率", "max": 100},
            {"name": "发布成功率", "max": 100},
            {"name": "缺陷逃逸率", "max": 100},
            {"name": "设备在线率", "max": 100},
        ],
        "values": [automation_coverage, ai_accuracy, release_success_rate, defect_score, device_online_rate],
    }


@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    """获取活跃告警: P0/P1 缺陷 + 设备离线 + 任务失败"""
    from app.models.defect import Defect, DefectPriority

    alerts = []

    # P0/P1 未关闭缺陷
    p0_defects = await db.execute(
        select(Defect).where(
            Defect.priority.in_([DefectPriority.P0, DefectPriority.P1]),
            Defect.status.notin_(["closed"]),
        ).limit(10)
    )
    for d in p0_defects.scalars().all():
        alerts.append({
            "type": "defect",
            "level": "critical" if d.priority == DefectPriority.P0 else "warning",
            "message": f"[{d.priority.value.upper()}] {d.title}",
            "link": f"/defects/{d.id}",
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })

    # 离线设备
    offline_devices = await db.execute(
        select(Device).where(Device.status == DeviceStatus.OFFLINE).limit(5)
    )
    for d in offline_devices.scalars().all():
        alerts.append({
            "type": "device",
            "level": "warning",
            "message": f"设备离线: {d.name} ({d.device_sn})",
            "link": f"/devices/{d.id}",
            "created_at": None,
        })

    # 最近失败任务
    failed_tasks = await db.execute(
        select(TestTask).where(
            TestTask.status == TaskStatus.FAILED,
        ).order_by(TestTask.id.desc()).limit(5)
    )
    for t in failed_tasks.scalars().all():
        alerts.append({
            "type": "task",
            "level": "error",
            "message": f"任务失败: {t.name}",
            "link": f"/test-tasks/{t.id}",
            "created_at": t.finished_at.isoformat() if t.finished_at else None,
        })

    return {"alerts": alerts, "total": len(alerts)}
