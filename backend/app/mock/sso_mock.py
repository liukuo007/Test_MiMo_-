from __future__ import annotations

import asyncio
import random
import time

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()


class SSOMock:
    """SSO Mock 服务 — 支持 WireMock 远程 Mock 或本地模拟"""

    def __init__(self):
        self._settings = None

    @property
    def settings(self):
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    async def _call_wiremock(self, path: str, json_data: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{self.settings.wiremock_url.rstrip('/')}{path}"
            resp = await client.post(url, json=json_data or {})
            return resp.json()

    async def validate_token(self, token: str) -> dict:
        try:
            return await self._call_wiremock("/api/v1/sso/validate", {"token": token})
        except Exception:
            logger.info("wiremock_sso_fallback", reason="wiremock_unavailable")
            await asyncio.sleep(random.uniform(0.02, 0.1))
            if token == "expired":
                return {"valid": False, "error": "token_expired"}
            return {
                "valid": True,
                "user_id": random.randint(1, 1000),
                "username": f"user_{random.randint(1, 100)}",
                "expires_at": time.time() + 3600,
            }

    async def refresh_token(self, refresh_token: str) -> dict:
        try:
            return await self._call_wiremock("/api/v1/sso/refresh", {"refresh_token": refresh_token})
        except Exception:
            await asyncio.sleep(random.uniform(0.02, 0.1))
            return {
                "access_token": f"new-token-{random.randint(10000, 99999)}",
                "expires_in": 3600,
            }


sso_mock = SSOMock()
