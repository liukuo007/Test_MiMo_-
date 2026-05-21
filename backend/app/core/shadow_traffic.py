"""
Takin 风格全链路压测 — 流量染色中间件

借鉴 Takin 核心思想:
  1. 通过请求头 `p-testing: true` 识别压测流量
  2. 自动为压测流量添加染色标记 (X-Shadow: true)
  3. 染色流量上下文透传: 子请求自动继承染色标记
  4. 影子库路由: 染色流量自动路由到影子库/影子表
  5. 流量隔离: 压测数据不会污染生产数据

使用:
  在 main.py 中添加:
    from app.core.shadow_traffic import ShadowTrafficMiddleware
    app.add_middleware(ShadowTrafficMiddleware)
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

# ── 上下文变量: 压测流量标记（全链路透传） ──────────────────
_shadow_context: ContextVar[bool] = ContextVar("shadow_traffic", default=False)
_shadow_trace_id: ContextVar[str] = ContextVar("shadow_trace_id", default="")


def is_shadow_traffic() -> bool:
    """当前请求是否为压测染色流量"""
    return _shadow_context.get(False)


def get_shadow_trace_id() -> str:
    """获取压测流量的追踪 ID"""
    return _shadow_trace_id.get("")


def set_shadow_context(enabled: bool, trace_id: str = ""):
    """手动设置压测上下文（用于引擎内部调用时透传）"""
    _shadow_context.set(enabled)
    if trace_id:
        _shadow_trace_id.set(trace_id)


# ── 染色标记头 ──────────────────────────────────────────
SHADOW_HEADER = "X-Shadow"
SHADOW_TRACE_HEADER = "X-Shadow-Trace-Id"
TESTING_HEADER = "p-testing"
TESTING_TOKEN_HEADER = "p-testing-token"

# 染色标识值
SHADOW_VALUE = "true"
SHADOW_ORIGIN_MIMO = "mimo"


class ShadowTrafficMiddleware(BaseHTTPMiddleware):
    """
    压测流量染色中间件

    识别规则（任一命中即为压测流量）:
      1. 请求头 `p-testing: true`
      2. 请求头 `X-Shadow: true`
      3. 请求参数 `__shadow=true`（用于 URL 级别染色）
      4. 特定压测 Token（`p-testing-token` 头）
    """

    # 不需要染色的路径（静态资源、健康检查等）
    SKIP_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过不需要染色的路径
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # ── 识别压测流量 ──
        is_shadow = self._detect_shadow_traffic(request)

        # 设置上下文
        trace_id = request.headers.get(SHADOW_TRACE_HEADER) or request.headers.get("X-Trace-Id", "")
        if is_shadow and not trace_id:
            trace_id = f"shadow-{uuid.uuid4().hex[:12]}"

        token = _shadow_context.set(is_shadow)
        trace_token = _shadow_trace_id.set(trace_id)

        start = time.time()
        try:
            response = await call_next(request)
        finally:
            _shadow_context.reset(token)
            _shadow_trace_id.reset(trace_token)

        duration_ms = round((time.time() - start) * 1000, 2)

        # ── 响应头注入染色标记 ──
        if is_shadow:
            response.headers[SHADOW_HEADER] = SHADOW_VALUE
            response.headers[SHADOW_TRACE_HEADER] = trace_id
            logger.info(
                "shadow_request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                shadow_trace_id=trace_id,
            )

        return response

    def _detect_shadow_traffic(self, request: Request) -> bool:
        """多策略识别压测流量"""
        headers = request.headers

        # 策略1: p-testing 头
        if headers.get(TESTING_HEADER, "").lower() == SHADOW_VALUE:
            return True

        # 策略2: X-Shadow 头（上游系统已染色）
        if headers.get(SHADOW_HEADER, "").lower() == SHADOW_VALUE:
            return True

        # 策略3: URL 参数
        if request.query_params.get("__shadow", "").lower() == SHADOW_VALUE:
            return True

        # 策略4: 压测 Token
        if headers.get(TESTING_TOKEN_HEADER):
            return True

        return False


# ── 数据库影子路由辅助 ──────────────────────────────────────
def get_shadow_database_url(original_url: str) -> str:
    """
    根据原始数据库 URL 生成影子库 URL

    策略: 将数据库名替换为 shadow_ 前缀
    例: postgresql://mimo:mimo123@host:5432/mimo
      → postgresql://mimo:mimo123@host:5432/mimo_shadow
    """
    if "/mimo" in original_url:
        return original_url.replace("/mimo", "/mimo_shadow")
    return original_url


def get_shadow_table_name(original_table: str) -> str:
    """生成影子表名"""
    return f"shadow_{original_table}"


# ── Redis 影子 Key 辅助 ──────────────────────────────────
def get_shadow_redis_key(original_key: str) -> str:
    """为压测流量生成影子 Redis Key"""
    return f"shadow:{original_key}"


# ── 压测流量统计 ──────────────────────────────────────────
class ShadowTrafficStats:
    """压测流量统计收集器"""

    def __init__(self):
        self.total_requests = 0
        self.shadow_requests = 0
        self.total_duration_ms = 0.0
        self.shadow_duration_ms = 0.0

    def record(self, is_shadow: bool, duration_ms: float):
        self.total_requests += 1
        self.total_duration_ms += duration_ms
        if is_shadow:
            self.shadow_requests += 1
            self.shadow_duration_ms += duration_ms

    def get_stats(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "shadow_requests": self.shadow_requests,
            "shadow_ratio": round(self.shadow_requests / max(self.total_requests, 1) * 100, 2),
            "avg_duration_ms": round(self.total_duration_ms / max(self.total_requests, 1), 2),
            "avg_shadow_duration_ms": round(self.shadow_duration_ms / max(self.shadow_requests, 1), 2),
        }


shadow_stats = ShadowTrafficStats()
