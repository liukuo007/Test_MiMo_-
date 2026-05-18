"""初始化测试数据 - 丰富的演示数据"""
import asyncio
import random
from datetime import datetime, timedelta

from app.database import engine, async_session, Base
from app.models.user import User, UserRole
from app.models.project import Project, Environment
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.test_case import TestCase, TestType, Priority
from app.models.test_task import TestTask, TestTaskStep, TaskStatus, TriggerType
from app.models.test_result import TestResult
from app.models.ai_model import AIModel, AIModelVersion, AIEvaluation
from app.models.trace import Trace, TraceSpan
from app.models.defect import Defect, DefectStatus, DefectPriority, DefectSource
from app.models.device_event import DeviceEvent, DeviceEventType
from app.models.schedule import Schedule
from app.models.dataset import Dataset, DatasetType
from app.models.setting import SystemSetting
from app.models.quality_gate import QualityGateRule
from app.models.quality_report import QualityReport
from app.core.security import hash_password


async def _seed_new_tables(db, now):
    """填充 datasets, system_settings, quality_gate_rules, quality_reports 表"""
    # ===== 数据集 =====
    dataset_defs = [
        ("sku-dataset-v3-large", DatasetType.SKU_IMAGES, "大规模 SKU 商品图片数据集", 2000, 12, 1288490188, "coco"),
        ("sku-dataset-v3-medium", DatasetType.SKU_IMAGES, "中等规模 SKU 数据集", 500, 12, 335544320, "coco"),
        ("sku-dataset-v3-small", DatasetType.SKU_IMAGES, "小规模快速验证数据集", 100, 12, 68157440, "coco"),
        ("face-dataset-v1", DatasetType.FACE_IMAGES, "人脸检测数据集", 800, 50, 471859200, "voc"),
        ("gesture-dataset-v1", DatasetType.GESTURE_VIDEOS, "手势识别视频数据集", 200, 5, 2254857830, "yolo"),
    ]
    for name, dtype, desc, samples, classes, size, fmt in dataset_defs:
        db.add(Dataset(
            name=name, type=dtype, description=desc,
            sample_count=samples, class_count=classes, size_bytes=size,
            annotation_format=fmt, project_id=1, created_by=1,
        ))

    # ===== 系统设置 =====
    settings_defs = {
        "basic": {"name": "MiMo - 智能货柜全链路测试平台", "description": "智能货柜质量基础设施", "default_env": "dev", "timezone": "Asia/Shanghai"},
        "notify": {"email_enabled": True, "smtp_host": "smtp.mimo.local", "smtp_from": "noreply@mimo.local", "webhook_enabled": False, "webhook_url": "", "events": ["task_completed", "task_failed"]},
        "engine": {"api_timeout": 30, "iot_max_concurrent": 1000, "ai_device": "cuda", "web_engine_type": "playwright", "appium_url": "http://localhost:4723"},
    }
    for category, values in settings_defs.items():
        db.add(SystemSetting(key=category, value=values, category=category, description=f"{category} 配置"))

    # ===== 质量门禁规则 =====
    gate_rules = [
        ("自动化用例通过率", "auto_pass_rate", 95, "gte"),
        ("自动化覆盖率", "auto_coverage", 80, "gte"),
        ("AI 识别准确率", "ai_accuracy", 95, "gte"),
        ("AI 推理延迟", "ai_latency_max", 50, "lte"),
        ("API P99 响应时间", "api_p99_ms", 2000, "lte"),
        ("设备在线率", "device_online_rate", 99, "gte"),
        ("缺陷逃逸率", "defect_escape_rate", 2, "lte"),
        ("发布成功率", "release_success_rate", 98, "gte"),
    ]
    for name, metric, threshold, op in gate_rules:
        db.add(QualityGateRule(name=name, metric=metric, threshold=threshold, operator=op))

    # ===== 质量报告 =====
    db.add(QualityReport(
        name=f"{now.year}-W{now.isocalendar()[1]-1:02d} 周质量报告",
        report_type="weekly", overall_score=86.5, pass_rate=92.3,
        defect_escape_rate=1.8, release_success_rate=95.0,
        device_online_rate=91.7, ai_accuracy=96.2,
        dimensions=[
            {"name": "自动化覆盖率", "score": 83.1, "trend": "up", "detail": "通过率 92.3%"},
            {"name": "AI 识别准确率", "score": 96.2, "trend": "up", "detail": "准确率 96.2%"},
            {"name": "缺陷逃逸率", "score": 91.0, "trend": "up", "detail": "逃逸率 1.8%"},
            {"name": "发布成功率", "score": 95.0, "trend": "stable", "detail": "成功率 95.0%"},
            {"name": "设备稳定性", "score": 91.7, "trend": "stable", "detail": "在线率 91.7%"},
        ],
        summary={"overall_score": 86.5, "pass_rate": 92.3, "ai_accuracy": 96.2, "defect_escape_rate": 1.8, "release_success_rate": 95.0, "device_online_rate": 91.7},
        project_id=1,
    ))

    await db.flush()
    print("New tables seeded: datasets, system_settings, quality_gate_rules, quality_reports")


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 检查是否已有数据
        from sqlalchemy import select, func
        now = datetime.now()
        count_result = await db.execute(select(func.count(User.id)))
        user_count = count_result.scalar()
        if user_count and user_count > 0:
            # 检查新表是否有数据
            ds_count = (await db.execute(select(func.count(Dataset.id)))).scalar() or 0
            if ds_count > 0:
                print("Seed data already exists, skipping.")
                return
            else:
                print("Core data exists, seeding new tables...")
                await _seed_new_tables(db, now)
                await db.commit()
                print("Done!")
                return
        # ===== 用户 =====
        users = [
            User(username="admin", email="admin@mimo.local", hashed_password=hash_password("admin123"),
                 full_name="张伟", role=UserRole.ADMIN),
            User(username="qa_lead", email="qalead@mimo.local", hashed_password=hash_password("qa123"),
                 full_name="李娜", role=UserRole.QA_LEAD),
            User(username="qa_wang", email="wang@mimo.local", hashed_password=hash_password("qa123"),
                 full_name="王强", role=UserRole.QA),
            User(username="qa_liu", email="liu@mimo.local", hashed_password=hash_password("qa123"),
                 full_name="刘芳", role=UserRole.QA),
            User(username="dev_chen", email="chen@mimo.local", hashed_password=hash_password("dev123"),
                 full_name="陈明", role=UserRole.DEVELOPER),
            User(username="algo_zhao", email="zhao@mimo.local", hashed_password=hash_password("algo123"),
                 full_name="赵磊", role=UserRole.ALGORITHM),
            User(username="ops_sun", email="sun@mimo.local", hashed_password=hash_password("ops123"),
                 full_name="孙涛", role=UserRole.OPS),
        ]
        for u in users:
            db.add(u)
        await db.flush()

        # ===== 项目 =====
        projects = [
            Project(name="智能货柜-V3 升级", description="第三代智能货柜全链路测试，涵盖 AI 识别、IoT 设备、支付流程",
                    environment=Environment.DEV, owner_id=1),
            Project(name="智能货柜-华东区", description="华东区域货柜部署前回归测试",
                    environment=Environment.STAGING, owner_id=2),
            Project(name="智能货柜-压力测试", description="大规模并发压力测试项目",
                    environment=Environment.DEV, owner_id=1),
            Project(name="智能货柜-生产巡检", description="生产环境日常巡检与回归",
                    environment=Environment.PROD, owner_id=2),
        ]
        for p in projects:
            db.add(p)
        await db.flush()

        # ===== 设备 =====
        device_names = [
            ("上海-陆家嘴-001", "cn-sh", DeviceStatus.ONLINE),
            ("上海-南京路-002", "cn-sh", DeviceStatus.ONLINE),
            ("北京-中关村-003", "cn-bj", DeviceStatus.OCCUPIED),
            ("北京-望京-004", "cn-bj", DeviceStatus.ONLINE),
            ("深圳-南山-005", "cn-sz", DeviceStatus.ONLINE),
            ("深圳-福田-006", "cn-sz", DeviceStatus.OFFLINE),
            ("杭州-西湖-007", "cn-hz", DeviceStatus.ONLINE),
            ("杭州-滨江-008", "cn-hz", DeviceStatus.FAULT),
            ("广州-天河-009", "cn-gz", DeviceStatus.ONLINE),
            ("成都-高新-010", "cn-cd", DeviceStatus.ONLINE),
            ("新加坡-011", "sea-sg", DeviceStatus.ONLINE),
            ("曼谷-012", "sea-bkk", DeviceStatus.MAINTENANCE),
        ]
        devices = []
        for i, (name, region, status) in enumerate(device_names):
            d = Device(
                name=name, device_sn=f"MC-{region.upper()}-{i+1:04d}",
                device_type=DeviceType.REAL, status=status, region=region.split("-")[0],
                firmware_version=random.choice(["3.2.1", "3.3.0", "3.4.0-beta"]),
                ip_address=f"192.168.{random.randint(1,10)}.{random.randint(1,254)}",
                temperature=round(random.uniform(18.0, 35.0), 1),
                project_id=random.choice([1, 2]),
                occupied_by=3 if status == DeviceStatus.OCCUPIED else None,
                last_heartbeat=datetime.now() - timedelta(seconds=random.randint(0, 300)),
            )
            db.add(d)
            devices.append(d)

        # 虚拟设备
        for i in range(8):
            d = Device(
                name=f"虚拟设备-L2-{i+1:03d}", device_sn=f"VIR-CN-{random.randint(10000000, 99999999)}",
                device_type=DeviceType.VIRTUAL_L2, status=DeviceStatus.ONLINE, region="cn",
                firmware_version="virtual", temperature=round(random.uniform(20.0, 28.0), 1),
                project_id=1,
            )
            db.add(d)
            devices.append(d)
        await db.flush()

        # ===== 测试用例 =====
        case_defs = [
            ("货柜开门-正常流程", TestType.IOT, Priority.P0, "设备控制",
             {"steps": [{"action": "send_command", "cmd": "door_open"}, {"action": "wait_state", "state": "door_opened"}]}),
            ("货柜关门-正常流程", TestType.IOT, Priority.P0, "设备控制",
             {"steps": [{"action": "send_command", "cmd": "door_close"}, {"action": "wait_state", "state": "idle"}]}),
            ("AI 识别-可口可乐", TestType.AI, Priority.P0, "AI识别",
             {"steps": [{"action": "capture_image"}, {"action": "ai_recognize", "expected": "可口可乐330ml"}]}),
            ("AI 识别-农夫山泉", TestType.AI, Priority.P0, "AI识别",
             {"steps": [{"action": "capture_image"}, {"action": "ai_recognize", "expected": "农夫山泉550ml"}]}),
            ("AI 识别-批量测试", TestType.AI, Priority.P1, "AI识别",
             {"steps": [{"action": "batch_recognize", "count": 100}]}),
            ("支付接口-微信支付", TestType.API, Priority.P0, "支付模块",
             {"steps": [{"method": "POST", "path": "/api/payment/create", "body": {"amount": 500, "channel": "wechat"}}]}),
            ("支付接口-支付宝", TestType.API, Priority.P0, "支付模块",
             {"steps": [{"method": "POST", "path": "/api/payment/create", "body": {"amount": 500, "channel": "alipay"}}]}),
            ("订单查询接口", TestType.API, Priority.P1, "订单模块",
             {"steps": [{"method": "GET", "path": "/api/orders/latest"}]}),
            ("库存同步接口", TestType.API, Priority.P1, "库存模块",
             {"steps": [{"method": "GET", "path": "/api/inventory/sync"}]}),
            ("用户登录-Web端", TestType.WEB, Priority.P1, "Web管理",
             {"steps": [{"action": "navigate", "url": "/login"}, {"action": "fill", "selector": "#username"}, {"action": "click", "selector": "#login-btn"}]}),
            ("设备管理-Web端", TestType.WEB, Priority.P2, "Web管理",
             {"steps": [{"action": "navigate", "url": "/devices"}, {"action": "assert", "selector": ".device-list"}]}),
            ("App扫码开门", TestType.APP, Priority.P0, "移动端",
             {"steps": [{"action": "tap", "locator": "#scan-btn"}, {"action": "wait", "ms": 2000}]}),
            ("App支付完成", TestType.APP, Priority.P1, "移动端",
             {"steps": [{"action": "tap", "locator": "#pay-btn"}, {"action": "assert", "locator": "#pay-success"}]}),
            ("端到端-完整购物", TestType.E2E, Priority.P0, "端到端",
             {"steps": [{"action": "open_door"}, {"action": "take_item"}, {"action": "close_door"}, {"action": "verify_payment"}]}),
            ("端到端-多商品", TestType.E2E, Priority.P1, "端到端",
             {"steps": [{"action": "open_door"}, {"action": "take_items", "count": 3}, {"action": "close_door"}]}),
            ("网络延迟-设备响应", TestType.IOT, Priority.P2, "异常场景",
             {"steps": [{"action": "inject_fault", "type": "network_latency", "severity": 5}]}),
            ("断电恢复测试", TestType.IOT, Priority.P2, "异常场景",
             {"steps": [{"action": "inject_fault", "type": "device_crash"}, {"action": "wait_recovery"}]}),
        ]

        cases = []
        for i, (name, test_type, priority, module, steps) in enumerate(case_defs):
            c = TestCase(
                name=name, test_type=test_type, priority=priority, module=module,
                steps=steps, expected_result="所有步骤执行通过",
                tags=["自动化", module], project_id=(i % 4) + 1,
                created_by=random.choice([1, 2, 3, 4]),
            )
            db.add(c)
            cases.append(c)
        await db.flush()

        # ===== 测试任务 =====
        task_defs = [
            ("每日回归-V3开发", TaskStatus.PASSED, "dev", TriggerType.CRON, 1, now - timedelta(hours=6)),
            ("华东区预发布验证", TaskStatus.RUNNING, "staging", TriggerType.MANUAL, 2, now - timedelta(hours=1)),
            ("压力测试-1000设备", TaskStatus.PASSED, "dev", TriggerType.MANUAL, 3, now - timedelta(days=1)),
            ("生产巡检-2026W19", TaskStatus.PASSED, "prod", TriggerType.CRON, 4, now - timedelta(days=2)),
            ("AI模型评测-v3.0", TaskStatus.PASSED, "dev", TriggerType.MANUAL, 1, now - timedelta(hours=12)),
            ("支付流程回归", TaskStatus.FAILED, "staging", TriggerType.CI_CD, 2, now - timedelta(hours=3)),
            ("混沌测试-网络故障", TaskStatus.PASSED, "dev", TriggerType.MANUAL, 1, now - timedelta(hours=8)),
            ("App 自动化冒烟", TaskStatus.PENDING, "dev", TriggerType.WEBHOOK, 1, now - timedelta(minutes=30)),
        ]

        tasks = []
        for i, (name, status, env, trigger, proj_id, started) in enumerate(task_defs):
            finished = started + timedelta(minutes=random.randint(5, 60)) if status != TaskStatus.RUNNING else None
            t = TestTask(
                name=name, status=status, environment=env, trigger_type=trigger,
                branch=random.choice(["main", "develop", "feature/v3-ai"]),
                description=f"任务描述: {name}",
                project_id=proj_id, created_by=random.choice([1, 2, 3]),
                started_at=started, finished_at=finished,
                dag_config={"nodes": [], "edges": []},
            )
            db.add(t)
            tasks.append(t)
        await db.flush()

        # ===== 任务步骤 =====
        for t in tasks:
            step_names = ["环境检查", "设备连接", "用例执行", "结果验证", "报告生成"]
            for j, sname in enumerate(step_names):
                step_status = TaskStatus.PASSED if t.status == TaskStatus.PASSED else (
                    TaskStatus.RUNNING if j == 2 and t.status == TaskStatus.RUNNING else
                    TaskStatus.FAILED if j == 2 and t.status == TaskStatus.FAILED else TaskStatus.PASSED
                )
                step = TestTaskStep(
                    task_id=t.id, name=sname, step_type=["api", "iot", "api", "assert", "wait"][j],
                    status=step_status, order=j + 1,
                    config={}, result={"status": step_status.value},
                    started_at=t.started_at + timedelta(minutes=j * 2) if t.started_at else None,
                    finished_at=t.started_at + timedelta(minutes=j * 2 + 1) if t.started_at and step_status != TaskStatus.RUNNING else None,
                )
                db.add(step)

        # ===== 测试结果 =====
        result_statuses = ["passed", "passed", "passed", "passed", "failed", "passed", "passed", "passed", "failed", "passed"]
        for t in tasks:
            if t.status in (TaskStatus.PASSED, TaskStatus.FAILED):
                for k in range(random.randint(8, 15)):
                    case = random.choice(cases)
                    is_failed = (k == 4 or k == 8) and t.status == TaskStatus.FAILED
                    r = TestResult(
                        task_id=t.id, test_case_id=case.id,
                        status="failed" if is_failed else "passed",
                        duration_ms=random.randint(200, 8000),
                        error_message="断言失败: AI 识别结果不匹配" if is_failed else None,
                        trace_id=f"trace-{t.id}-{k:04d}",
                        device_sn=random.choice(devices).device_sn if devices else None,
                        ai_result={
                            "accuracy": round(random.uniform(0.85, 0.99), 3),
                            "predicted": "可口可乐330ml" if not is_failed else "百事可乐330ml",
                            "confidence": round(random.uniform(0.7, 0.99), 3),
                        },
                        metadata_={"environment": t.environment, "branch": t.branch},
                    )
                    db.add(r)

        # ===== AI 模型 =====
        models = [
            AIModel(name="SKU-识别模型", description="基于 YOLOv8 的货柜商品识别模型", model_type="yolov8", created_by=6),
            AIModel(name="人脸检测模型", description="用户身份验证人脸检测", model_type="retinaface", created_by=6),
            AIModel(name="手势识别模型", description="用户取货手势识别", model_type="mediapipe", created_by=6),
        ]
        for m in models:
            db.add(m)
        await db.flush()

        versions = [
            AIModelVersion(model_id=1, version="v2.0", path="/models/sku/v2.0", metrics={"accuracy": 0.95, "recall": 0.93}, is_active=False),
            AIModelVersion(model_id=1, version="v2.1", path="/models/sku/v2.1", metrics={"accuracy": 0.96, "recall": 0.94}, is_active=False),
            AIModelVersion(model_id=1, version="v3.0", path="/models/sku/v3.0", metrics={"accuracy": 0.97, "recall": 0.96}, is_active=True),
            AIModelVersion(model_id=2, version="v1.0", path="/models/face/v1.0", metrics={"accuracy": 0.98}, is_active=True),
            AIModelVersion(model_id=2, version="v1.1", path="/models/face/v1.1", metrics={"accuracy": 0.985}, is_active=False),
            AIModelVersion(model_id=3, version="v1.0", path="/models/gesture/v1.0", metrics={"accuracy": 0.92}, is_active=True),
        ]
        for v in versions:
            db.add(v)
        await db.flush()

        # ===== AI 评测记录 =====
        for v in versions[:3]:
            for dataset in ["small", "medium", "large"]:
                base_acc = v.metrics.get("accuracy", 0.9) if v.metrics else 0.9
                ev = AIEvaluation(
                    model_version_id=v.id, dataset_name=dataset,
                    accuracy=round(base_acc + random.gauss(0, 0.01), 4),
                    recall=round(base_acc - 0.02 + random.gauss(0, 0.01), 4),
                    f1_score=round(base_acc - 0.01 + random.gauss(0, 0.01), 4),
                    avg_latency_ms=round(35 + random.gauss(0, 5), 2),
                    total_samples={"small": 100, "medium": 500, "large": 2000}[dataset],
                    failed_samples=random.randint(3, 30),
                )
                db.add(ev)

        # ===== 链路追踪 =====
        services = ["api-gateway", "device-service", "ai-service", "payment-service", "order-service"]
        operations = ["HTTP GET", "HTTP POST", "MQTT Publish", "DB Query", "AI Inference", "Redis Get"]
        for i in range(20):
            trace_id = f"trace-{random.randint(100000, 999999)}"
            svc = random.choice(services)
            op = random.choice(operations)
            duration = random.randint(50, 5000)
            status = random.choice(["ok", "ok", "ok", "ok", "error"])
            started = now - timedelta(hours=random.randint(0, 72))

            trace = Trace(
                trace_id=trace_id, service=svc, operation=op,
                status=status, duration_ms=duration,
                tags={"env": random.choice(["dev", "staging"]), "version": "3.0.0"},
                started_at=started, finished_at=started + timedelta(milliseconds=duration),
            )
            db.add(trace)
            await db.flush()

            # 为每个 trace 创建 span
            span_count = random.randint(3, 8)
            parent_id = None
            for j in range(span_count):
                span_svc = services[j % len(services)]
                span_op = operations[j % len(operations)]
                span_dur = random.randint(5, duration // span_count)
                span = TraceSpan(
                    trace_id=trace_id,
                    span_id=f"span-{trace_id}-{j:03d}",
                    parent_span_id=parent_id,
                    service=span_svc, operation=span_op,
                    status=status if j > 0 or random.random() > 0.2 else "error",
                    duration_ms=span_dur,
                    tags={"component": span_svc},
                    logs=[],
                    started_at=started + timedelta(milliseconds=j * span_dur),
                    finished_at=started + timedelta(milliseconds=(j + 1) * span_dur),
                )
                db.add(span)
                parent_id = span.span_id

        # ===== 设备事件 =====
        event_messages = {
            DeviceEventType.HEARTBEAT: ["设备心跳正常", "心跳检测完成"],
            DeviceEventType.INFO: ["固件版本更新至 3.4.0", "用户完成一次购物流程", "库存同步完成", "温度传感器校准完成"],
            DeviceEventType.WARNING: ["温度偏高: 34.2°C", "网络延迟偏高: 800ms", "库存不足: 剩余 2 件", "CPU 使用率超过 80%"],
            DeviceEventType.ERROR: ["网络延迟超过阈值 (2000ms)", "传感器读取失败", "支付网关连接超时", "AI 推理超时"],
            DeviceEventType.CONTROL: ["开门指令执行成功", "重启指令已发送", "固件更新指令已下发"],
            DeviceEventType.FAULT: ["设备离线告警", "温度传感器故障", "门锁异常"],
        }
        for d in devices:
            for _ in range(random.randint(8, 20)):
                evt_type = random.choice(list(DeviceEventType))
                msg = random.choice(event_messages[evt_type])
                evt = DeviceEvent(
                    device_id=d.id,
                    event_type=evt_type,
                    message=msg,
                    details={"source": "seed", "auto": evt_type in (DeviceEventType.HEARTBEAT,)},
                    created_at=now - timedelta(hours=random.randint(0, 72), minutes=random.randint(0, 59)),
                )
                db.add(evt)

        # ===== 缺陷 =====
        defect_defs = [
            ("AI 识别准确率下降至 85%", "v3.0 模型在特定光照条件下识别准确率下降", DefectPriority.P0, DefectStatus.IN_PROGRESS, DefectSource.AUTO),
            ("支付回调延迟超过 5 秒", "微信支付回调响应时间不稳定", DefectPriority.P1, DefectStatus.FIXED, DefectSource.TEST),
            ("设备重启后库存数据丢失", "断电恢复后库存数量未正确同步", DefectPriority.P0, DefectStatus.NEW, DefectSource.MONITOR),
            ("App 扫码偶发失败", "约 5% 概率扫码识别失败需要重试", DefectPriority.P1, DefectStatus.IN_PROGRESS, DefectSource.USER),
            ("Web 管理页面加载缓慢", "设备列表超过 1000 台时页面加载超过 3 秒", DefectPriority.P2, DefectStatus.CLOSED, DefectSource.TEST),
            ("温度传感器数据异常", "杭州-滨江设备温度读数持续偏高", DefectPriority.P1, DefectStatus.FIXED, DefectSource.MONITOR),
            ("订单并发冲突", "同一设备同时生成两个订单", DefectPriority.P0, DefectStatus.REOPENED, DefectSource.AUTO),
            ("短信验证码发送失败", "海外设备短信网关偶发超时", DefectPriority.P2, DefectStatus.NEW, DefectSource.TEST),
            ("SSO Token 过期处理异常", "Token 过期后未正确跳转登录页", DefectPriority.P2, DefectStatus.IN_PROGRESS, DefectSource.USER),
            ("DAG 编排器并发执行 bug", "并行节点执行时存在竞态条件", DefectPriority.P1, DefectStatus.FIXED, DefectSource.AUTO),
        ]
        for title, desc, priority, status, source in defect_defs:
            d = Defect(
                title=title, description=desc, priority=priority, status=status, source=source,
                device_sn=random.choice(devices).device_sn if source == DefectSource.MONITOR else None,
                test_case_id=random.choice(cases).id if source in (DefectSource.TEST, DefectSource.AUTO) else None,
                assigned_to=random.choice([3, 4, 5]),
                created_by=random.choice([1, 2, 3, 4]),
                screenshot_url="https://via.placeholder.com/800x600?text=Screenshot" if random.random() > 0.5 else None,
                tags={"module": random.choice(["AI识别", "支付模块", "设备控制", "Web管理"])},
                resolved_at=now - timedelta(hours=random.randint(1, 48)) if status in (DefectStatus.FIXED, DefectStatus.CLOSED) else None,
                closed_at=now - timedelta(hours=random.randint(0, 24)) if status == DefectStatus.CLOSED else None,
            )
            db.add(d)

        # ===== 定时任务 =====
        schedule_defs = [
            ("每日回归测试", 1, "0 9 * * *"),
            ("工作日冒烟测试", 1, "0 10 * * 1-5"),
            ("周末压力测试", 3, "0 2 * * 6,0"),
        ]
        for name, task_idx, cron in schedule_defs:
            s = Schedule(
                name=name,
                task_id=tasks[task_idx].id,
                cron_expression=cron,
                is_active=True,
                next_run_at=now + timedelta(hours=random.randint(1, 24)),
                created_by=1,
            )
            db.add(s)

        await _seed_new_tables(db, now)
        await db.commit()
        print("=" * 50)
        print("Seed data created successfully!")
        print(f"  Users: {len(users)}")
        print(f"  Projects: {len(projects)}")
        print(f"  Devices: {len(devices)}")
        print(f"  Test Cases: {len(cases)}")
        print(f"  Test Tasks: {len(tasks)}")
        print(f"  AI Models: {len(models)}")
        print(f"  AI Versions: {len(versions)}")
        print(f"  Defects: {len(defect_defs)}")
        print(f"  Device Events: ~{len(devices) * 14}")
        print(f"  Schedules: {len(schedule_defs)}")
        print(f"  Traces: 20")
        print(f"  Datasets: {len(dataset_defs)}")
        print(f"  Settings: {len(settings_defs)}")
        print(f"  Quality Gate Rules: {len(gate_rules)}")
        print(f"  Quality Reports: 1")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
