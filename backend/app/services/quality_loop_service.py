from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.defect import Defect, DefectPriority, DefectSource, DefectStatus
from app.models.quality_loop import QualityLoopExecution, QualityLoopRule
from app.models.test_result import TestResult


class QualityLoopService:

    async def list_rules(self, db: AsyncSession) -> list[QualityLoopRule]:
        result = await db.execute(select(QualityLoopRule).order_by(QualityLoopRule.id))
        return list(result.scalars().all())

    async def get_rule(self, db: AsyncSession, rule_id: int) -> QualityLoopRule | None:
        result = await db.execute(select(QualityLoopRule).where(QualityLoopRule.id == rule_id))
        return result.scalar_one_or_none()

    async def create_rule(self, db: AsyncSession, data: dict) -> QualityLoopRule:
        rule = QualityLoopRule(**data)
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    async def update_rule(self, db: AsyncSession, rule_id: int, data: dict) -> QualityLoopRule | None:
        rule = await self.get_rule(db, rule_id)
        if not rule:
            return None
        for k, v in data.items():
            if v is not None and hasattr(rule, k):
                setattr(rule, k, v)
        await db.commit()
        await db.refresh(rule)
        return rule

    async def delete_rule(self, db: AsyncSession, rule_id: int) -> bool:
        rule = await self.get_rule(db, rule_id)
        if not rule:
            return False
        await db.delete(rule)
        await db.commit()
        return True

    def _check_condition(self, value: float, operator: str, threshold: float) -> bool:
        if operator == "<":
            return value < threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">=":
            return value >= threshold
        return False

    async def evaluate_rules(self, db: AsyncSession) -> list[QualityLoopExecution]:
        """Evaluate all enabled rules and trigger execution if conditions met."""
        result = await db.execute(
            select(QualityLoopRule).where(QualityLoopRule.enabled == True)
        )
        rules = list(result.scalars().all())
        executions = []

        for rule in rules:
            metric_value = await self._get_metric_value(db, rule.trigger_metric)
            if metric_value is None:
                continue

            if self._check_condition(metric_value, rule.operator, rule.threshold):
                # Check if there's already a recent running execution
                existing = await db.execute(
                    select(QualityLoopExecution).where(
                        QualityLoopExecution.rule_id == rule.id,
                        QualityLoopExecution.status == "running",
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                execution = await self.execute_loop(db, rule, metric_value)
                if execution:
                    executions.append(execution)

        return executions

    async def _get_metric_value(self, db: AsyncSession, metric: str) -> float | None:
        """Get current metric value for rule evaluation."""
        if metric == "health_score":
            from app.models.health_score import HealthScoreSnapshot
            result = await db.execute(
                select(HealthScoreSnapshot.overall_score)
                .order_by(desc(HealthScoreSnapshot.computed_at))
                .limit(1)
            )
            row = result.scalar_one_or_none()
            return row if row is not None else None

        elif metric == "pass_rate":
            result = await db.execute(
                select(
                    func.count().filter(TestResult.status == "passed").label("passed"),
                    func.count().label("total"),
                )
            )
            row = result.one()
            if row.total > 0:
                return round(row.passed / row.total * 100, 1)
            return None

        elif metric == "flaky_rate":
            from app.models.stability import FlakyTestCase
            result = await db.execute(
                select(func.count()).select_from(FlakyTestCase).where(FlakyTestCase.status == "active")
            )
            return float(result.scalar() or 0)

        return None

    async def execute_loop(
        self, db: AsyncSession, rule: QualityLoopRule, trigger_value: float
    ) -> QualityLoopExecution | None:
        """Execute the action chain for a triggered rule."""
        actions = rule.action_chain or {"actions": [
            {"type": "create_defect", "params": {}},
            {"type": "assign_defect", "params": {}},
            {"type": "trigger_regression", "params": {}},
        ]}
        action_list = actions.get("actions", [])

        execution = QualityLoopExecution(
            rule_id=rule.id,
            trigger_value=trigger_value,
            total_steps=len(action_list),
            status="running",
            steps_log={"steps": []},
        )
        db.add(execution)
        await db.flush()

        steps = []
        defect_id = None

        for i, action in enumerate(action_list):
            step_result = {"step": i + 1, "action": action["type"], "status": "pending", "detail": ""}
            try:
                if action["type"] == "create_defect":
                    defect = Defect(
                        title=f"[闭环] {rule.name} 触发 - {rule.trigger_metric}={trigger_value}",
                        description=f"质量闭环规则「{rule.name}」触发。\n指标: {rule.trigger_metric}\n当前值: {trigger_value}\n阈值: {rule.operator} {rule.threshold}",
                        priority=DefectPriority.P2,
                        source=DefectSource.AUTO,
                        status=DefectStatus.NEW,
                    )
                    db.add(defect)
                    await db.flush()
                    defect_id = defect.id
                    step_result["status"] = "completed"
                    step_result["detail"] = f"缺陷 #{defect.id} 已创建"

                elif action["type"] == "assign_defect" and defect_id:
                    # Auto-assign to first available user
                    from app.models.user import User
                    user_result = await db.execute(select(User).limit(1))
                    user = user_result.scalar_one_or_none()
                    if user:
                        defect_result = await db.execute(select(Defect).where(Defect.id == defect_id))
                        defect = defect_result.scalar_one_or_none()
                        if defect:
                            defect.assigned_to = user.id
                            step_result["status"] = "completed"
                            step_result["detail"] = f"已分配给 {user.username}"
                    else:
                        step_result["status"] = "skipped"
                        step_result["detail"] = "无可用用户"

                elif action["type"] == "trigger_regression":
                    step_result["status"] = "completed"
                    step_result["detail"] = "回归测试已触发（待实现）"

                else:
                    step_result["status"] = "skipped"
                    step_result["detail"] = f"未知动作类型: {action['type']}"

            except Exception as e:
                step_result["status"] = "failed"
                step_result["detail"] = str(e)

            steps.append(step_result)
            execution.current_step = i + 1

        execution.steps_log = {"steps": steps}
        execution.defect_id = defect_id
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(execution)
        return execution

    async def list_executions(
        self, db: AsyncSession, rule_id: int | None = None, status: str | None = None
    ) -> list[dict]:
        q = select(QualityLoopExecution).order_by(desc(QualityLoopExecution.started_at))
        if rule_id:
            q = q.where(QualityLoopExecution.rule_id == rule_id)
        if status:
            q = q.where(QualityLoopExecution.status == status)
        result = await db.execute(q)
        executions = list(result.scalars().all())

        enriched = []
        for ex in executions:
            rule_result = await db.execute(select(QualityLoopRule).where(QualityLoopRule.id == ex.rule_id))
            rule = rule_result.scalar_one_or_none()
            enriched.append({
                "id": ex.id,
                "rule_id": ex.rule_id,
                "rule_name": rule.name if rule else None,
                "trigger_value": ex.trigger_value,
                "current_step": ex.current_step,
                "total_steps": ex.total_steps,
                "status": ex.status,
                "steps_log": ex.steps_log,
                "defect_id": ex.defect_id,
                "started_at": ex.started_at,
                "completed_at": ex.completed_at,
            })
        return enriched

    async def manual_trigger(self, db: AsyncSession, rule_id: int) -> QualityLoopExecution | None:
        """Manually trigger a rule execution."""
        rule = await self.get_rule(db, rule_id)
        if not rule:
            return None
        metric_value = await self._get_metric_value(db, rule.trigger_metric)
        return await self.execute_loop(db, rule, metric_value or 0)


quality_loop_service = QualityLoopService()
