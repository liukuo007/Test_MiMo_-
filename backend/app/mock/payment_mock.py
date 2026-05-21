from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()


@dataclass
class PaymentRequest:
    order_id: str
    amount: float
    currency: str = "CNY"
    method: str = "wechat"


@dataclass
class PaymentResponse:
    success: bool
    transaction_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class PaymentMock:
    """支付 Mock 服务 — 支持 WireMock 远程 Mock 或本地模拟"""

    def __init__(self):
        self._settings = None

    @property
    def settings(self):
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def wiremock_url(self) -> str:
        return self.settings.wiremock_url.rstrip("/")

    async def _call_wiremock(self, method: str, path: str, json_data: dict = None) -> dict:
        """通过 WireMock 发起请求"""
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{self.wiremock_url}{path}"
            if method == "POST":
                resp = await client.post(url, json=json_data)
            else:
                resp = await client.get(url)
            return resp.json()

    async def process_payment(self, req: PaymentRequest) -> PaymentResponse:
        try:
            result = await self._call_wiremock("POST", "/api/v1/payment/create", {
                "order_id": req.order_id,
                "amount": req.amount,
                "currency": req.currency,
                "method": req.method,
            })
            return PaymentResponse(
                success=result.get("success", False),
                transaction_id=result.get("transaction_id"),
                error_code=result.get("error_code"),
                error_message=result.get("error_message"),
            )
        except Exception as e:
            logger.info("wiremock_payment_fallback", reason=str(e))
            return await self._local_process(req)

    async def _local_process(self, req: PaymentRequest) -> PaymentResponse:
        """本地模拟 fallback"""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        if req.amount <= 0:
            return PaymentResponse(success=False, error_code="INVALID_AMOUNT", error_message="Amount must be positive")
        if req.amount > 10000:
            return PaymentResponse(success=False, error_code="RISK_CONTROL", error_message="Amount exceeds limit")
        return PaymentResponse(
            success=True,
            transaction_id=f"TXN-{req.order_id}-{random.randint(1000, 9999)}",
        )

    async def refund(self, transaction_id: str, amount: float) -> PaymentResponse:
        try:
            result = await self._call_wiremock("POST", "/api/v1/payment/refund", {
                "transaction_id": transaction_id,
                "amount": amount,
            })
            return PaymentResponse(
                success=result.get("success", False),
                transaction_id=result.get("refund_id"),
                error_code=result.get("error_code"),
            )
        except Exception:
            await asyncio.sleep(random.uniform(0.1, 0.3))
            return PaymentResponse(success=True, transaction_id=f"REF-{transaction_id}")

    async def query_payment(self, order_id: str) -> dict:
        try:
            return await self._call_wiremock("GET", f"/api/v1/payment/query/{order_id}")
        except Exception:
            return {"success": True, "order_id": order_id, "status": "paid"}


payment_mock = PaymentMock()
