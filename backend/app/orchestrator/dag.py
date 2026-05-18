from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    id: str
    name: str
    step_type: str
    config: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    # ── RunnerGo 扩展: 条件分支 ──
    condition: dict | None = None  # {"field": "x", "operator": "eq", "value": "y", "true_branch": "nodeA", "false_branch": "nodeB"}
    # ── RunnerGo 扩展: 循环 ──
    loop_config: dict | None = None  # {"max_iterations": 10, "break_condition": {...}, "items_field": "list"}
    iteration: int = 0  # 当前迭代次数


class DAG:
    """有向无环图 - 测试任务编排（含 RunnerGo 条件分支 & 循环支持）"""

    def __init__(self):
        self.nodes: dict[str, DAGNode] = {}
        self.context: dict[str, Any] = {}  # 步骤间共享上下文（条件分支的判断依据）

    def add_node(self, node: DAGNode):
        self.nodes[node.id] = node

    def get_ready_nodes(self) -> list[DAGNode]:
        """获取所有依赖已满足的节点"""
        ready = []
        for node in self.nodes.values():
            if node.status != StepStatus.PENDING:
                continue
            deps_met = all(
                self.nodes[dep].status == StepStatus.PASSED
                for dep in node.dependencies
                if dep in self.nodes
            )
            if deps_met:
                ready.append(node)
        return ready

    def mark_complete(self, node_id: str, status: StepStatus):
        if node_id in self.nodes:
            self.nodes[node_id].status = status

    def set_context(self, key: str, value: Any):
        """设置共享上下文（步骤间传递数据）"""
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    def is_complete(self) -> bool:
        return all(
            n.status in (StepStatus.PASSED, StepStatus.FAILED, StepStatus.SKIPPED)
            for n in self.nodes.values()
        )

    def has_failed(self) -> bool:
        return any(n.status == StepStatus.FAILED for n in self.nodes.values())

    # ── RunnerGo: 条件分支评估 ──────────────────────────────
    def evaluate_condition(self, node: DAGNode) -> bool:
        """评估节点的条件表达式，返回是否应执行"""
        if node.condition is None:
            return True  # 无条件节点，始终执行

        field_name = node.condition.get("field", "")
        operator = node.condition.get("operator", "eq")
        expected = node.condition.get("value")
        actual = self.context.get(field_name)

        result = self._compare(actual, operator, expected)
        return result

    def resolve_branch(self, node: DAGNode) -> str | None:
        """根据条件结果返回下一个应执行的分支节点 ID"""
        if node.condition is None:
            return None

        condition_result = self.evaluate_condition(node)
        if condition_result:
            return node.condition.get("true_branch")
        else:
            return node.condition.get("false_branch")

    @staticmethod
    def _compare(actual: Any, operator: str, expected: Any) -> bool:
        """条件比较运算"""
        try:
            if operator == "eq" or operator == "==":
                return actual == expected
            elif operator == "neq" or operator == "!=":
                return actual != expected
            elif operator == "gt" or operator == ">":
                return float(actual) > float(expected)
            elif operator == "gte" or operator == ">=":
                return float(actual) >= float(expected)
            elif operator == "lt" or operator == "<":
                return float(actual) < float(expected)
            elif operator == "lte" or operator == "<=":
                return float(actual) <= float(expected)
            elif operator == "contains":
                return str(expected) in str(actual)
            elif operator == "not_contains":
                return str(expected) not in str(actual)
            elif operator == "in":
                return actual in expected if isinstance(expected, list) else False
            elif operator == "not_in":
                return actual not in expected if isinstance(expected, list) else True
            elif operator == "is_null":
                return actual is None
            elif operator == "is_not_null":
                return actual is not None
            elif operator == "regex":
                import re
                return bool(re.search(str(expected), str(actual)))
            else:
                return True  # 未知运算符默认通过
        except (TypeError, ValueError):
            return False

    # ── RunnerGo: 循环节点处理 ──────────────────────────────
    def should_continue_loop(self, node: DAGNode) -> bool:
        """判断循环节点是否应继续迭代"""
        if node.loop_config is None:
            return False

        max_iter = node.loop_config.get("max_iterations", 10)
        if node.iteration >= max_iter:
            return False

        # 检查中断条件
        break_cond = node.loop_config.get("break_condition")
        if break_cond:
            field_name = break_cond.get("field", "")
            operator = break_cond.get("operator", "eq")
            expected = break_cond.get("value")
            actual = self.context.get(field_name)
            if self._compare(actual, operator, expected):
                return False  # 满足中断条件，停止循环

        return True

    def advance_loop(self, node: DAGNode) -> DAGNode:
        """推进循环迭代：重置节点状态以便重新执行"""
        node.iteration += 1
        node.status = StepStatus.PENDING
        return node

    def get_loop_items(self, node: DAGNode) -> list:
        """获取循环遍历的列表数据"""
        if node.loop_config is None:
            return []
        items_field = node.loop_config.get("items_field", "")
        return self.context.get(items_field, [])

    # ── 跳过被条件排除的分支节点 ──────────────────────────
    def skip_excluded_branches(self, resolved_branches: dict[str, str]):
        """
        将未被选中的分支节点标记为 SKIPPED

        Args:
            resolved_branches: {条件节点ID: 被选中的分支节点ID}
        """
        for cond_node_id, chosen_branch_id in resolved_branches.items():
            cond_node = self.nodes.get(cond_node_id)
            if not cond_node or not cond_node.condition:
                continue

            # 获取所有可能的分支
            true_branch = cond_node.condition.get("true_branch")
            false_branch = cond_node.condition.get("false_branch")
            all_branches = {true_branch, false_branch} - {None, ""}

            # 跳过未被选中的分支
            for branch_id in all_branches:
                if branch_id != chosen_branch_id and branch_id in self.nodes:
                    branch_node = self.nodes[branch_id]
                    if branch_node.status == StepStatus.PENDING:
                        branch_node.status = StepStatus.SKIPPED

    @classmethod
    def from_config(cls, config: dict) -> "DAG":
        dag = cls()
        for step in config.get("steps", []):
            dag.add_node(DAGNode(
                id=step["id"],
                name=step["name"],
                step_type=step["type"],
                config=step.get("config", {}),
                dependencies=step.get("dependencies", []),
                condition=step.get("condition"),
                loop_config=step.get("loop"),
            ))
        return dag
