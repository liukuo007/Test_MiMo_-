"""
Locust 分布式压测 — 模拟 20 万台 IoT 智能货柜高并发场景

运行方式:
  单机:   locust -f locustfile.py --host http://localhost:8100
  分布式: locust -f locustfile.py --master --host http://localhost:8100
          locust -f locustfile.py --worker --master-host=<master-ip>

Web UI: http://localhost:8089
"""

from __future__ import annotations

import json
import random
import time
import uuid

from locust import HttpUser, task, between, events, tag


# ── 设备池配置 ──────────────────────────────────────────────
DEVICE_PREFIXES = [
    "MC-CN-SH", "MC-CN-BJ", "MC-CN-GZ", "MC-CN-SZ",
    "MC-US-LA", "MC-US-NY", "MC-JP-TK", "MC-UK-LD",
]
REGIONS = ["cn-east", "cn-south", "cn-north", "us-west", "us-east", "jp-tokyo", "eu-london"]
FIRMWARE_VERSIONS = ["v1.0.3", "v1.1.0", "v1.2.1", "v2.0.0", "v2.1.0"]
DEVICE_TYPES = ["smart_cabinet", "smart_fridge", "smart_locker"]


def generate_device_sn() -> str:
    prefix = random.choice(DEVICE_PREFIXES)
    suffix = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{suffix}"


# ── 货柜用户行为 ──────────────────────────────────────────
class SmartCabinetUser(HttpUser):
    """模拟一台智能货柜的完整生命周期行为"""
    wait_time = between(5, 30)
    abstract = False

    def on_start(self):
        self.device_sn = generate_device_sn()
        self.region = random.choice(REGIONS)
        self.firmware = random.choice(FIRMWARE_VERSIONS)
        self.device_type = random.choice(DEVICE_TYPES)
        self.token = None
        self._login()
        self._register_device()

    def _login(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123",
        }, name="/api/v1/auth/login")
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    def _auth_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _register_device(self):
        self.client.post(
            "/api/v1/devices/virtual",
            json=[{
                "device_sn": self.device_sn,
                "name": f"压测货柜-{self.device_sn[-8:]}",
                "device_type": self.device_type,
                "region": self.region,
                "firmware_version": self.firmware,
            }],
            headers=self._auth_headers(),
            name="/api/v1/devices/virtual [register]",
        )

    # ── 核心任务: 心跳（高频） ──
    @tag("heartbeat")
    @task(10)
    def heartbeat(self):
        self.client.post(
            "/api/v1/devices/virtual/heartbeat",
            json={
                "device_sn": self.device_sn,
                "status": random.choice(["online", "online", "online", "occupied"]),
                "temperature": round(random.uniform(18.0, 35.0), 1),
            },
            headers=self._auth_headers(),
            name="/api/v1/devices/virtual/heartbeat",
        )

    # ── 核心任务: 开门事件 ──
    @tag("event")
    @task(5)
    def door_open_event(self):
        self.client.post(
            "/api/v1/devices/virtual/event",
            json={
                "device_sn": self.device_sn,
                "event_type": "door_open",
                "message": f"用户扫码开门, 设备={self.device_sn}",
            },
            headers=self._auth_headers(),
            name="/api/v1/devices/virtual/event [door_open]",
        )

    # ── 核心任务: 取货+AI识别 ──
    @tag("event")
    @task(3)
    def item_pickup_event(self):
        sku = f"SKU-{random.randint(10000, 99999)}"
        self.client.post(
            "/api/v1/devices/virtual/event",
            json={
                "device_sn": self.device_sn,
                "event_type": "item_detected",
                "message": json.dumps({
                    "action": "pickup",
                    "sku": sku,
                    "confidence": round(random.uniform(0.85, 0.99), 3),
                    "bbox": [120, 80, 200, 180],
                }),
            },
            headers=self._auth_headers(),
            name="/api/v1/devices/virtual/event [item_pickup]",
        )

    # ── 核心任务: 关门结算 ──
    @tag("event")
    @task(3)
    def door_close_event(self):
        self.client.post(
            "/api/v1/devices/virtual/event",
            json={
                "device_sn": self.device_sn,
                "event_type": "door_close",
                "message": f"关门结算完成, 设备={self.device_sn}",
            },
            headers=self._auth_headers(),
            name="/api/v1/devices/virtual/event [door_close]",
        )

    # ── 设备控制指令 ──
    @tag("control")
    @task(1)
    def heartbeat_check(self):
        self.client.post(
            f"/api/v1/devices/{self.device_sn}/control",
            json={"command": "heartbeat"},
            headers=self._auth_headers(),
            name="/api/v1/devices/{sn}/control [heartbeat]",
        )

    # ── 查询 Dashboard ──
    @tag("dashboard")
    @task(2)
    def check_dashboard(self):
        self.client.get(
            "/api/v1/dashboard/overview",
            headers=self._auth_headers(),
            name="/api/v1/dashboard/overview",
        )

    # ── 查询设备列表 ──
    @tag("query")
    @task(2)
    def list_devices(self):
        self.client.get(
            "/api/v1/devices?limit=20",
            headers=self._auth_headers(),
            name="/api/v1/devices [list]",
        )


# ── 高并发压测用户（模拟瞬时大量请求） ──────────────────
class BurstUser(HttpUser):
    """模拟突发流量 — 大量货柜同时上报"""
    wait_time = between(0.5, 2)
    weight = 3

    def on_start(self):
        self.device_sn = generate_device_sn()
        self.token = None
        resp = self.client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "admin123",
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    @tag("burst")
    @task
    def rapid_heartbeat(self):
        self.client.post(
            "/api/v1/devices/virtual/heartbeat",
            json={
                "device_sn": self.device_sn,
                "status": "online",
                "temperature": round(random.uniform(20.0, 30.0), 1),
            },
            headers=self._headers(),
            name="/api/v1/devices/virtual/heartbeat [burst]",
        )


# ── 统计钩子 ──────────────────────────────────────────────
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("MiMo IoT 压测启动")
    print(f"  目标: {environment.host}")
    print(f"  模拟: 智能货柜心跳/开门/取货/结算全链路")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("=" * 60)
    print("MiMo IoT 压测结束")
    print("=" * 60)
