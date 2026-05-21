from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Optional

import httpx
import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.device_event import DeviceEvent, DeviceEventType

logger = structlog.get_logger()

router = APIRouter()

SMOKE_DEVICE_SN = "SMOKE-VIRTUAL-001"


class SmokeStepResult(BaseModel):
    step: int
    name: str
    status: str
    duration_ms: float
    detail: str = ""
    error: Optional[str] = None


class SmokeTestResponse(BaseModel):
    status: str
    total_duration_ms: float
    steps: list[SmokeStepResult]


@router.post("/run", response_model=SmokeTestResponse)
async def run_smoke_test(db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    """一键式全链路冒烟测试"""
    results: list[SmokeStepResult] = []
    total_start = time.time()

    step1 = await _step1_init_device(db)
    results.append(step1)
    if step1.status == "failed":
        return SmokeTestResponse(status="failed", total_duration_ms=_ms(total_start), steps=results)

    step2 = await _step2_simulate_events(db)
    results.append(step2)
    if step2.status == "failed":
        return SmokeTestResponse(status="failed", total_duration_ms=_ms(total_start), steps=results)

    step3 = await _step3_verify_payment()
    results.append(step3)

    overall = "passed" if all(s.status == "passed" for s in results) else "failed"
    return SmokeTestResponse(status=overall, total_duration_ms=_ms(total_start), steps=results)


async def _step1_init_device(db: AsyncSession) -> SmokeStepResult:
    start = time.time()
    try:
        result = await db.execute(select(Device).where(Device.device_sn == SMOKE_DEVICE_SN))
        device = result.scalar_one_or_none()

        if not device:
            device = Device(
                device_sn=SMOKE_DEVICE_SN,
                name="冒烟测试-虚拟货柜",
                device_type=DeviceType.VIRTUAL_L1,
                status=DeviceStatus.ONLINE,
                region="cn-smoke",
                firmware_version="v2.0.0-smoke",
                ip_address="127.0.0.1",
                temperature=25.0,
            )
            db.add(device)
        else:
            device.status = DeviceStatus.ONLINE
            device.last_heartbeat = datetime.now()
            device.temperature = 25.0

        await db.flush()
        await db.refresh(device)

        return SmokeStepResult(
            step=1,
            name="虚拟设备初始化",
            status="passed",
            duration_ms=_ms(start),
            detail=f"设备 {SMOKE_DEVICE_SN} 已上线, id={device.id}",
        )
    except Exception as e:
        logger.error("smoke_step1_failed", error=str(e))
        return SmokeStepResult(step=1, name="虚拟设备初始化", status="failed", duration_ms=_ms(start), error=str(e))


async def _step2_simulate_events(db: AsyncSession) -> SmokeStepResult:
    start = time.time()
    try:
        result = await db.execute(select(Device).where(Device.device_sn == SMOKE_DEVICE_SN))
        device = result.scalar_one_or_none()
        if not device:
            return SmokeStepResult(step=2, name="模拟购物事件", status="failed", duration_ms=_ms(start), error="冒烟设备不存在")

        events = [
            (DeviceEventType.DOOR_OPEN, "[冒烟测试] 用户扫码开门"),
            (DeviceEventType.ITEM_DETECTED, "[冒烟测试] AI识别 SKU-SMOKE-001, confidence=0.98"),
            (DeviceEventType.DOOR_CLOSE, "[冒烟测试] 关门结算完成"),
        ]

        event_names = []
        for etype, msg in events:
            db.add(DeviceEvent(device_id=device.id, event_type=etype, message=msg))
            event_names.append(etype.value)

        await db.flush()

        return SmokeStepResult(
            step=2,
            name="模拟购物事件",
            status="passed",
            duration_ms=_ms(start),
            detail=f"已上报 3 个事件: {' -> '.join(event_names)}",
        )
    except Exception as e:
        logger.error("smoke_step2_failed", error=str(e))
        return SmokeStepResult(step=2, name="模拟购物事件", status="failed", duration_ms=_ms(start), error=str(e))


async def _step3_verify_payment() -> SmokeStepResult:
    start = time.time()
    try:
        from app.config import get_settings
        wiremock_url = get_settings().wiremock_url.rstrip("/")
        order_id = f"SMOKE-{uuid.uuid4().hex[:8]}"

        async with httpx.AsyncClient(timeout=10) as client:
            pay_resp = await client.post(
                f"{wiremock_url}/api/v1/payment/create",
                json={"order_id": order_id, "amount": 9.90, "currency": "CNY", "method": "wechat"},
            )
            if pay_resp.status_code != 200:
                return SmokeStepResult(step=3, name="校验支付 Mock", status="failed", duration_ms=_ms(start),
                                       error=f"WireMock HTTP {pay_resp.status_code}")

            pay_data = pay_resp.json()
            if not pay_data.get("success"):
                return SmokeStepResult(step=3, name="校验支付 Mock", status="failed", duration_ms=_ms(start),
                                       error=f"支付失败: {pay_data.get('error_message')}")

            query_resp = await client.get(f"{wiremock_url}/api/v1/payment/query/{order_id}")
            query_data = query_resp.json()

        return SmokeStepResult(
            step=3,
            name="校验支付 Mock",
            status="passed",
            duration_ms=_ms(start),
            detail=f"order={order_id}, txn={pay_data.get('transaction_id', '-')}, 状态={query_data.get('status', '-')}",
        )
    except httpx.ConnectError:
        return SmokeStepResult(step=3, name="校验支付 Mock", status="failed", duration_ms=_ms(start),
                               error="WireMock 服务不可达, 请确认 wiremock 容器已启动")
    except Exception as e:
        logger.error("smoke_step3_failed", error=str(e))
        return SmokeStepResult(step=3, name="校验支付 Mock", status="failed", duration_ms=_ms(start), error=str(e))


def _ms(start: float) -> float:
    return round((time.time() - start) * 1000, 1)
