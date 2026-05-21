from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FaultType(str, Enum):
    NETWORK_LATENCY = "network_latency"
    NETWORK_LOSS = "network_loss"
    DEVICE_CRASH = "device_crash"
    IOT_NODE_DOWN = "iot_node_down"
    GPU_CRASH = "gpu_crash"
    REDIS_DOWN = "redis_down"
    CLOCK_DRIFT = "clock_drift"


@dataclass
class ChaosExperiment:
    fault_type: FaultType
    target: str
    duration_seconds: int
    params: Optional[dict] = None


@dataclass
class ChaosResult:
    experiment: ChaosExperiment
    status: str
    observations: list[str]
    system_recovered: bool


class ChaosEngine:
    """混沌测试引擎 - 模拟各类故障注入与系统恢复"""

    async def inject_fault(self, experiment: ChaosExperiment) -> ChaosResult:
        """注入故障并观测系统行为"""
        observations = []
        fault = experiment.fault_type
        duration = experiment.duration_seconds
        severity = (experiment.params or {}).get("severity", 5)

        if fault == FaultType.NETWORK_LATENCY:
            latency_ms = severity * 200
            observations.append(f"注入网络延迟: {latency_ms}ms, 目标: {experiment.target}")
            observations.append(f"等待 {min(duration, 3)}s 观测系统响应...")
            await asyncio.sleep(min(duration, 3))
            observations.append(f"设备心跳间隔增大至 {latency_ms * 2}ms")
            observations.append("MQTT 消息出现排队积压")
            recovered = random.random() > 0.2
            observations.append("网络延迟恢复, 心跳恢复正常" if recovered else "部分设备仍存在高延迟")

        elif fault == FaultType.NETWORK_LOSS:
            loss_rate = min(severity * 10, 100)
            observations.append(f"注入丢包率: {loss_rate}%, 目标: {experiment.target}")
            await asyncio.sleep(min(duration, 3))
            observations.append(f"MQTT 消息丢失率: {loss_rate}%")
            observations.append("触发设备重连机制")
            recovered = random.random() > 0.15
            observations.append("网络恢复, 设备全部重连成功" if recovered else "2 台设备重连超时")

        elif fault == FaultType.DEVICE_CRASH:
            observations.append(f"模拟设备崩溃: {experiment.target}")
            await asyncio.sleep(min(duration, 2))
            observations.append("设备心跳停止")
            observations.append("上报告警: DEVICE_OFFLINE")
            recovered = random.random() > 0.25
            observations.append("设备自动重启恢复" if recovered else "设备需要手动重启")

        elif fault == FaultType.IOT_NODE_DOWN:
            observations.append(f"模拟 IoT 节点宕机: {experiment.target}")
            await asyncio.sleep(min(duration, 2))
            observations.append("该节点下所有设备离线")
            observations.append("触发设备迁移流程")
            recovered = random.random() > 0.3
            observations.append("设备迁移完成, 服务恢复" if recovered else "迁移超时, 部分设备不可用")

        elif fault == FaultType.GPU_CRASH:
            observations.append(f"模拟 GPU 故障: {experiment.target}")
            await asyncio.sleep(min(duration, 2))
            observations.append("AI 推理服务不可用")
            observations.append("回退到 CPU 推理模式")
            observations.append(f"推理延迟从 35ms 上升至 {35 * 8}ms")
            recovered = True
            observations.append("GPU 恢复, 切回 GPU 推理")

        elif fault == FaultType.REDIS_DOWN:
            observations.append("模拟 Redis 宕机")
            await asyncio.sleep(min(duration, 2))
            observations.append("缓存击穿, 所有请求穿透到数据库")
            observations.append(f"数据库 QPS 上升 {severity * 50}%")
            recovered = random.random() > 0.1
            observations.append("Redis 恢复, 缓存重建完成" if recovered else "Redis 主从切换超时")

        elif fault == FaultType.CLOCK_DRIFT:
            drift_ms = severity * 100
            observations.append(f"模拟时钟漂移: {drift_ms}ms, 目标: {experiment.target}")
            await asyncio.sleep(min(duration, 2))
            observations.append(f"设备时间与服务端偏差 {drift_ms}ms")
            observations.append("订单时间戳异常")
            recovered = random.random() > 0.2
            observations.append("NTP 同步恢复" if recovered else "时钟漂移持续存在")

        else:
            await asyncio.sleep(min(duration, 1))
            observations.append(f"未知故障类型: {fault}")
            recovered = True

        return ChaosResult(
            experiment=experiment,
            status="completed",
            observations=observations,
            system_recovered=recovered,
        )

    async def run_chaos_suite(self, experiments: list[ChaosExperiment]) -> list[ChaosResult]:
        """运行混沌测试套件"""
        results = []
        for exp in experiments:
            result = await self.inject_fault(exp)
            results.append(result)
        return results


chaos_engine = ChaosEngine()
