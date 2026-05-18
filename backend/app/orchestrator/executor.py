from __future__ import annotations

import asyncio
import random
import structlog

from app.orchestrator.dag import DAGNode, DAG, StepStatus
from app.engines.api_engine import api_engine, APIStep
from app.engines.iot_engine import iot_engine
from app.engines.ai_engine import ai_engine
from app.engines.web_engine import web_engine, WebTestStep
from app.engines.app_engine import app_engine, AppTestStep
from app.engines.chaos_engine import chaos_engine, ChaosExperiment, FaultType

logger = structlog.get_logger()


class StepExecutor:
    """步骤执行器 - 根据步骤类型分发到对应引擎（含 RunnerGo 条件分支 & 循环）"""

    def __init__(self):
        self.dag: DAG | None = None

    def set_dag(self, dag: DAG):
        self.dag = dag

    async def execute(self, node: DAGNode) -> dict:
        # ── RunnerGo: 条件分支节点 ──
        if node.step_type == "condition":
            return await self._execute_condition(node)

        # ── RunnerGo: 循环节点 ──
        if node.step_type == "loop":
            return await self._execute_loop(node)

        handler = getattr(self, f"_execute_{node.step_type}", None)
        if not handler:
            logger.error("unknown_step_type", step_type=node.step_type)
            return {"status": "failed", "error": f"Unknown step type: {node.step_type}"}
        return await handler(node.config)

    # ── RunnerGo: 条件分支执行 ──────────────────────────────
    async def _execute_condition(self, node: DAGNode) -> dict:
        """
        条件分支节点：根据上下文中的变量值决定走向

        config 示例:
        {
            "field": "api_status_code",
            "operator": "eq",
            "value": 200,
            "true_branch": "success_node_id",
            "false_branch": "fail_node_id"
        }
        """
        if not self.dag:
            return {"status": "failed", "error": "DAG context not set"}

        condition = node.config.get("condition", node.condition or {})
        field_name = condition.get("field", "")
        operator = condition.get("operator", "eq")
        expected = condition.get("value")
        actual = self.dag.get_context(field_name)

        result = DAG._compare(actual, operator, expected)

        logger.info(
            "condition_evaluated",
            node_id=node.id,
            field=field_name,
            operator=operator,
            actual=actual,
            expected=expected,
            result=result,
        )

        # 将条件结果写入上下文
        self.dag.set_context(f"condition_{node.id}", result)

        return {
            "status": "passed",
            "condition_result": result,
            "field": field_name,
            "actual": actual,
            "expected": expected,
        }

    # ── RunnerGo: 循环执行 ──────────────────────────────
    async def _execute_loop(self, node: DAGNode) -> dict:
        """
        循环节点：对列表数据逐项执行子步骤，或重复执行直到满足条件

        config 示例:
        {
            "items_field": "test_data_list",       # 上下文中的列表字段
            "max_iterations": 10,                  # 最大迭代次数
            "break_condition": {                    # 中断条件（可选）
                "field": "error_count",
                "operator": "gt",
                "value": 3
            },
            "sub_step": {                           # 每次迭代执行的子步骤
                "type": "api",
                "config": {"base_url": "...", "steps": [...]}
            }
        }
        """
        if not self.dag:
            return {"status": "failed", "error": "DAG context not set"}

        loop_config = node.loop_config or node.config.get("loop", {})
        max_iterations = loop_config.get("max_iterations", 10)
        items_field = loop_config.get("items_field", "")
        sub_step_config = loop_config.get("sub_step", {})

        items = self.dag.get_context(items_field, []) if items_field else list(range(max_iterations))
        if not items:
            items = list(range(max_iterations))

        results = []
        total_passed = 0
        total_failed = 0

        for i, item in enumerate(items[:max_iterations]):
            # 设置当前迭代项到上下文
            self.dag.set_context(f"loop_{node.id}_current_item", item)
            self.dag.set_context(f"loop_{node.id}_index", i)

            # 检查中断条件
            break_cond = loop_config.get("break_condition")
            if break_cond:
                break_field = break_cond.get("field", "")
                break_op = break_cond.get("operator", "eq")
                break_val = break_cond.get("value")
                break_actual = self.dag.get_context(break_field)
                if DAG._compare(break_actual, break_op, break_val):
                    logger.info("loop_break", node_id=node.id, iteration=i, reason=f"{break_field} {break_op} {break_val}")
                    break

            # 执行子步骤
            if sub_step_config:
                sub_node = DAGNode(
                    id=f"{node.id}_iter_{i}",
                    name=f"{node.name} [迭代 {i}]",
                    step_type=sub_step_config.get("type", "api"),
                    config=sub_step_config.get("config", {}),
                )
                sub_result = await self.execute(sub_node)
            else:
                # 没有子步骤时，仅记录迭代
                sub_result = {"status": "passed", "iteration": i, "item": item}

            results.append(sub_result)
            if sub_result.get("status") == "passed":
                total_passed += 1
            else:
                total_failed += 1

        overall_status = "passed" if total_failed == 0 else "failed"
        return {
            "status": overall_status,
            "total_iterations": len(results),
            "passed": total_passed,
            "failed": total_failed,
            "results": results,
        }

    # ── 原有步骤类型 ──────────────────────────────────────
    async def _execute_api(self, config: dict) -> dict:
        steps = [APIStep(**s) for s in config.get("steps", [])]
        results = await api_engine.execute(config.get("base_url", ""), steps)
        all_passed = all(r.status == "passed" for r in results)
        # 将最后一个响应写入上下文（供条件分支使用）
        if results and self.dag:
            last = results[-1]
            self.dag.set_context("api_status_code", getattr(last, "status_code", None))
            self.dag.set_context("api_response_body", getattr(last, "body", None))
        return {"status": "passed" if all_passed else "failed", "results": [r.__dict__ for r in results]}

    async def _execute_iot(self, config: dict) -> dict:
        result = await iot_engine.simulate_normal_flow(config.get("device_sn", ""))
        if self.dag:
            self.dag.set_context("iot_status", result.status)
            self.dag.set_context("iot_duration_ms", result.duration_ms)
        return {"status": result.status, "duration_ms": result.duration_ms}

    async def _execute_wait(self, config: dict) -> dict:
        seconds = config.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"status": "passed"}

    async def _execute_assert(self, config: dict) -> dict:
        """执行断言检查"""
        assert_type = config.get("type", "equals")
        actual = config.get("actual")
        expected = config.get("expected")
        field_name = config.get("field", "value")

        # 支持从上下文读取值
        if isinstance(actual, str) and self.dag and actual.startswith("$"):
            actual = self.dag.get_context(actual[1:])

        passed = False
        message = ""

        if assert_type == "equals":
            passed = actual == expected
            message = f"{field_name}: 期望={expected}, 实际={actual}"
        elif assert_type == "not_equals":
            passed = actual != expected
            message = f"{field_name}: 不应等于 {expected}"
        elif assert_type == "contains":
            passed = expected in str(actual) if actual else False
            message = f"{field_name}: 期望包含 '{expected}'"
        elif assert_type == "greater_than":
            passed = float(actual or 0) > float(expected or 0)
            message = f"{field_name}: {actual} > {expected}"
        elif assert_type == "less_than":
            passed = float(actual or 0) < float(expected or 0)
            message = f"{field_name}: {actual} < {expected}"
        elif assert_type == "not_null":
            passed = actual is not None and actual != ""
            message = f"{field_name}: 不为空"
        elif assert_type == "status_code":
            passed = actual == expected
            message = f"HTTP 状态码: 期望={expected}, 实际={actual}"
        else:
            passed = True
            message = f"未知断言类型: {assert_type}, 默认通过"

        result_status = "passed" if passed else "failed"
        if self.dag:
            self.dag.set_context(f"assert_{field_name}", result_status)

        return {
            "status": result_status,
            "message": message,
            "assert_type": assert_type,
        }

    async def _execute_ai_eval(self, config: dict) -> dict:
        """执行 AI 模型评测"""
        result = await ai_engine.evaluate_model(
            model_path=config.get("model_path", ""),
            dataset_path=config.get("dataset_path", "medium"),
            model_version=config.get("model_version", "v2.0"),
        )
        if self.dag:
            self.dag.set_context("ai_accuracy", result.accuracy)
            self.dag.set_context("ai_f1_score", result.f1_score)
        return {
            "status": "passed" if result.accuracy >= config.get("threshold", 0.9) else "failed",
            "accuracy": result.accuracy,
            "recall": result.recall,
            "f1_score": result.f1_score,
            "avg_latency_ms": result.avg_latency_ms,
            "total_samples": result.total_samples,
            "failed_samples": result.failed_samples,
        }

    async def _execute_web(self, config: dict) -> dict:
        """执行 Web 自动化测试"""
        steps = [WebTestStep(**s) for s in config.get("steps", [])]
        results = await web_engine.execute(config.get("base_url", ""), steps)
        all_passed = all(r.status == "passed" for r in results)
        return {"status": "passed" if all_passed else "failed", "results": [r.__dict__ for r in results]}

    async def _execute_app(self, config: dict) -> dict:
        """执行 App 自动化测试"""
        steps = [AppTestStep(**s) for s in config.get("steps", [])]
        results = await app_engine.execute(config.get("app_path", ""), steps)
        all_passed = all(r.status == "passed" for r in results)
        return {"status": "passed" if all_passed else "failed", "results": [r.__dict__ for r in results]}

    async def _execute_chaos(self, config: dict) -> dict:
        """执行混沌测试"""
        experiment = ChaosExperiment(
            fault_type=FaultType(config.get("fault_type", "network_latency")),
            target=config.get("target", "default"),
            duration_seconds=config.get("duration_seconds", 5),
            params=config.get("params"),
        )
        result = await chaos_engine.inject_fault(experiment)
        return {
            "status": "passed" if result.system_recovered else "failed",
            "observations": result.observations,
            "system_recovered": result.system_recovered,
        }

    async def _execute_payment(self, config: dict) -> dict:
        """执行支付模拟步骤"""
        from app.mock.payment_mock import payment_mock, PaymentRequest

        req_data = config.get("request", {})
        req = PaymentRequest(
            order_id=req_data.get("order_id", f"ORD-{random.randint(1000, 9999)}"),
            amount=req_data.get("amount", 10.0),
            currency=req_data.get("currency", "CNY"),
            method=req_data.get("method", "wechat"),
        )
        result = await payment_mock.process_payment(req)
        if self.dag:
            self.dag.set_context("payment_success", result.success)
            self.dag.set_context("payment_transaction_id", result.transaction_id)
        return {
            "status": "passed" if result.success else "failed",
            "transaction_id": result.transaction_id,
            "error_code": result.error_code,
            "error_message": result.error_message,
        }

    async def _execute_sms(self, config: dict) -> dict:
        """执行短信模拟步骤"""
        from app.mock.sms_mock import sms_mock

        action = config.get("action", "send_code")
        if action == "send_code":
            result = await sms_mock.send_code(
                config.get("phone", "+8613800000000"),
                config.get("code", "123456"),
            )
        else:
            result = await sms_mock.send_notification(
                config.get("phone", "+8613800000000"),
                config.get("message", "Test notification"),
            )
        return {
            "status": "passed" if result.get("success") else "failed",
            "message_id": result.get("message_id"),
        }

    async def _execute_sso(self, config: dict) -> dict:
        """执行 SSO 模拟步骤"""
        from app.mock.sso_mock import sso_mock

        action = config.get("action", "validate")
        if action == "validate":
            result = await sso_mock.validate_token(config.get("token", "test-token"))
        else:
            result = await sso_mock.refresh_token(config.get("refresh_token", "test-refresh-token"))
        is_valid = result.get("valid", False) or result.get("access_token") is not None
        return {
            "status": "passed" if is_valid else "failed",
            "result": result,
        }


step_executor = StepExecutor()
