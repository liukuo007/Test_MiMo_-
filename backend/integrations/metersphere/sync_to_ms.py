"""
MeterSphere 同步桥接器

当 MiMo 平台产生缺陷（Defect）或测试报告（QualityReport）时，
自动通过 MeterSphere REST API 推送数据，实现双向同步。

使用方式:
  from integrations.metersphere.sync_to_ms import metersphere_sync
  await metersphere_sync.push_defect(defect)
  await metersphere_sync.push_report(report, project)
"""

from __future__ import annotations

import os
from typing import Optional
from datetime import datetime

import httpx
import structlog

logger = structlog.get_logger()

# ── 配置（可通过环境变量覆盖） ──────────────────────────────
MS_BASE_URL = os.getenv("METERSPHERE_URL", "http://localhost:8081")
MS_ACCESS_KEY = os.getenv("MS_ACCESS_KEY", "")
MS_SECRET_KEY = os.getenv("MS_SECRET_KEY", "")
MS_PROJECT_ID = os.getenv("MS_PROJECT_ID", "mimo-project-001")

# MeterSphere 优先级映射: MiMo p0→P0, p1→P1, p2→P2, p3→P3
PRIORITY_MAP = {"p0": "P0", "p1": "P1", "p2": "P2", "p3": "P3"}

# MeterSphere 缺陷状态映射
STATUS_MAP = {
    "new": "new",
    "in_progress": "processing",
    "fixed": "resolved",
    "verified": "verified",
    "closed": "closed",
    "reopened": "reopened",
}


class MeterSphereSync:
    """MeterSphere 双向同步客户端"""

    def __init__(self, base_url: str = MS_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Content-Type": "application/json",
                    "AccessKey": MS_ACCESS_KEY,
                    "SecretKey": MS_SECRET_KEY,
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── 推送缺陷到 MeterSphere ──────────────────────────────
    async def push_defect(self, defect) -> dict:
        """
        将 MiMo Defect 推送到 MeterSphere 缺陷管理模块

        Args:
            defect: app.models.defect.Defect 实例或 dict
        """
        if hasattr(defect, "__dict__"):
            data = {
                "title": defect.title,
                "description": defect.description or "",
                "severity": PRIORITY_MAP.get(
                    defect.priority.value if hasattr(defect.priority, "value") else str(defect.priority),
                    "P2",
                ),
                "status": STATUS_MAP.get(
                    defect.status.value if hasattr(defect.status, "value") else str(defect.status),
                    "new",
                ),
                "projectId": MS_PROJECT_ID,
                "platform": "MiMo",
                "customFields": {
                    "mimo_defect_id": str(defect.id),
                    "source": defect.source.value if hasattr(defect.source, "value") else str(defect.source),
                    "device_sn": getattr(defect, "device_sn", None),
                    "test_task_id": str(getattr(defect, "test_task_id", "")),
                    "created_at": defect.created_at.isoformat() if getattr(defect, "created_at", None) else None,
                },
            }
        else:
            data = defect

        client = await self._get_client()
        try:
            resp = await client.post("/api/defect/v1/add", json=data)
            resp.raise_for_status()
            result = resp.json()
            logger.info("metersphere_defect_pushed", defect_id=data.get("title"), ms_result=result)
            return result
        except httpx.HTTPError as e:
            logger.error("metersphere_defect_push_failed", error=str(e))
            return {"success": False, "error": str(e)}

    # ── 推送测试报告到 MeterSphere ──────────────────────────
    async def push_report(self, report, project=None) -> dict:
        """
        将 MiMo QualityReport 推送到 MeterSphere 报告模块

        Args:
            report: app.models.quality_report.QualityReport 实例或 dict
            project: app.models.project.Project 实例（可选）
        """
        if hasattr(report, "__dict__"):
            data = {
                "name": f"MiMo 质量报告 #{report.id}",
                "projectId": MS_PROJECT_ID,
                "reportType": "performance",
                "summary": {
                    "overall_score": float(report.overall_score) if report.overall_score else 0,
                    "pass_rate": float(report.pass_rate) if report.pass_rate else 0,
                    "defect_escape_rate": float(report.defect_escape_rate) if report.defect_escape_rate else 0,
                },
                "content": report.dimensions if hasattr(report, "dimensions") else {},
                "generatedAt": report.generated_at.isoformat() if getattr(report, "generated_at", None) else None,
                "customFields": {
                    "mimo_report_id": str(report.id),
                    "project_name": project.name if project else None,
                },
            }
        else:
            data = report

        client = await self._get_client()
        try:
            resp = await client.post("/api/report/v1/add", json=data)
            resp.raise_for_status()
            result = resp.json()
            logger.info("metersphere_report_pushed", report_id=data.get("name"), ms_result=result)
            return result
        except httpx.HTTPError as e:
            logger.error("metersphere_report_push_failed", error=str(e))
            return {"success": False, "error": str(e)}

    # ── 同步测试用例到 MeterSphere ──────────────────────────
    async def push_test_case(self, test_case) -> dict:
        if hasattr(test_case, "__dict__"):
            data = {
                "name": test_case.name,
                "projectId": MS_PROJECT_ID,
                "module": getattr(test_case, "module", "默认模块"),
                "priority": PRIORITY_MAP.get(
                    test_case.priority.value if hasattr(test_case, "priority", ) and hasattr(test_case.priority, "value") else "p2",
                    "P2",
                ),
                "type": "functional",
                "method": "auto" if test_case.test_type.value != "manual" else "manual",
                "steps": [
                    {
                        "num": i + 1,
                        "desc": step.get("name", ""),
                        "result": step.get("action", ""),
                    }
                    for i, step in enumerate(getattr(test_case, "steps", []) or [])
                ],
                "customFields": {
                    "mimo_case_id": str(test_case.id),
                    "test_type": test_case.test_type.value if hasattr(test_case, "test_type") else "api",
                },
            }
        else:
            data = test_case

        client = await self._get_client()
        try:
            resp = await client.post("/api/test/case/v1/add", json=data)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("metersphere_case_push_failed", error=str(e))
            return {"success": False, "error": str(e)}

    # ── 推送测试结果到 MeterSphere ──────────────────────────
    async def push_test_result(self, task, results: list[dict]) -> dict:
        data = {
            "name": f"MiMo 任务执行 - {task.name}",
            "projectId": MS_PROJECT_ID,
            "type": "API",
            "status": "completed" if task.status.value == "passed" else "error",
            "executionMethod": "API",
            "testResults": [
                {
                    "caseName": r.get("name", ""),
                    "status": "Pass" if r.get("status") == "passed" else "Failure",
                    "duration": r.get("duration_ms", 0),
                    "message": r.get("message", ""),
                }
                for r in results
            ],
        }

        client = await self._get_client()
        try:
            resp = await client.post("/api/test/plan/v1/run", json=data)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            logger.error("metersphere_result_push_failed", error=str(e))
            return {"success": False, "error": str(e)}

    # ── 健康检查 ──────────────────────────────────────────
    async def health_check(self) -> dict:
        client = await self._get_client()
        try:
            resp = await client.get("/api/v1/system/health")
            return {"connected": True, "status": resp.status_code, "url": self.base_url}
        except httpx.HTTPError as e:
            return {"connected": False, "error": str(e), "url": self.base_url}


# 单例
metersphere_sync = MeterSphereSync()
