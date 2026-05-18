import asyncio
import random
import time
from dataclasses import dataclass, field

import structlog

from simulator.device import VirtualDevice, VirtualDeviceManager
from simulator.mqtt_handler import MQTTHandler
from simulator.scenarios.normal_flow import run_normal_flow

logger = structlog.get_logger()


@dataclass
class StressTestResult:
    scenario: str = "stress_test"
    device_count: int = 0
    duration_seconds: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    status: str = "pending"
    latencies: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "device_count": self.device_count,
            "duration_seconds": self.duration_seconds,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.successful_requests / self.total_requests * 100, 2) if self.total_requests > 0 else 0,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "status": self.status,
        }


async def run_stress_test(device_count: int, duration_seconds: int, mqtt_handler: MQTTHandler | None = None) -> dict:
    logger.info("stress_test_started", device_count=device_count, duration=duration_seconds)

    manager = VirtualDeviceManager(mqtt_handler)
    devices = manager.create_batch(count=device_count, region="cn")

    result = StressTestResult(device_count=device_count, duration_seconds=duration_seconds)
    start_time = time.time()
    all_latencies = []

    async def run_device_flow(device: VirtualDevice):
        nonlocal result
        while time.time() - start_time < duration_seconds:
            flow_start = time.time()
            try:
                flow_result = await run_normal_flow(device, mqtt_handler)
                latency = flow_result.get("duration_ms", 0)
                all_latencies.append(latency)
                result.total_requests += 1
                if flow_result.get("status") == "passed":
                    result.successful_requests += 1
                else:
                    result.failed_requests += 1
            except Exception as e:
                result.total_requests += 1
                result.failed_requests += 1
                logger.error("stress_test_flow_error", device_sn=device.device_sn, error=str(e))

            await asyncio.sleep(random.uniform(0.1, 0.5))

    tasks = [run_device_flow(d) for d in devices]
    await asyncio.gather(*tasks)

    manager.stop_all()

    if all_latencies:
        all_latencies.sort()
        result.avg_latency_ms = sum(all_latencies) / len(all_latencies)
        p95_idx = int(len(all_latencies) * 0.95)
        p99_idx = int(len(all_latencies) * 0.99)
        result.p95_latency_ms = all_latencies[min(p95_idx, len(all_latencies) - 1)]
        result.p99_latency_ms = all_latencies[min(p99_idx, len(all_latencies) - 1)]

    result.status = "completed"
    logger.info("stress_test_completed", total=result.total_requests, success=result.successful_requests)

    return result.to_dict()
