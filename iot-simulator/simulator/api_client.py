from __future__ import annotations

from typing import Optional

import httpx
import structlog

from simulator.config import config

logger = structlog.get_logger()


class APIClient:
    """HTTP client for communicating with MiMo backend."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url or config.MIMO_API_URL

    async def register_device(self, device_sn: str, name: str, device_type: str = "virtual", region: str = "cn") -> dict:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base_url}/devices", json={
                    "name": name,
                    "device_sn": device_sn,
                    "device_type": device_type,
                    "region": region,
                })
                if resp.status_code in (200, 201):
                    return resp.json()
                logger.warning("register_device_failed", device_sn=device_sn, status=resp.status_code)
                return {}
        except Exception as e:
            logger.warning("register_device_error", device_sn=device_sn, error=str(e))
            return {}

    async def report_heartbeat(self, device_sn: str, state: str, temperature: float = 25.0):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(f"{self.base_url}/devices/virtual/heartbeat", json={
                    "device_sn": device_sn,
                    "state": state,
                    "temperature": temperature,
                })
        except Exception as e:
            logger.debug("heartbeat_report_error", device_sn=device_sn, error=str(e))

    async def report_event(self, device_sn: str, event_type: str, details: Optional[dict] = None):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(f"{self.base_url}/devices/virtual/event", json={
                    "device_sn": device_sn,
                    "event_type": event_type,
                    "details": details or {},
                })
        except Exception as e:
            logger.debug("event_report_error", device_sn=device_sn, error=str(e))


api_client = APIClient()
