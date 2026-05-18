from __future__ import annotations

import subprocess
import os
import signal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.dependencies import CurrentUser
from app.core.exceptions import BadRequestError

router = APIRouter()

# 全局 Locust 进程管理
_locust_process: Optional[subprocess.Popen] = None


class LocustStartRequest(BaseModel):
    host: str = "http://localhost:8100"
    users: int = 100
    spawn_rate: int = 10
    run_time: str = "5m"
    tags: str = ""  # comma-separated tags
    locustfile: str = "integrations/locust/locustfile.py"


class LocustStatus(BaseModel):
    running: bool
    pid: Optional[int] = None
    host: Optional[str] = None
    users: Optional[int] = None


@router.post("/start", summary="启动 Locust 压测")
async def start_locust(req: LocustStartRequest, current_user: CurrentUser = None):
    global _locust_process

    if _locust_process and _locust_process.poll() is None:
        raise BadRequestError("Locust is already running (pid={})".format(_locust_process.pid))

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    locustfile_path = os.path.join(project_root, req.locustfile)

    if not os.path.exists(locustfile_path):
        raise BadRequestError(f"Locustfile not found: {locustfile_path}")

    cmd = [
        "locust",
        "-f", locustfile_path,
        "--host", req.host,
        "--users", str(req.users),
        "--spawn-rate", str(req.spawn_rate),
        "--run-time", req.run_time,
        "--headless",
        "--only-summary",
        "--csv", "/tmp/mimo-locust",
    ]
    if req.tags:
        cmd.extend(["--tags", req.tags])

    _locust_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=project_root,
    )

    return {
        "message": "Locust started",
        "pid": _locust_process.pid,
        "host": req.host,
        "users": req.users,
        "spawn_rate": req.spawn_rate,
        "run_time": req.run_time,
    }


@router.post("/stop", summary="停止 Locust 压测")
async def stop_locust(current_user: CurrentUser = None):
    global _locust_process

    if not _locust_process or _locust_process.poll() is not None:
        _locust_process = None
        return {"message": "Locust is not running"}

    _locust_process.send_signal(signal.SIGTERM)
    try:
        _locust_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _locust_process.kill()
    pid = _locust_process.pid
    _locust_process = None

    return {"message": "Locust stopped", "pid": pid}


@router.get("/status", summary="查看 Locust 状态")
async def locust_status(current_user: CurrentUser = None):
    running = _locust_process is not None and _locust_process.poll() is None
    return LocustStatus(
        running=running,
        pid=_locust_process.pid if running else None,
        host=None,
        users=None,
    )


@router.get("/results", summary="获取压测结果")
async def locust_results(current_user: CurrentUser = None):
    """读取 Locust headless 模式输出的 CSV 统计"""
    import glob
    import csv

    results = {}
    for csv_file in glob.glob("/tmp/mimo-locust*.csv"):
        name = os.path.basename(csv_file).replace("mimo-locust_", "").replace(".csv", "")
        try:
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                if rows:
                    results[name] = rows[-1]  # 最后一行是汇总
        except Exception:
            pass

    return {
        "running": _locust_process is not None and _locust_process.poll() is None,
        "results": results,
    }
