"""Seed P8 upgrade tables with demo data."""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta

from app.database import async_session
from app.models.environment import Environment
from app.models.device_pool import DevicePool, DevicePoolMember, DeviceTag
from app.models.region import Region
from app.models.load_test import TrafficProfile
from app.models.health_score import HealthScoreSnapshot
from app.models.quality_loop import QualityLoopRule
from app.models.device import Device
from app.models.region import RegionMetric


async def seed():
    async with async_session() as db:
        # --- 1. Environments ---
        env_count = (await db.execute(
            __import__('sqlalchemy').select(__import__('sqlalchemy').func.count()).select_from(Environment)
        )).scalar() or 0
        if env_count == 0:
            envs = [
                Environment(
                    name="开发环境", env_type="dev", region="LOCAL",
                    base_url="http://localhost:8100",
                    mqtt_broker_url="mqtt://localhost:1883",
                    db_url="postgresql://mimo:mimo123@localhost:5432/mimo",
                    redis_url="redis://localhost:6379/0",
                    ai_evaluator_url="http://localhost:8000",
                    wiremock_url="http://localhost:8080",
                    payment_endpoint="http://localhost:9090/pay",
                    status="healthy",
                    description="本地开发环境",
                ),
                Environment(
                    name="测试环境", env_type="staging", region="SG",
                    base_url="https://staging-sg.mimo.example.com",
                    mqtt_broker_url="mqtt://staging-mqtt.mimo.example.com:1883",
                    status="healthy",
                    description="新加坡测试环境",
                ),
                Environment(
                    name="生产环境", env_type="prod", region="SG",
                    base_url="https://sg.mimo.example.com",
                    mqtt_broker_url="mqtt://prod-mqtt.mimo.example.com:1883",
                    status="healthy",
                    description="新加坡生产环境",
                ),
            ]
            db.add_all(envs)
            print(f"  + {len(envs)} environments")

        # --- 2. Regions ---
        reg_count = (await db.execute(
            __import__('sqlalchemy').select(__import__('sqlalchemy').func.count()).select_from(Region)
        )).scalar() or 0
        if reg_count == 0:
            regions = [
                Region(code="SG", name="新加坡", status="active", description="东南亚主区"),
                Region(code="US", name="美国", status="active", description="北美区"),
                Region(code="EU", name="欧洲", status="active", description="欧洲区"),
                Region(code="JP", name="日本", status="active", description="日本区"),
            ]
            db.add_all(regions)
            print(f"  + {len(regions)} regions")

        # --- 3. Traffic Profiles ---
        tp_count = (await db.execute(
            __import__('sqlalchemy').select(__import__('sqlalchemy').func.count()).select_from(TrafficProfile)
        )).scalar() or 0
        if tp_count == 0:
            profiles = [
                TrafficProfile(
                    name="早高峰", duration_seconds=300,
                    pattern={"phases": [{"duration_s": 60, "rps": 10}, {"duration_s": 180, "rps": 50}, {"duration_s": 60, "rps": 10}]},
                    description="模拟早 8-9 点购物高峰",
                ),
                TrafficProfile(
                    name="深夜补货", duration_seconds=180,
                    pattern={"phases": [{"duration_s": 180, "rps": 5}]},
                    description="凌晨补货场景，低频稳定",
                ),
                TrafficProfile(
                    name="支付洪峰", duration_seconds=120,
                    pattern={"phases": [{"duration_s": 20, "rps": 100}, {"duration_s": 80, "rps": 200}, {"duration_s": 20, "rps": 50}]},
                    description="模拟支付高峰，高并发短时",
                ),
                TrafficProfile(
                    name="节假日促销", duration_seconds=600,
                    pattern={"phases": [{"duration_s": 120, "rps": 30}, {"duration_s": 360, "rps": 80}, {"duration_s": 120, "rps": 20}]},
                    description="节假日全天持续高流量",
                ),
            ]
            db.add_all(profiles)
            print(f"  + {len(profiles)} traffic profiles")

        # --- 4. Device Pools + Members ---
        pool_count = (await db.execute(
            __import__('sqlalchemy').select(__import__('sqlalchemy').func.count()).select_from(DevicePool)
        )).scalar() or 0
        if pool_count == 0:
            pools = [
                DevicePool(name="新加坡货柜池", pool_type="auto", auto_assign=True, max_devices=20, description="SG 区域自动分配池"),
                DevicePool(name="压力测试专用池", pool_type="manual", auto_assign=False, max_devices=10, description="压测隔离池"),
                DevicePool(name="VIP 高优先级池", pool_type="manual", auto_assign=True, max_devices=5, description="重要客户专用设备"),
            ]
            db.add_all(pools)
            await db.flush()

            # Assign devices to pools
            devices_result = await db.execute(__import__('sqlalchemy').select(Device).limit(20))
            devices = list(devices_result.scalars().all())
            members = []
            for i, dev in enumerate(devices):
                pool_idx = 0 if i < 10 else (1 if i < 15 else 2)
                members.append(DevicePoolMember(pool_id=pools[pool_idx].id, device_id=dev.id))
                # Add tags
                db.add(DeviceTag(device_id=dev.id, tag_key="region", tag_value="SG"))
                db.add(DeviceTag(device_id=dev.id, tag_key="env", tag_value="staging"))
                if i < 5:
                    db.add(DeviceTag(device_id=dev.id, tag_key="priority", tag_value="high"))
            db.add_all(members)
            print(f"  + {len(pools)} device pools, {len(members)} members, {len(devices) * 2} tags")

        # --- 5. Health Score Snapshots (7-day trend) ---
        hs_count = (await db.execute(
            __import__('sqlalchemy').select(__import__('sqlalchemy').func.count()).select_from(HealthScoreSnapshot)
        )).scalar() or 0
        if hs_count == 0:
            snapshots = []
            base_score = 82.0
            for i in range(7):
                day = datetime.utcnow() - timedelta(days=6 - i)
                score = base_score + random.uniform(-3, 5)
                score = round(min(100, max(0, score)), 1)
                snapshots.append(HealthScoreSnapshot(
                    overall_score=score,
                    dimensions={
                        "pass_rate": {"name": "用例通过率", "value": round(score + random.uniform(-2, 2), 1)},
                        "ai_accuracy": {"name": "AI 识别准确率", "value": round(score + random.uniform(-5, 3), 1)},
                        "payment_success": {"name": "支付成功率", "value": round(min(100, score + random.uniform(0, 5)), 1)},
                        "device_online": {"name": "设备在线率", "value": round(min(100, 75 + random.uniform(0, 20)), 1)},
                        "mqtt_latency": {"name": "MQTT P99 延迟", "value": round(random.uniform(80, 100), 1)},
                        "crash_rate": {"name": "崩溃率", "value": round(random.uniform(85, 98), 1)},
                        "flaky_ratio": {"name": "Flaky 比例", "value": round(random.uniform(88, 99), 1)},
                    },
                    release_allowed=score >= 80,
                    computed_at=day,
                ))
                base_score = score
            db.add_all(snapshots)
            print(f"  + {len(snapshots)} health score snapshots")

        # --- 6. Quality Loop Rule ---
        qlr_count = (await db.execute(
            __import__('sqlalchemy').select(__import__('sqlalchemy').func.count()).select_from(QualityLoopRule)
        )).scalar() or 0
        if qlr_count == 0:
            rules = [
                QualityLoopRule(
                    name="健康分低于 80 自动创建缺陷",
                    trigger_metric="health_score",
                    threshold=80.0,
                    operator="<",
                    action_chain={"actions": [
                        {"type": "create_defect", "params": {}},
                        {"type": "assign_defect", "params": {}},
                    ]},
                    enabled=True,
                ),
                QualityLoopRule(
                    name="Flaky 用例超过 5 个触发回归",
                    trigger_metric="flaky_rate",
                    threshold=5.0,
                    operator=">",
                    action_chain={"actions": [
                        {"type": "create_defect", "params": {}},
                        {"type": "trigger_regression", "params": {}},
                    ]},
                    enabled=True,
                ),
            ]
            db.add_all(rules)
            print(f"  + {len(rules)} quality loop rules")

        # --- 7. Region Metrics ---
        rm_count = (await db.execute(
            __import__('sqlalchemy').select(__import__('sqlalchemy').func.count()).select_from(RegionMetric)
        )).scalar() or 0
        if rm_count == 0:
            region_metrics = []
            for code in ['SG', 'US', 'EU', 'JP']:
                base = random.uniform(78, 92)
                region_metrics.extend([
                    RegionMetric(region_code=code, metric_name='health_score', metric_value=round(base, 1)),
                    RegionMetric(region_code=code, metric_name='device_online_rate', metric_value=round(min(100, base + random.uniform(2, 8)), 1)),
                    RegionMetric(region_code=code, metric_name='pass_rate', metric_value=round(min(100, base + random.uniform(-3, 5)), 1)),
                    RegionMetric(region_code=code, metric_name='payment_success_rate', metric_value=round(min(100, base + random.uniform(0, 6)), 1)),
                ])
            db.add_all(region_metrics)
            print(f"  + {len(region_metrics)} region metrics")

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
