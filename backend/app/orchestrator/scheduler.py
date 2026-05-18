from __future__ import annotations

import asyncio
from datetime import datetime

import structlog

from app.orchestrator.dag import DAG, DAGNode, StepStatus

logger = structlog.get_logger()


class TaskScheduler:
    """测试任务调度器（含 RunnerGo 条件分支 & 循环支持）"""

    def __init__(self, step_executor=None):
        self.step_executor = step_executor

    async def execute_dag(self, dag: DAG, step_executor=None) -> dict:
        executor = step_executor or self.step_executor
        """执行 DAG 编排的测试任务"""
        # 将 DAG 注入执行器（供条件分支和循环使用上下文）
        if hasattr(executor, "set_dag"):
            executor.set_dag(dag)

        # 记录条件分支的解析结果
        resolved_branches: dict[str, str] = {}

        max_rounds = 100  # 防止死循环
        round_count = 0

        while not dag.is_complete():
            round_count += 1
            if round_count > max_rounds:
                logger.error("dag_max_rounds_exceeded", rounds=max_rounds)
                break

            ready_nodes = dag.get_ready_nodes()
            if not ready_nodes:
                if not dag.is_complete():
                    logger.error("dag_deadlock", nodes={k: v.status.value for k, v in dag.nodes.items()})
                break

            tasks = []
            for node in ready_nodes:
                tasks.append(self._execute_step(node, executor, dag, resolved_branches))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # 处理条件分支解析: 跳过未被选中的分支
            if resolved_branches:
                dag.skip_excluded_branches(resolved_branches)
                resolved_branches.clear()

        return {
            "status": "failed" if dag.has_failed() else "passed",
            "steps": {nid: n.status.value for nid, n in dag.nodes.items()},
            "context": dag.context,
        }

    async def _execute_step(
        self,
        node: DAGNode,
        step_executor,
        dag: DAG,
        resolved_branches: dict,
    ):
        logger.info("step_started", step_id=node.id, step_name=node.name, step_type=node.step_type)

        # ── RunnerGo: 循环节点特殊处理 ──
        if node.step_type == "loop":
            await self._execute_loop_node(node, step_executor, dag)
            return

        try:
            result = await step_executor(node)
            node.status = StepStatus.PASSED if result.get("status") == "passed" else StepStatus.FAILED

            # 将结果写入上下文
            dag.set_context(f"step_{node.id}", result)

            # ── RunnerGo: 条件分支解析 ──
            if node.step_type == "condition":
                branch_target = dag.resolve_branch(node)
                if branch_target:
                    resolved_branches[node.id] = branch_target
                    logger.info("branch_resolved", node_id=node.id, target=branch_target)

            logger.info("step_completed", step_id=node.id, status=node.status.value)
        except Exception as e:
            node.status = StepStatus.FAILED
            logger.error("step_failed", step_id=node.id, error=str(e))

    async def _execute_loop_node(self, node: DAGNode, step_executor, dag: DAG):
        """循环节点执行：支持迭代和条件中断"""
        logger.info("loop_started", node_id=node.id, max_iterations=node.loop_config.get("max_iterations", 10))

        try:
            result = await step_executor(node)
            node.status = StepStatus.PASSED if result.get("status") == "passed" else StepStatus.FAILED
            dag.set_context(f"step_{node.id}", result)
            logger.info(
                "loop_completed",
                node_id=node.id,
                total_iterations=result.get("total_iterations", 0),
                passed=result.get("passed", 0),
                failed=result.get("failed", 0),
            )
        except Exception as e:
            node.status = StepStatus.FAILED
            logger.error("loop_failed", node_id=node.id, error=str(e))


scheduler = TaskScheduler()
