from __future__ import annotations

import asyncio
import time
from typing import Optional

from app.iot.device_state import DeviceEvent
from app.iot.virtual_device import VirtualDevice


async def run_normal_flow(device: VirtualDevice, items: Optional[list[dict]] = None) -> dict:
    """正常业务流程：开门 → 取货 → 关门 → 结算"""
    start = time.time()
    events_log = []

    await device.send_event(DeviceEvent.DOOR_OPEN_CMD)
    events_log.append("door_opened")
    await asyncio.sleep(0.2)

    items = items or [{"sku": "SKU001", "name": "可乐"}]
    for item in items:
        await device.send_event(DeviceEvent.ITEM_DETECTED, {"item": item})
        events_log.append(f"item_detected: {item.get('sku')}")
        await asyncio.sleep(0.3)

        await device.send_event(DeviceEvent.AI_RESULT, {"recognized": True, "sku": item["sku"]})
        events_log.append(f"ai_recognized: {item['sku']}")
        await asyncio.sleep(0.5)

    await device.send_event(DeviceEvent.DOOR_CLOSE_CMD)
    events_log.append("door_closed")
    await asyncio.sleep(0.2)

    await device.send_event(DeviceEvent.PAYMENT_RESULT, {"success": True, "amount": len(items) * 3.5})
    events_log.append("payment_success")

    duration_ms = round((time.time() - start) * 1000, 2)
    return {"status": "passed", "duration_ms": duration_ms, "events": events_log}
