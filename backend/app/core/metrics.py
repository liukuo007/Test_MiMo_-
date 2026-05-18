from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse


class MetricsCollector:
    """Lightweight in-memory metrics collector with Prometheus text exposition format."""

    def __init__(self):
        self._lock = Lock()
        self._request_count: dict[str, int] = defaultdict(int)
        self._request_duration_sum: dict[str, float] = defaultdict(float)
        self._request_duration_count: dict[str, int] = defaultdict(int)
        self._request_errors: dict[str, int] = defaultdict(int)

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float):
        key = f"{method}:{path}"
        with self._lock:
            self._request_count[key] += 1
            self._request_duration_sum[key] += duration_ms
            self._request_duration_count[key] += 1
            if status_code >= 400:
                self._request_errors[key] += 1

    def render(self) -> str:
        lines = []
        lines.append("# HELP mimo_http_requests_total Total HTTP requests")
        lines.append("# TYPE mimo_http_requests_total counter")
        with self._lock:
            for key, count in sorted(self._request_count.items()):
                method, path = key.split(":", 1)
                lines.append(f'mimo_http_requests_total{{method="{method}",path="{path}"}} {count}')

        lines.append("")
        lines.append("# HELP mimo_http_request_duration_ms_avg Average request duration in ms")
        lines.append("# TYPE mimo_http_request_duration_ms_avg gauge")
        with self._lock:
            for key, total in sorted(self._request_duration_sum.items()):
                count = self._request_duration_count[key]
                avg = round(total / count, 2) if count > 0 else 0
                method, path = key.split(":", 1)
                lines.append(f'mimo_http_request_duration_ms_avg{{method="{method}",path="{path}"}} {avg}')

        lines.append("")
        lines.append("# HELP mimo_http_request_errors_total Total HTTP errors (4xx/5xx)")
        lines.append("# TYPE mimo_http_request_errors_total counter")
        with self._lock:
            for key, count in sorted(self._request_errors.items()):
                method, path = key.split(":", 1)
                lines.append(f'mimo_http_request_errors_total{{method="{method}",path="{path}"}} {count}')

        return "\n".join(lines) + "\n"


metrics_collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        path = request.url.path
        if not path.startswith("/metrics"):
            normalized = _normalize_path(path)
            metrics_collector.record_request(request.method, normalized, response.status_code, duration_ms)

        return response


def _normalize_path(path: str) -> str:
    """Replace numeric/UUID path segments with :id to keep cardinality low."""
    import re
    parts = path.strip("/").split("/")
    normalized = []
    for part in parts:
        if part.isdigit() or re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", part):
            normalized.append(":id")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized)


async def metrics_endpoint(request: Request) -> PlainTextResponse:
    return PlainTextResponse(metrics_collector.render(), media_type="text/plain")
