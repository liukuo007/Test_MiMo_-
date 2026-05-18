from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from enum import Enum


class FaultType(str, Enum):
    NETWORK_LATENCY = "network_latency"
    PACKET_LOSS = "packet_loss"
    DEVICE_OFFLINE = "device_offline"
    CAMERA_FAILURE = "camera_failure"
    SENSOR_DRIFT = "sensor_drift"
    POWER_FLUCTUATION = "power_fluctuation"


@dataclass
class FaultConfig:
    fault_type: FaultType
    severity: float = 0.5  # 0.0 ~ 1.0
    duration_seconds: int = 60


class FaultInjector:
    """故障注入器"""

    async def inject(self, device_sn: str, config: FaultConfig) -> dict:
        if config.fault_type == FaultType.NETWORK_LATENCY:
            return await self._inject_latency(device_sn, config)
        elif config.fault_type == FaultType.PACKET_LOSS:
            return await self._inject_packet_loss(device_sn, config)
        elif config.fault_type == FaultType.DEVICE_OFFLINE:
            return await self._inject_offline(device_sn, config)
        elif config.fault_type == FaultType.CAMERA_FAILURE:
            return await self._inject_camera_failure(device_sn, config)
        return {"status": "unsupported"}

    async def _inject_latency(self, device_sn: str, config: FaultConfig) -> dict:
        latency_ms = int(config.severity * 5000)
        return {"fault": "network_latency", "latency_ms": latency_ms, "duration": config.duration_seconds}

    async def _inject_packet_loss(self, device_sn: str, config: FaultConfig) -> dict:
        loss_rate = config.severity
        return {"fault": "packet_loss", "loss_rate": loss_rate, "duration": config.duration_seconds}

    async def _inject_offline(self, device_sn: str, config: FaultConfig) -> dict:
        await asyncio.sleep(config.duration_seconds)
        return {"fault": "device_offline", "duration": config.duration_seconds}

    async def _inject_camera_failure(self, device_sn: str, config: FaultConfig) -> dict:
        return {"fault": "camera_failure", "duration": config.duration_seconds}


fault_injector = FaultInjector()
