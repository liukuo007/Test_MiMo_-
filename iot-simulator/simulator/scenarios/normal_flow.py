import asyncio
import random
import time

import structlog

logger = structlog.get_logger()

NORMAL_FLOW_EVENTS = [
    ("door_open_cmd", 0.2, 0.5),
    ("item_detected", 0.5, 1.5),
    ("ai_result", 0.3, 0.8),
    ("door_close_cmd", 0.1, 0.3),
    ("payment_result", 0.5, 1.0),
    ("payment_success", 0.2, 0.5),
]


async def run_normal_flow(device, mqtt_handler=None) -> dict:
    start = time.time()
    device_sn = device.device_sn
    steps_log = []

    for event, min_delay, max_delay in NORMAL_FLOW_EVENTS:
        step_start = time.time()
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

        new_state = await device.send_event(event)
        step_duration = round((time.time() - step_start) * 1000, 2)
        steps_log.append({
            "event": event,
            "state": new_state.value,
            "duration_ms": step_duration,
        })

        if new_state.value == "error":
            logger.warning("normal_flow_error", device_sn=device_sn, event=event)
            return {
                "device_sn": device_sn,
                "scenario": "normal_flow",
                "status": "failed",
                "duration_ms": round((time.time() - start) * 1000, 2),
                "steps": steps_log,
                "failed_at": event,
            }

    total_ms = round((time.time() - start) * 1000, 2)
    logger.info("normal_flow_completed", device_sn=device_sn, duration_ms=total_ms)
    return {
        "device_sn": device_sn,
        "scenario": "normal_flow",
        "status": "passed",
        "duration_ms": total_ms,
        "steps": steps_log,
    }
