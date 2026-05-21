from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.trace import Trace, TraceSpan

router = APIRouter()


class SpanIngest(BaseModel):
    span_id: str
    parent_span_id: Optional[str] = None
    service: str
    operation: str
    status: str = "ok"
    duration_ms: Optional[int] = None
    tags: Optional[dict] = None
    logs: Optional[list] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class TraceIngest(BaseModel):
    trace_id: str
    service: str
    operation: str
    status: str = "ok"
    duration_ms: Optional[int] = None
    tags: Optional[dict] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    spans: list[SpanIngest] = []


@router.post("/ingest")
async def ingest_trace(req: TraceIngest, db: AsyncSession = Depends(get_db)):
    trace = Trace(
        trace_id=req.trace_id,
        root_span_id=req.spans[0].span_id if req.spans else None,
        service=req.service,
        operation=req.operation,
        status=req.status,
        duration_ms=req.duration_ms,
        tags=req.tags,
        started_at=req.started_at,
        finished_at=req.finished_at,
    )
    db.add(trace)

    for span in req.spans:
        db.add(TraceSpan(
            trace_id=req.trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
            service=span.service,
            operation=span.operation,
            status=span.status,
            duration_ms=span.duration_ms,
            tags=span.tags,
            logs=span.logs,
            started_at=span.started_at,
            finished_at=span.finished_at,
        ))

    await db.flush()
    return {"message": "Trace ingested", "trace_id": req.trace_id, "span_count": len(req.spans)}


@router.get("")
async def list_traces(
    db: AsyncSession = Depends(get_db),
    service: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(Trace)
    if service:
        query = query.where(Trace.service == service)
    if status:
        query = query.where(Trace.status == status)
    query = query.offset(skip).limit(limit).order_by(Trace.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{trace_id}")
async def get_trace_detail(trace_id: str, db: AsyncSession = Depends(get_db)):
    trace_result = await db.execute(select(Trace).where(Trace.trace_id == trace_id))
    trace = trace_result.scalar_one_or_none()
    if not trace:
        raise NotFoundError("Trace", trace_id)

    spans_result = await db.execute(
        select(TraceSpan).where(TraceSpan.trace_id == trace_id).order_by(TraceSpan.started_at)
    )
    spans = spans_result.scalars().all()

    return {
        "trace": trace,
        "spans": spans,
    }
