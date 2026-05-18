from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.defect import Defect
from app.models.quality_report import QualityReport
from app.models.test_case import TestCase
from app.dependencies import CurrentUser
from app.core.exceptions import NotFoundError

from integrations.metersphere.sync_to_ms import metersphere_sync

router = APIRouter()


@router.get("/health", summary="MeterSphere 连接健康检查")
async def ms_health(current_user: CurrentUser = None):
    return await metersphere_sync.health_check()


@router.post("/sync/defect/{defect_id}", summary="推送单个缺陷到 MeterSphere")
async def sync_defect(defect_id: int, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise NotFoundError("Defect", defect_id)
    ms_result = await metersphere_sync.push_defect(defect)
    return {"mimo_defect_id": defect_id, "metersphere_result": ms_result}


@router.post("/sync/report/{report_id}", summary="推送质量报告到 MeterSphere")
async def sync_report(report_id: int, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    result = await db.execute(select(QualityReport).where(QualityReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError("QualityReport", report_id)
    ms_result = await metersphere_sync.push_report(report)
    return {"mimo_report_id": report_id, "metersphere_result": ms_result}


@router.post("/sync/case/{case_id}", summary="推送测试用例到 MeterSphere")
async def sync_case(case_id: int, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    test_case = result.scalar_one_or_none()
    if not test_case:
        raise NotFoundError("TestCase", case_id)
    ms_result = await metersphere_sync.push_test_case(test_case)
    return {"mimo_case_id": case_id, "metersphere_result": ms_result}


@router.post("/sync/all-defects", summary="批量同步所有未关闭缺陷")
async def sync_all_defects(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = None,
):
    query = select(Defect)
    if status:
        query = query.where(Defect.status == status)
    result = await db.execute(query.limit(100))
    defects = result.scalars().all()

    synced = []
    for d in defects:
        ms_result = await metersphere_sync.push_defect(d)
        synced.append({"defect_id": d.id, "ms_result": ms_result})

    return {"synced_count": len(synced), "results": synced}
