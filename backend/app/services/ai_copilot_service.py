from __future__ import annotations

import re

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.device_event import DeviceEvent
from app.models.test_result import TestResult
from app.models.trace import TraceSpan
from app.services.stability_service import FAILURE_CATEGORIES


class AICopilotService:

    async def analyze_failure(self, db: AsyncSession, result_id: int) -> dict:
        """Analyze a failed test result: correlate with device events and traces."""
        result = await db.execute(select(TestResult).where(TestResult.id == result_id))
        test_result = result.scalar_one_or_none()
        if not test_result:
            return {"error": "Test result not found"}

        # Get related device events (match via device_sn -> Device.id)
        events = []
        if test_result.device_sn:
            dev_result = await db.execute(
                select(Device.id).where(Device.device_sn == test_result.device_sn).limit(1)
            )
            device_id = dev_result.scalar_one_or_none()
            if device_id:
                ev_result = await db.execute(
                    select(DeviceEvent)
                    .where(DeviceEvent.device_id == device_id)
                    .order_by(desc(DeviceEvent.created_at))
                    .limit(20)
                )
                events = [
                    {
                        "event_type": str(e.event_type),
                        "message": e.message,
                        "details": e.details,
                        "created_at": str(e.created_at),
                    }
                    for e in ev_result.scalars().all()
                ]

        # Get related trace spans
        traces = []
        if test_result.trace_id:
            tr_result = await db.execute(
                select(TraceSpan)
                .where(TraceSpan.trace_id == test_result.trace_id)
                .order_by(TraceSpan.started_at)
            )
            traces = [
                {
                    "span_name": s.operation,
                    "span_type": s.service,
                    "duration_ms": s.duration_ms,
                    "status": s.status,
                    "error": (s.logs or {}).get("error"),
                }
                for s in tr_result.scalars().all()
            ]

        # Classify root cause
        error_msg = test_result.error_message or ""
        category = await self._classify_error(error_msg, events, traces)

        # Generate suggestion
        suggestion = self._generate_suggestion(category, error_msg, events, traces)

        return {
            "test_result_id": result_id,
            "root_cause": error_msg[:200] if error_msg else "Unknown",
            "category": category,
            "confidence": 0.7 if category != "unknown" else 0.3,
            "related_events": events,
            "related_traces": traces,
            "suggestion": suggestion,
        }

    async def _classify_error(self, error_msg: str, events: list, traces: list) -> str:
        """Classify error using keyword matching + event correlation."""
        lower = error_msg.lower()

        # Keyword-based classification
        scores: dict[str, int] = {}
        for cat, keywords in FAILURE_CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                scores[cat] = score

        # Event-based hints
        event_types = [str(e.get("event_type", "")).lower() for e in events]
        if "fault" in event_types or "error" in event_types:
            scores["data_corruption"] = scores.get("data_corruption", 0) + 2

        # Trace-based hints
        slow_spans = [t for t in traces if (t.get("duration_ms") or 0) > 5000]
        if slow_spans:
            scores["network_error"] = scores.get("network_error", 0) + 1

        if not scores:
            return "unknown"
        return max(scores, key=scores.get)

    def _generate_suggestion(self, category: str, error_msg: str, events: list, traces: list) -> str:
        suggestions = {
            "mqtt_timeout": "检查 MQTT Broker 连接状态，确认设备在线。可尝试增加超时时间或重试机制。",
            "ai_misprediction": "AI 模型识别结果不符合预期。建议检查图片质量、模型版本，或更新训练数据集。",
            "payment_failure": "支付流程失败。检查 Mock 支付服务配置，确认交易金额和订单格式正确。",
            "network_error": "网络连接异常。检查环境网络配置、DNS 解析，确认服务端点可达。",
            "config_issue": "配置问题。检查环境变量、数据库连接字符串、API Key 等配置项。",
            "data_corruption": "数据异常。检查测试数据完整性，确认数据库状态和缓存一致性。",
        }
        return suggestions.get(category, "建议查看详细错误日志和链路追踪信息，定位具体失败原因。")

    async def generate_test_from_nl(self, description: str) -> dict:
        """Generate test steps from natural language description using keyword mapping."""
        lower = description.lower()

        steps = []
        step_id = 1

        # Pattern: 设备初始化
        if any(kw in lower for kw in ["设备", "初始化", "开机", "连接"]):
            steps.append({
                "id": step_id,
                "action": "device_init",
                "description": "初始化虚拟设备并连接 MQTT",
                "params": {"device_type": "cabinet"},
            })
            step_id += 1

        # Pattern: 扫码/购物
        if any(kw in lower for kw in ["扫码", "购物", "商品", "选购", "取货"]):
            steps.append({
                "id": step_id,
                "action": "simulate_scan",
                "description": "模拟用户扫码购物事件",
                "params": {"product_count": 1},
            })
            step_id += 1

        # Pattern: 支付
        if any(kw in lower for kw in ["支付", "付款", "结账", "微信", "支付宝"]):
            steps.append({
                "id": step_id,
                "action": "payment",
                "description": "模拟支付流程",
                "params": {"payment_method": "wechat"},
            })
            step_id += 1

        # Pattern: 开门/关门
        if any(kw in lower for kw in ["开门", "关门", "门", "柜门"]):
            steps.append({
                "id": step_id,
                "action": "door_operation",
                "description": "模拟柜门开关操作",
                "params": {"operation": "open_close"},
            })
            step_id += 1

        # Pattern: 温度/传感器
        if any(kw in lower for kw in ["温度", "传感器", "监控", "报警"]):
            steps.append({
                "id": step_id,
                "action": "sensor_check",
                "description": "检查传感器数据和告警",
                "params": {"sensor_type": "temperature"},
            })
            step_id += 1

        # Pattern: AI 识别
        if any(kw in lower for kw in ["ai", "识别", "检测", "图像", "视觉"]):
            steps.append({
                "id": step_id,
                "action": "ai_verify",
                "description": "AI 图像识别验证",
                "params": {"verify_type": "object_detection"},
            })
            step_id += 1

        # Default: if no pattern matched
        if not steps:
            steps.append({
                "id": 1,
                "action": "device_init",
                "description": "初始化虚拟设备",
                "params": {},
            })
            steps.append({
                "id": 2,
                "action": "simulate_scan",
                "description": "模拟基本操作",
                "params": {},
            })

        return {
            "description": description,
            "steps": steps,
            "estimated_duration_ms": len(steps) * 3000,
            "suggested_devices": ["虚拟货柜 A", "虚拟货柜 B"],
        }

    async def auto_fix_selector(self, selector: str, context: str | None = None) -> dict:
        """Suggest fixes for a broken selector."""
        fixes = []

        # Common selector patterns
        if selector.startswith("#"):
            # ID selector - suggest alternatives
            base_id = selector[1:]
            fixes.extend([
                {"selector": f'[data-testid="{base_id}"]', "reason": "使用 data-testid 更稳定"},
                {"selector": f'[id*="{base_id}"]', "reason": "模糊匹配 ID"},
                {"selector": f'.{base_id}', "reason": "尝试 class 选择器"},
            ])
        elif selector.startswith("."):
            # Class selector
            base_class = selector[1:]
            fixes.extend([
                {"selector": f'[class*="{base_class}"]', "reason": "模糊匹配 class"},
                {"selector": f'[data-testid*="{base_class}"]', "reason": "尝试 data-testid"},
            ])
        elif selector.startswith("["):
            # Attribute selector
            fixes.extend([
                {"selector": selector.replace("=", '*="'), "reason": "改为模糊匹配"},
            ])
        elif selector.startswith("//") or selector.startswith("("):
            # XPath selector
            fixes.extend([
                {"selector": re.sub(r'\[\d+\]', '', selector), "reason": "移除位置索引"},
                {"selector": re.sub(r'/text\(\)', '', selector), "reason": "移除 text() 谓词"},
            ])

        # Generic fallbacks
        fixes.extend([
            {"selector": '[data-testid]', "reason": "使用通用 data-testid"},
            {"selector": 'button', "reason": "降级为标签选择器"},
        ])

        return {
            "original_selector": selector,
            "selector_type": "xpath" if selector.startswith(("//", "(")) else "css",
            "suggested_fixes": fixes[:5],
            "confidence": 0.6,
        }

    async def generate_scenario(self, description: str) -> dict:
        """Generate a complete scenario template from natural language."""
        test_result = await self.generate_test_from_nl(description)

        return {
            "name": f"AI生成 - {description[:30]}",
            "description": description,
            "steps": test_result["steps"],
            "source": "ai_generated",
        }


ai_copilot_service = AICopilotService()
