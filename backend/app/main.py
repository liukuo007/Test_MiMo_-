from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.v1.router import api_router
from app.core.logging import setup_logging
from app.core.middleware import TraceMiddleware, RequestLoggingMiddleware
from app.core.metrics import MetricsMiddleware, metrics_endpoint
from app.core.shadow_traffic import ShadowTrafficMiddleware
from app.services.scheduler_service import scheduler_service
from app.iot.mqtt_client import mqtt_client
import structlog

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await scheduler_service.start()
    mqtt_client.connect()
    yield
    mqtt_client.disconnect()
    await scheduler_service.stop()


app = FastAPI(
    title="MiMo - 智能货柜全链路测试平台",
    description="智能货柜质量基础设施 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)
app.add_middleware(ShadowTrafficMiddleware)
app.add_middleware(TraceMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router, prefix="/api/v1")

app.add_route("/metrics", metrics_endpoint)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", exc_info=exc, path=request.url.path, method=request.method)
    detail = str(exc) if settings.app_debug else "Internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.app_name}
