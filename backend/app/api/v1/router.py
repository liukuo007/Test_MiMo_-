from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, users, projects, devices, test_cases, test_tasks, test_results, ai_verify, traces, dashboard, quality_gate, quality_report, datasets, settings, defects, webhooks, schedules, simulator, metersphere, smoke_test, scenarios, health_score, environments, device_mesh, stability, ai_copilot, quality_loop, regions, load_test, scenario_ai

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目管理"])
api_router.include_router(devices.router, prefix="/devices", tags=["设备管理"])
api_router.include_router(test_cases.router, prefix="/test-cases", tags=["用例管理"])
api_router.include_router(test_tasks.router, prefix="/test-tasks", tags=["任务编排"])
api_router.include_router(test_results.router, prefix="/test-results", tags=["测试结果"])
api_router.include_router(ai_verify.router, prefix="/ai", tags=["AI验证"])
api_router.include_router(traces.router, prefix="/traces", tags=["链路追踪"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["数据看板"])
api_router.include_router(quality_gate.router, prefix="/quality-gate", tags=["质量门禁"])
api_router.include_router(quality_report.router, prefix="/quality-reports", tags=["质量报告"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["数据集管理"])
api_router.include_router(settings.router, prefix="/settings", tags=["系统设置"])
api_router.include_router(defects.router, prefix="/defects", tags=["缺陷管理"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["CI/CD集成"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["定时任务"])
api_router.include_router(simulator.router, prefix="/simulator", tags=["Locust 压测"])
api_router.include_router(metersphere.router, prefix="/metersphere", tags=["MeterSphere 集成"])
api_router.include_router(smoke_test.router, prefix="/smoke-test", tags=["冒烟测试"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["场景工作台"])
api_router.include_router(health_score.router, prefix="/health-score", tags=["质量健康分"])
api_router.include_router(environments.router, prefix="/environments", tags=["环境治理"])
api_router.include_router(device_mesh.router, prefix="/device-mesh", tags=["设备网格"])
api_router.include_router(stability.router, prefix="/stability", tags=["稳定性治理"])
api_router.include_router(ai_copilot.router, prefix="/ai-copilot", tags=["AI助手"])
api_router.include_router(quality_loop.router, prefix="/quality-loop", tags=["质量闭环"])
api_router.include_router(regions.router, prefix="/regions", tags=["全球运营"])
api_router.include_router(load_test.router, prefix="/load-test", tags=["压测中心"])
api_router.include_router(scenario_ai.router, prefix="/scenario-ai", tags=["场景AI"])
