from __future__ import annotations

from typing import Optional

import httpx
import structlog

from evaluator.config import config

logger = structlog.get_logger()


class APIClient:
    def __init__(self, base_url: str = ""):
        self.base_url = base_url or config.MIMO_API_URL

    async def report_evaluation(self, evaluation_id: int, result: dict):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.put(f"{self.base_url}/ai/evaluations/{evaluation_id}", json=result)
        except Exception as e:
            logger.warning("report_evaluation_error", evaluation_id=evaluation_id, error=str(e))

    async def get_model_info(self, model_version_id: int) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/ai/models/versions/{model_version_id}")
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning("get_model_info_error", model_version_id=model_version_id, error=str(e))
        return {}


api_client = APIClient()
