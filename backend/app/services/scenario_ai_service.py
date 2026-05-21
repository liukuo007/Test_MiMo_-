from __future__ import annotations

from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_event import DeviceEvent
from app.models.scenario import ScenarioTemplate


class ScenarioAIService:

    async def replay_order(self, db: AsyncSession, order_id: str) -> dict:
        """Reconstruct scenario steps from device events for a given order."""
        # Try to find events in details JSON
        result = await db.execute(
            select(DeviceEvent)
            .where(DeviceEvent.details["order_id"].as_string() == order_id)
            .order_by(DeviceEvent.created_at)
            .limit(50)
        )
        events = list(result.scalars().all())

        if not events:
            # Try broader search on recent events
            result = await db.execute(
                select(DeviceEvent)
                .order_by(desc(DeviceEvent.created_at))
                .limit(20)
            )
            events = list(result.scalars().all())

        steps = []
        step_id = 1
        for event in events:
            event_type = str(event.event_type)
            action = self._map_event_to_action(event_type)
            if action:
                steps.append({
                    "id": step_id,
                    "action": action["action"],
                    "description": action["description"],
                    "params": event.details or {},
                    "source_event": event_type,
                    "timestamp": str(event.created_at),
                })
                step_id += 1

        if not steps:
            steps = [
                {"id": 1, "action": "device_init", "description": "初始化设备", "params": {}},
                {"id": 2, "action": "simulate_scan", "description": "模拟扫码", "params": {}},
                {"id": 3, "action": "payment", "description": "模拟支付", "params": {}},
            ]

        return {
            "order_id": order_id,
            "steps": steps,
            "event_count": len(events),
            "reconstructed": True,
        }

    def _map_event_to_action(self, event_type: str) -> Optional[dict]:
        """Map a device event type to a scenario action."""
        mapping = {
            "ITEM_DETECTED": {"action": "simulate_scan", "description": "模拟扫码购物"},
            "DOOR_OPEN": {"action": "door_operation", "description": "打开柜门"},
            "DOOR_CLOSE": {"action": "door_operation", "description": "关闭柜门"},
            "PAYMENT": {"action": "payment", "description": "支付流程"},
            "AI_RECOGNITION": {"action": "ai_verify", "description": "AI 识别验证"},
            "HEARTBEAT": {"action": "device_init", "description": "设备心跳"},
            "ERROR": {"action": "error_check", "description": "错误事件"},
            "FAULT": {"action": "error_check", "description": "设备故障"},
            "CONTROL": {"action": "device_control", "description": "设备控制指令"},
        }
        return mapping.get(event_type)

    async def preview_scenario(self, db: AsyncSession, scenario_id: int) -> dict:
        """Preview a scenario template's steps."""
        result = await db.execute(
            select(ScenarioTemplate).where(ScenarioTemplate.id == scenario_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            return {"error": "Scenario not found"}

        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "steps": template.steps_definition or [],
            "source": getattr(template, 'source', 'manual'),
        }


scenario_ai_service = ScenarioAIService()
