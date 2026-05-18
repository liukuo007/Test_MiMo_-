import asyncio
import random
import time

import structlog

logger = structlog.get_logger()

FAULT_TYPES = {
    "network_latency": {"min_delay": 2.0, "max_delay": 10.0, "recovery_rate": 0.9},
    "network_loss": {"min_delay": 0, "max_delay": 0, "recovery_rate": 0.7},
    "device_crash": {"min_delay": 3.0, "max_delay": 8.0, "recovery_rate": 0.85},
    "sensor_malfunction": {"min_delay": 1.0, "max_delay": 5.0, "recovery_rate": 0.8},
    "payment_timeout": {"min_delay": 5.0, "max_delay": 15.0, "recovery_rate": 0.75},
    "ai_timeout": {"min_delay": 2.0, "max_delay": 10.0, "recovery_rate": 0.85},
}


async def inject_fault(device, fault_type: str, duration: int = 10) -> dict:
    start = time.time()
    device_sn = device.device_sn

    fault_config = FAULT_TYPES.get(fault_type, FAULT_TYPES["network_latency"])
    observations = []

    logger.info("fault_injection_started", device_sn=device_sn, fault_type=fault_type, duration=duration)

    await device.send_event("fault_inject")
    observations.append(f"[{time.time():.2f}] 设备 {device_sn} 进入 ERROR 状态")

    await asyncio.sleep(min(fault_config["min_delay"], duration * 0.3))
    observations.append(f"[{time.time():.2f}] 故障 '{fault_type}' 已注入, 持续 {duration}s")

    if fault_type == "network_latency":
        delay = random.uniform(1.0, 5.0)
        await asyncio.sleep(delay)
        observations.append(f"[{time.time():.2f}] 网络延迟增加到 {delay:.1f}s")

    elif fault_type == "network_loss":
        observations.append(f"[{time.time():.2f}] 网络连接断开")
        await asyncio.sleep(duration * 0.5)
        observations.append(f"[{time.time():.2f}] 网络连接恢复中...")

    elif fault_type == "device_crash":
        observations.append(f"[{time.time():.2f}] 设备进程崩溃")
        await asyncio.sleep(duration * 0.4)
        observations.append(f"[{time.time():.2f}] 设备正在重启...")

    elif fault_type == "sensor_malfunction":
        observations.append(f"[{time.time():.2f}] 传感器数据异常")
        await asyncio.sleep(duration * 0.3)
        observations.append(f"[{time.time():.2f}] 传感器校准中...")

    elif fault_type == "payment_timeout":
        observations.append(f"[{time.time():.2f}] 支付请求超时")
        await asyncio.sleep(duration * 0.5)
        observations.append(f"[{time.time():.2f}] 支付服务重连...")

    elif fault_type == "ai_timeout":
        observations.append(f"[{time.time():.2f}] AI 推理超时")
        await asyncio.sleep(duration * 0.4)
        observations.append(f"[{time.time():.2f}] AI 服务恢复...")

    recovered = random.random() < fault_config["recovery_rate"]
    if recovered:
        await device.send_event("reset")
        observations.append(f"[{time.time():.2f}] 设备恢复正常")
    else:
        observations.append(f"[{time.time():.2f}] 设备恢复失败, 需要人工介入")

    total_ms = round((time.time() - start) * 1000, 2)
    logger.info("fault_injection_completed", device_sn=device_sn, fault_type=fault_type, recovered=recovered)

    return {
        "device_sn": device_sn,
        "fault_type": fault_type,
        "duration_seconds": duration,
        "actual_duration_ms": total_ms,
        "status": "recovered" if recovered else "unrecovered",
        "system_recovered": recovered,
        "observations": observations,
    }
