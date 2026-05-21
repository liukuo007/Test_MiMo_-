from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_model import AIEvaluation
from app.models.device import Device, DeviceStatus
from app.models.device_event import DeviceEvent, DeviceEventType
from app.models.test_result import TestResult
from app.models.trace import TraceSpan

logger = structlog.get_logger()

RELEASE_THRESHOLD = 80.0


@dataclass
class DimensionResult:
    name: str
    key: str
    weight: float
    value: float
    score: float
    status: str


@dataclass
class HealthScoreResult:
    overall_score: float
    release_allowed: bool
    dimensions: list[DimensionResult] = field(default_factory=list)


class HealthScoreService:

    async def compute_health_score(
        self, db: AsyncSession, project_id: Optional[int] = None, region: Optional[str] = None
    ) -> HealthScoreResult:
        """计算 7 维质量健康分"""

        pass_rate = await self._compute_pass_rate(db, project_id)
        ai_accuracy = await self._compute_ai_accuracy(db)
        payment_success_rate = await self._compute_payment_success_rate(db)
        device_online_rate = await self._compute_device_online_rate(db, region)
        mqtt_latency_score = await self._compute_mqtt_latency_score(db)
        crash_rate = await self._compute_crash_rate(db)
        flaky_ratio = await self._compute_flaky_ratio(db, project_id)

        dimensions = [
            DimensionResult("用例通过率", "pass_rate", 0.15, pass_rate, pass_rate * 0.15, "good" if pass_rate >= 90 else "warn" if pass_rate >= 70 else "bad"),
            DimensionResult("AI 识别准确率", "ai_accuracy", 0.20, ai_accuracy, ai_accuracy * 0.20, "good" if ai_accuracy >= 90 else "warn" if ai_accuracy >= 70 else "bad"),
            DimensionResult("支付成功率", "payment_success_rate", 0.15, payment_success_rate, payment_success_rate * 0.15, "good" if payment_success_rate >= 95 else "warn" if payment_success_rate >= 80 else "bad"),
            DimensionResult("设备在线率", "device_online_rate", 0.20, device_online_rate, device_online_rate * 0.20, "good" if device_online_rate >= 95 else "warn" if device_online_rate >= 80 else "bad"),
            DimensionResult("MQTT P99 延迟", "mqtt_latency", 0.10, mqtt_latency_score, mqtt_latency_score * 0.10, "good" if mqtt_latency_score >= 80 else "warn" if mqtt_latency_score >= 50 else "bad"),
            DimensionResult("崩溃率", "crash_rate", 0.10, crash_rate, crash_rate * 0.10, "good" if crash_rate >= 95 else "warn" if crash_rate >= 80 else "bad"),
            DimensionResult("Flaky 比例", "flaky_ratio", 0.10, flaky_ratio, flaky_ratio * 0.10, "good" if flaky_ratio >= 90 else "warn" if flaky_ratio >= 70 else "bad"),
        ]

        overall_score = round(sum(d.score for d in dimensions), 1)
        release_allowed = overall_score >= RELEASE_THRESHOLD

        return HealthScoreResult(
            overall_score=overall_score,
            release_allowed=release_allowed,
            dimensions=dimensions,
        )

    async def _compute_pass_rate(self, db: AsyncSession, project_id: Optional[int]) -> float:
        total_q = select(func.count(TestResult.id))
        passed_q = select(func.count(TestResult.id)).where(TestResult.status == "passed")

        if project_id:
            from app.models.test_task import TestTask
            task_ids = select(TestTask.id).where(TestTask.project_id == project_id)
            total_q = total_q.where(TestResult.task_id.in_(task_ids))
            passed_q = passed_q.where(TestResult.task_id.in_(task_ids))

        total = (await db.execute(total_q)).scalar() or 0
        passed = (await db.execute(passed_q)).scalar() or 0
        return round(passed / total * 100, 1) if total > 0 else 0

    async def _compute_ai_accuracy(self, db: AsyncSession) -> float:
        result = await db.execute(
            select(func.avg(AIEvaluation.accuracy)).where(AIEvaluation.accuracy.isnot(None))
        )
        val = result.scalar()
        return round(val * 100, 1) if val else 0

    async def _compute_payment_success_rate(self, db: AsyncSession) -> float:
        total = (await db.execute(
            select(func.count(DeviceEvent.id)).where(
                DeviceEvent.event_type == DeviceEventType.PAYMENT
            )
        )).scalar() or 0

        success = (await db.execute(
            select(func.count(DeviceEvent.id)).where(
                DeviceEvent.event_type == DeviceEventType.PAYMENT,
                DeviceEvent.message.ilike("%成功%"),
            )
        )).scalar() or 0

        return round(success / total * 100, 1) if total > 0 else 100

    async def _compute_device_online_rate(self, db: AsyncSession, region: Optional[str]) -> float:
        total_q = select(func.count(Device.id))
        online_q = select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)

        if region:
            total_q = total_q.where(Device.region == region)
            online_q = online_q.where(Device.region == region)

        total = (await db.execute(total_q)).scalar() or 0
        online = (await db.execute(online_q)).scalar() or 0
        return round(online / total * 100, 1) if total > 0 else 0

    async def _compute_mqtt_latency_score(self, db: AsyncSession) -> float:
        result = await db.execute(
            select(func.percentile_cont(0.99).within_group(TraceSpan.duration_ms))
            .where(TraceSpan.service == "mqtt")
        )
        p99 = result.scalar()

        if p99 is None:
            return 100

        if p99 <= 100:
            return 100
        elif p99 <= 500:
            return 80
        elif p99 <= 1000:
            return 60
        elif p99 <= 2000:
            return 40
        else:
            return 20

    async def _compute_crash_rate(self, db: AsyncSession) -> float:
        total = (await db.execute(select(func.count(DeviceEvent.id)))).scalar() or 0
        errors = (await db.execute(
            select(func.count(DeviceEvent.id)).where(
                DeviceEvent.event_type.in_([DeviceEventType.FAULT, DeviceEventType.ERROR])
            )
        )).scalar() or 0

        if total == 0:
            return 100
        crash_pct = errors / total * 100
        return round(max(0, 100 - crash_pct * 10), 1)

    async def _compute_flaky_ratio(self, db: AsyncSession, project_id: Optional[int]) -> float:
        query = (
            select(
                TestResult.test_case_id,
                func.count(TestResult.id).label("total"),
                func.count(case((TestResult.status == "failed", 1))).label("failures"),
            )
            .where(TestResult.test_case_id.isnot(None))
            .group_by(TestResult.test_case_id)
            .having(func.count(TestResult.id) >= 3)
        )

        if project_id:
            from app.models.test_task import TestTask
            task_ids = select(TestTask.id).where(TestTask.project_id == project_id)
            query = query.where(TestResult.task_id.in_(task_ids))

        result = await db.execute(query)
        rows = result.all()

        if not rows:
            return 100

        flaky_count = 0
        for row in rows:
            if row.failures > 0 and row.failures < row.total:
                flaky_count += 1

        return round((1 - flaky_count / len(rows)) * 100, 1) if rows else 100


health_score_service = HealthScoreService()
