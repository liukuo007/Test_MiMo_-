from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum


class SimulationLevel(str, Enum):
    L1_PROTOCOL = "l1_protocol"
    L2_STATE = "l2_state"
    L3_PHYSICAL = "l3_physical"


@dataclass
class VirtualDeviceConfig:
    device_sn: str
    region: str = "cn"
    simulation_level: SimulationLevel = SimulationLevel.L2_STATE


@dataclass
class SimulationResult:
    device_sn: str
    scenario: str
    status: str
    duration_ms: float
    events: list[dict] = field(default_factory=list)
    error: str | None = None


class IoTTestEngine:
    """IoT 仿真测试引擎"""

    def __init__(self):
        self._devices: dict[str, VirtualDeviceConfig] = {}

    async def create_virtual_devices(self, count: int, config: VirtualDeviceConfig) -> list[str]:
        sns = []
        for i in range(count):
            sn = f"VIR-{config.region.upper()}-{uuid.uuid4().hex[:8].upper()}"
            self._devices[sn] = VirtualDeviceConfig(
                device_sn=sn,
                region=config.region,
                simulation_level=config.simulation_level,
            )
            sns.append(sn)
        return sns

    async def simulate_normal_flow(self, device_sn: str) -> SimulationResult:
        """模拟正常业务流程：开门 → 取货 → 关门 → 结算"""
        import time
        start = time.time()
        events = []

        steps = [
            ("heartbeat", 100),
            ("door_open", 200),
            ("item_detected", 500),
            ("ai_recognition", 800),
            ("door_close", 200),
            ("order_generated", 300),
            ("payment_success", 500),
            ("inventory_updated", 100),
        ]

        for step_name, delay_ms in steps:
            await asyncio.sleep(delay_ms / 1000)
            events.append({"step": step_name, "timestamp": time.time(), "status": "ok"})

        duration_ms = round((time.time() - start) * 1000, 2)
        return SimulationResult(
            device_sn=device_sn,
            scenario="normal_flow",
            status="passed",
            duration_ms=duration_ms,
            events=events,
        )

    async def simulate_stress(self, device_count: int, duration_seconds: int) -> dict:
        """压力测试：模拟大量设备并发消息"""
        import random
        import time

        start = time.time()
        total_messages = 0
        latencies = []
        errors = 0

        # 模拟设备并发发送心跳和业务消息
        end_time = start + duration_seconds
        while time.time() < end_time:
            batch_size = min(device_count, 50)  # 每批最多 50 个设备
            tasks = []
            for _ in range(batch_size):
                # 模拟单设备消息延迟
                base_latency = 50 + (device_count / 100) * 10  # 设备越多延迟越高
                latency = max(10, base_latency + random.gauss(0, 20))
                latencies.append(latency)
                total_messages += 1
                if random.random() < 0.001 * (device_count / 100):  # 设备越多错误率越高
                    errors += 1

            await asyncio.sleep(0.1)  # 每 100ms 一个批次

        latencies.sort()
        p99_idx = int(len(latencies) * 0.99) if latencies else 0

        return {
            "device_count": device_count,
            "duration_seconds": duration_seconds,
            "total_messages": total_messages,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "p99_latency_ms": round(latencies[p99_idx], 2) if latencies else 0,
            "error_rate": round(errors / total_messages, 4) if total_messages else 0,
            "throughput_msg_per_sec": round(total_messages / duration_seconds, 1) if duration_seconds else 0,
        }

    async def cleanup(self, device_sns: list[str]):
        for sn in device_sns:
            self._devices.pop(sn, None)


iot_engine = IoTTestEngine()
