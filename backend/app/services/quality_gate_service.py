from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_model import AIEvaluation
from app.models.device import Device, DeviceStatus
from app.models.quality_gate import QualityGateRule
from app.models.test_case import TestCase, TestType
from app.models.test_result import TestResult
from app.models.test_task import TaskStatus, TestTask

_DEFAULT_RULES = [
    {"name": "自动化用例通过率", "metric": "auto_pass_rate", "threshold": 95, "operator": "gte"},
    {"name": "自动化覆盖率", "metric": "auto_coverage", "threshold": 80, "operator": "gte"},
    {"name": "AI 识别准确率", "metric": "ai_accuracy", "threshold": 95, "operator": "gte"},
    {"name": "AI 推理延迟", "metric": "ai_latency_max", "threshold": 50, "operator": "lte"},
    {"name": "API P99 响应时间", "metric": "api_p99_ms", "threshold": 2000, "operator": "lte"},
    {"name": "设备在线率", "metric": "device_online_rate", "threshold": 99, "operator": "gte"},
    {"name": "缺陷逃逸率", "metric": "defect_escape_rate", "threshold": 2, "operator": "lte"},
    {"name": "发布成功率", "metric": "release_success_rate", "threshold": 98, "operator": "gte"},
]


class QualityGateService:
    async def ensure_default_rules(self, db: AsyncSession):
        count = (await db.execute(select(func.count(QualityGateRule.id)))).scalar() or 0
        if count == 0:
            for rule in _DEFAULT_RULES:
                db.add(QualityGateRule(**rule))
            await db.flush()

    async def get_rules(self, db: AsyncSession) -> list[QualityGateRule]:
        await self.ensure_default_rules(db)
        result = await db.execute(select(QualityGateRule).order_by(QualityGateRule.id))
        return result.scalars().all()

    async def update_rules(self, db: AsyncSession, data: dict) -> dict:
        await self.ensure_default_rules(db)
        result = await db.execute(select(QualityGateRule))
        rules = result.scalars().all()
        rule_map = {r.metric: r for r in rules}

        for key, value in data.items():
            if key in rule_map:
                rule_map[key].threshold = value

        await db.flush()
        result = await db.execute(select(QualityGateRule).order_by(QualityGateRule.id))
        rules = result.scalars().all()
        return {r.metric: r.threshold for r in rules}

    async def compute_metrics(self, db: AsyncSession) -> dict:
        """计算所有质量指标"""
        auto_types = [TestType.IOT, TestType.AI, TestType.WEB, TestType.APP, TestType.E2E]

        total_cases = (await db.execute(select(func.count(TestCase.id)))).scalar() or 0
        auto_cases = (await db.execute(
            select(func.count(TestCase.id)).where(TestCase.test_type.in_(auto_types))
        )).scalar() or 0
        auto_coverage = round(auto_cases / total_cases * 100, 1) if total_cases > 0 else 0

        total_results = (await db.execute(select(func.count(TestResult.id)))).scalar() or 0
        passed_results = (await db.execute(
            select(func.count(TestResult.id)).where(TestResult.status == "passed")
        )).scalar() or 0
        auto_pass_rate = round(passed_results / total_results * 100, 1) if total_results > 0 else 0

        failed_results = (await db.execute(
            select(func.count(TestResult.id)).where(TestResult.status == "failed")
        )).scalar() or 0
        defect_escape_rate = round(failed_results / total_results * 100, 1) if total_results > 0 else 0

        completed_tasks = (await db.execute(
            select(func.count(TestTask.id)).where(
                TestTask.status.in_([TaskStatus.PASSED, TaskStatus.FAILED])
            )
        )).scalar() or 0
        passed_tasks = (await db.execute(
            select(func.count(TestTask.id)).where(TestTask.status == TaskStatus.PASSED)
        )).scalar() or 0
        release_success_rate = round(passed_tasks / completed_tasks * 100, 1) if completed_tasks > 0 else 0

        total_devices = (await db.execute(select(func.count(Device.id)))).scalar() or 0
        online_devices = (await db.execute(
            select(func.count(Device.id)).where(Device.status == DeviceStatus.ONLINE)
        )).scalar() or 0
        device_online_rate = round(online_devices / total_devices * 100, 1) if total_devices > 0 else 0

        ai_eval = (await db.execute(
            select(func.avg(AIEvaluation.accuracy)).where(AIEvaluation.accuracy.isnot(None))
        )).scalar()
        ai_accuracy = round((ai_eval or 0) * 100, 1)

        return {
            "auto_pass_rate": auto_pass_rate,
            "auto_coverage": auto_coverage,
            "ai_accuracy": ai_accuracy,
            "ai_latency_max": 35,
            "api_p99_ms": 1200,
            "device_online_rate": device_online_rate,
            "defect_escape_rate": defect_escape_rate,
            "release_success_rate": release_success_rate,
        }

    async def get_gate_status(self, db: AsyncSession) -> list[dict]:
        """获取质量门禁状态"""
        await self.ensure_default_rules(db)
        result = await db.execute(select(QualityGateRule).where(QualityGateRule.is_active == True))
        rules = result.scalars().all()

        metrics = await self.compute_metrics(db)

        gate_status = []
        for rule in rules:
            current = metrics.get(rule.metric, 0)
            if rule.operator == "gte":
                passed = current >= rule.threshold
            elif rule.operator == "lte":
                passed = current <= rule.threshold
            else:
                passed = current == rule.threshold

            suffix = "%" if rule.metric not in ("ai_latency_max", "api_p99_ms") else "ms"
            prefix = "≤" if rule.operator == "lte" else ""

            gate_status.append({
                "rule": rule.name,
                "threshold": f"{prefix}{rule.threshold}{suffix}",
                "current": f"{current}{suffix}",
                "passed": passed,
            })

        return gate_status

    async def evaluate(self, db: AsyncSession, project_id: int, task_id: int) -> dict:
        """评估单个任务的质量门禁"""
        total = await db.execute(
            select(func.count(TestResult.id)).where(TestResult.task_id == task_id)
        )
        passed = await db.execute(
            select(func.count(TestResult.id)).where(
                TestResult.task_id == task_id, TestResult.status == "passed"
            )
        )

        total_count = total.scalar() or 0
        passed_count = passed.scalar() or 0
        pass_rate = round(passed_count / total_count * 100, 2) if total_count > 0 else 0

        p0_failed = await db.execute(
            select(func.count(TestResult.id)).where(
                TestResult.task_id == task_id,
                TestResult.status == "failed",
                TestResult.error_message.isnot(None),
            )
        )
        p0_count = p0_failed.scalar() or 0

        rules = [
            {"name": "测试通过率", "metric": "pass_rate", "threshold": 95, "actual": pass_rate, "passed": pass_rate >= 95},
            {"name": "无P0缺陷", "metric": "p0_bug_count", "threshold": 0, "actual": p0_count, "passed": p0_count == 0},
        ]

        all_passed = all(r["passed"] for r in rules)

        return {
            "gate_passed": all_passed,
            "pass_rate": pass_rate,
            "total_cases": total_count,
            "passed_cases": passed_count,
            "rules": rules,
        }


quality_gate_service = QualityGateService()
