from __future__ import annotations

import asyncio
import random

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()


class SMSMock:
    """短信 Mock 服务 — 支持 WireMock 远程 Mock 或本地模拟"""

    def __init__(self):
        self._settings = None

    @property
    def settings(self):
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    async def _call_wiremock(self, path: str, json_data: dict) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{self.settings.wiremock_url.rstrip('/')}{path}"
            resp = await client.post(url, json=json_data)
            return resp.json()

    async def send_code(self, phone: str, code: str) -> dict:
        try:
            return await self._call_wiremock("/api/v1/sms/send-code", {
                "phone": phone,
                "code": code,
            })
        except Exception as e:
            logger.info("wiremock_sms_fallback", reason=str(e))
            await asyncio.sleep(random.uniform(0.05, 0.2))
            return {"success": True, "message_id": f"SMS-{random.randint(100000, 999999)}"}

    async def send_notification(self, phone: str, message: str) -> dict:
        try:
            return await self._call_wiremock("/api/v1/sms/send-notification", {
                "phone": phone,
                "message": message,
            })
        except Exception:
            await asyncio.sleep(random.uniform(0.05, 0.2))
            return {"success": True, "message_id": f"SMS-{random.randint(100000, 999999)}"}


sms_mock = SMSMock()
