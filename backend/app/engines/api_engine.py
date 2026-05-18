from __future__ import annotations

from typing import Optional

import httpx
import time
from dataclasses import dataclass, field


@dataclass
class APIStep:
    name: str
    method: str
    url: str
    headers: dict = field(default_factory=dict)
    body: Optional[dict] = None
    expected_status: int = 200
    expected_body: Optional[dict] = None


@dataclass
class APIResult:
    step_name: str
    status: str
    status_code: int
    duration_ms: float
    response_body: Optional[dict] = None
    error: Optional[str] = None


class APITestEngine:
    """API 测试引擎"""

    async def execute(self, base_url: str, steps: list[APIStep]) -> list[APIResult]:
        results = []
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            for step in steps:
                start = time.time()
                try:
                    response = await client.request(
                        method=step.method,
                        url=step.url,
                        headers=step.headers,
                        json=step.body,
                    )
                    duration_ms = round((time.time() - start) * 1000, 2)

                    passed = response.status_code == step.expected_status
                    if passed and step.expected_body:
                        body = response.json()
                        for key, value in step.expected_body.items():
                            if body.get(key) != value:
                                passed = False
                                break

                    results.append(APIResult(
                        step_name=step.name,
                        status="passed" if passed else "failed",
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                        response_body=response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                    ))
                except Exception as e:
                    duration_ms = round((time.time() - start) * 1000, 2)
                    results.append(APIResult(
                        step_name=step.name,
                        status="error",
                        status_code=0,
                        duration_ms=duration_ms,
                        error=str(e),
                    ))
        return results


api_engine = APITestEngine()
