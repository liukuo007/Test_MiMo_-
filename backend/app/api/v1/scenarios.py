from __future__ import annotations

import time
import uuid
from datetime import datetime

import httpx
import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.device_event import DeviceEvent, DeviceEventType
from app.models.scenario import (
    BatchStatus,
    ExecutionStatus,
    ScenarioBatch,
    ScenarioExecution,
    ScenarioTemplate,
)
from app.schemas.scenario import (
    BatchResponse,
    BatchRunResponse,
    DevicePickItem,
    ScenarioExecutionResponse,
    ScenarioRunRequest,
    ScenarioRunResponse,
    ScenarioTemplateCreate,
    ScenarioTemplateResponse,
    StepResult,
)

logger = structlog.get_logger()
router = APIRouter()

# ── 商品库 & 设备类型 ────────────────────────────────────────────
PRODUCT_CATALOG = {
    "cola": {"name": "可口可乐 330ml", "sku": "SKU-COLA-001", "price": 3.00},
    "chips": {"name": "乐事薯片 70g", "sku": "SKU-CHIPS-001", "price": 8.50},
    "water": {"name": "农夫山泉 550ml", "sku": "SKU-WATER-001", "price": 2.00},
    "juice": {"name": "美汁源果粒橙 450ml", "sku": "SKU-JUICE-001", "price": 5.50},
    "bread": {"name": "桃李面包 150g", "sku": "SKU-BREAD-001", "price": 6.80},
    "milk": {"name": "蒙牛纯牛奶 250ml", "sku": "SKU-MILK-001", "price": 4.50},
    "snickers": {"name": "士力架 51g", "sku": "SKU-SNCK-001", "price": 5.00},
    "tea": {"name": "康师傅冰红茶 500ml", "sku": "SKU-TEA-001", "price": 3.50},
}

DEVICE_TYPES = [
    {"value": "V1", "label": "V1 标准柜", "desc": "单门标准货柜"},
    {"value": "V2", "label": "V2 双温柜", "desc": "冷藏+常温双温区"},
    {"value": "V3", "label": "V3 旗舰柜", "desc": "大屏+AI 摄像头"},
]

PAYMENT_METHODS = [
    {"value": "wechat", "label": "微信支付"},
    {"value": "alipay", "label": "支付宝"},
    {"value": "credit_card", "label": "信用卡"},
    {"value": "face_pay", "label": "刷脸支付"},
]

# ── 默认场景模板 ─────────────────────────────────────────────────
DEFAULT_TEMPLATES = [
    {
        "name": "常规购物全链路",
        "description": "模拟用户扫码开门，拿走商品，关门，系统自动扣款成功",
        "category": "shopping",
        "icon": "ShoppingCart",
        "color": "#67c23a",
        "sort_order": 1,
        "params_schema": {
            "fields": [
                {"key": "device_type", "label": "货柜型号", "type": "select", "options": "device_types", "default": "V1"},
                {"key": "product_key", "label": "商品", "type": "select", "options": "products", "default": "cola"},
                {"key": "quantity", "label": "数量", "type": "number", "default": 2, "min": 1, "max": 10},
                {"key": "payment_method", "label": "支付方式", "type": "select", "options": "payment_methods", "default": "wechat"},
            ],
        },
        "steps_definition": {
            "steps": [
                {"name": "扫码开门", "event_type": "door_open", "message_tpl": "用户扫码验证通过，{device_type} 货柜门打开"},
                {"name": "AI 识别商品", "event_type": "item_detected", "message_tpl": "AI 识别 {product_name} x{quantity}, 总价 ¥{total_price}, confidence=0.{confidence}"},
                {"name": "关门结算", "event_type": "door_close", "message_tpl": "货柜门关闭，开始结算 ¥{total_price}"},
                {"name": "自动扣款", "event_type": "payment", "message_tpl": "{payment_label}扣款 ¥{total_price} 成功"},
            ],
        },
        "wiremock_mapping": {"payment_status": "success"},
    },
    {
        "name": "异常：余额不足",
        "description": "模拟用户开门拿走商品，但扣款失败，触发欠费告警",
        "category": "exception",
        "icon": "CreditCard",
        "color": "#e6a23c",
        "sort_order": 2,
        "params_schema": {
            "fields": [
                {"key": "device_type", "label": "货柜型号", "type": "select", "options": "device_types", "default": "V1"},
                {"key": "product_key", "label": "商品", "type": "select", "options": "products", "default": "chips"},
                {"key": "quantity", "label": "数量", "type": "number", "default": 1, "min": 1, "max": 10},
                {"key": "payment_method", "label": "支付方式", "type": "select", "options": "payment_methods", "default": "credit_card"},
            ],
        },
        "steps_definition": {
            "steps": [
                {"name": "扫码开门", "event_type": "door_open", "message_tpl": "用户扫码验证通过，{device_type} 货柜门打开"},
                {"name": "AI 识别商品", "event_type": "item_detected", "message_tpl": "AI 识别 {product_name} x{quantity}, 总价 ¥{total_price}, confidence=0.{confidence}"},
                {"name": "关门结算", "event_type": "door_close", "message_tpl": "货柜门关闭，开始结算 ¥{total_price}"},
                {"name": "扣款失败", "event_type": "payment", "message_tpl": "{payment_label}扣款 ¥{total_price} 失败: INSUFFICIENT_FUNDS"},
            ],
        },
        "wiremock_mapping": {"payment_status": "insufficient_funds"},
    },
    {
        "name": "异常：关门超时",
        "description": "模拟用户开门后长时间不关门，系统触发超时报警",
        "category": "exception",
        "icon": "AlarmClock",
        "color": "#f56c6c",
        "sort_order": 3,
        "params_schema": {
            "fields": [
                {"key": "device_type", "label": "货柜型号", "type": "select", "options": "device_types", "default": "V1"},
                {"key": "timeout_seconds", "label": "超时时间(秒)", "type": "number", "default": 120, "min": 30, "max": 600},
            ],
        },
        "steps_definition": {
            "steps": [
                {"name": "扫码开门", "event_type": "door_open", "message_tpl": "用户扫码验证通过，{device_type} 货柜门打开"},
                {"name": "等待超时", "event_type": "warning", "message_tpl": "门已开启超过 {timeout_seconds} 秒，触发超时告警"},
                {"name": "系统报警", "event_type": "fault", "message_tpl": "关门超时 {timeout_seconds}s，已通知运营人员处理"},
            ],
        },
        "wiremock_mapping": None,
    },
    {
        "name": "多商品混合购物",
        "description": "模拟用户拿走多种不同商品，验证 AI 多 SKU 识别和合并结算能力",
        "category": "shopping",
        "icon": "Goods",
        "color": "#909399",
        "sort_order": 4,
        "params_schema": {
            "fields": [
                {"key": "device_type", "label": "货柜型号", "type": "select", "options": "device_types", "default": "V2"},
                {"key": "payment_method", "label": "支付方式", "type": "select", "options": "payment_methods", "default": "alipay"},
            ],
        },
        "steps_definition": {
            "steps": [
                {"name": "扫码开门", "event_type": "door_open", "message_tpl": "用户扫码验证通过，{device_type} 货柜门打开"},
                {"name": "AI 识别商品 1", "event_type": "item_detected", "message_tpl": "AI 识别 SKU-COLA-001 x1 ¥3.00, confidence=0.97"},
                {"name": "AI 识别商品 2", "event_type": "item_detected", "message_tpl": "AI 识别 SKU-CHIPS-001 x1 ¥8.50, confidence=0.94"},
                {"name": "AI 识别商品 3", "event_type": "item_detected", "message_tpl": "AI 识别 SKU-WATER-001 x2 ¥4.00, confidence=0.96"},
                {"name": "关门结算", "event_type": "door_close", "message_tpl": "货柜门关闭，合并结算 ¥15.50"},
                {"name": "自动扣款", "event_type": "payment", "message_tpl": "{payment_label}扣款 ¥15.50 成功"},
            ],
        },
        "wiremock_mapping": {"payment_status": "success"},
    },
    {
        "name": "AI 误识别告警",
        "description": "模拟 AI 识别置信度不足，触发人工复核流程",
        "category": "exception",
        "icon": "WarningFilled",
        "color": "#e6a23c",
        "sort_order": 5,
        "params_schema": {
            "fields": [
                {"key": "device_type", "label": "货柜型号", "type": "select", "options": "device_types", "default": "V3"},
                {"key": "product_key", "label": "商品", "type": "select", "options": "products", "default": "bread"},
            ],
        },
        "steps_definition": {
            "steps": [
                {"name": "扫码开门", "event_type": "door_open", "message_tpl": "用户扫码验证通过，{device_type} 货柜门打开"},
                {"name": "AI 识别商品", "event_type": "item_detected", "message_tpl": "AI 识别 {product_name} x1, confidence=0.52 — 低于阈值 0.85"},
                {"name": "触发复核", "event_type": "ai_recognition", "message_tpl": "AI 置信度不足，已触发人工复核流程"},
                {"name": "关门等待", "event_type": "door_close", "message_tpl": "货柜门关闭，等待人工复核结果"},
            ],
        },
        "wiremock_mapping": None,
    },
    {
        "name": "设备离线恢复",
        "description": "模拟设备网络中断后自动重连恢复，验证设备容错能力",
        "category": "exception",
        "icon": "Connection",
        "color": "#909399",
        "sort_order": 6,
        "params_schema": {
            "fields": [
                {"key": "device_type", "label": "货柜型号", "type": "select", "options": "device_types", "default": "V1"},
            ],
        },
        "steps_definition": {
            "steps": [
                {"name": "设备心跳正常", "event_type": "heartbeat", "message_tpl": "{device_type} 设备心跳正常，温度 4.2°C"},
                {"name": "网络中断", "event_type": "error", "message_tpl": "设备网络连接中断，最后心跳时间 2026-01-01 10:00:00"},
                {"name": "自动重连", "event_type": "info", "message_tpl": "设备尝试重新连接... 第 1 次重连成功"},
                {"name": "状态恢复", "event_type": "heartbeat", "message_tpl": "{device_type} 设备恢复正常，在线温度 4.3°C"},
            ],
        },
        "wiremock_mapping": None,
    },
]


async def _ensure_templates(db: AsyncSession) -> None:
    result = await db.execute(select(func.count(ScenarioTemplate.id)))
    count = result.scalar() or 0
    if count > 0:
        return
    for tpl in DEFAULT_TEMPLATES:
        db.add(ScenarioTemplate(**tpl))
    await db.flush()
    logger.info("scenario_templates_seeded", count=len(DEFAULT_TEMPLATES))


def _resolve_message(tpl_msg: str, params: dict) -> str:
    try:
        return tpl_msg.format(**params)
    except (KeyError, ValueError):
        return tpl_msg


def _build_run_params(req: ScenarioRunRequest | None, template: ScenarioTemplate) -> dict:
    product_key = (req.product_key if req else None) or "cola"
    product = PRODUCT_CATALOG.get(product_key, PRODUCT_CATALOG["cola"])
    quantity = (req.quantity if req else None) or 2
    unit_price = product["price"]
    total_price = round(unit_price * quantity, 2)
    device_type = (req.device_type if req else None) or "V1"
    payment_method = (req.payment_method if req else None) or "wechat"

    payment_label_map = {
        "wechat": "微信支付", "alipay": "支付宝",
        "credit_card": "信用卡", "face_pay": "刷脸支付",
    }
    import random
    confidence = random.randint(92, 99)

    return {
        "device_type": device_type,
        "product_key": product_key,
        "product_name": product["name"],
        "product_sku": product["sku"],
        "quantity": quantity,
        "unit_price": unit_price,
        "total_price": total_price,
        "payment_method": payment_method,
        "payment_label": payment_label_map.get(payment_method, payment_method),
        "timeout_seconds": (req.timeout_seconds if req else None) or 120,
        "confidence": confidence,
    }


async def _execute_on_virtual_device(
    db: AsyncSession,
    template: ScenarioTemplate,
    run_params: dict,
    uid: str,
) -> tuple[str, str, list[StepResult], str]:
    """在虚拟设备上执行场景，返回 (device_sn, virtual_user, steps, overall_status)"""
    device_sn = f"VSN-{uid}"
    virtual_user = f"user-{uid}"

    device_type_map = {"V1": DeviceType.VIRTUAL_L1, "V2": DeviceType.VIRTUAL_L2, "V3": DeviceType.VIRTUAL_L3}
    device = Device(
        device_sn=device_sn,
        name=f"场景沙箱-{uid}",
        device_type=device_type_map.get(run_params.get("device_type", "V1"), DeviceType.VIRTUAL_L1),
        status=DeviceStatus.ONLINE,
        region="scenario-sandbox",
        firmware_version="v2.0.0-scenario",
        ip_address="127.0.0.1",
        temperature=25.0,
    )
    db.add(device)
    await db.flush()
    await db.refresh(device)

    steps_def = template.steps_definition or {"steps": []}
    step_list = steps_def.get("steps", [])
    step_results: list[StepResult] = []
    overall_status = "passed"

    for idx, step_def in enumerate(step_list):
        step_start = time.time()
        try:
            step_name = step_def.get("name", f"Step {idx + 1}")
            event_type_str = step_def.get("event_type", "info")
            message = _resolve_message(step_def.get("message_tpl", step_def.get("message", "")), run_params)

            try:
                etype = DeviceEventType(event_type_str)
            except ValueError:
                etype = DeviceEventType.INFO
            db.add(DeviceEvent(device_id=device.id, event_type=etype, message=message))
            await db.flush()

            if event_type_str == "payment" and template.wiremock_mapping:
                wm = template.wiremock_mapping
                amount = run_params.get("total_price", wm.get("amount", 0))
                method = run_params.get("payment_method", wm.get("method", "wechat"))
                pay_result = await _call_wiremock_payment(
                    f"SCN-{uid}", float(amount), method, wm.get("payment_status", "success")
                )
                if not pay_result["success"]:
                    overall_status = "failed"
                    step_results.append(StepResult(
                        step=idx + 1, name=step_name, status="failed",
                        duration_ms=_ms(step_start), error=pay_result.get("error", "支付失败"),
                    ))
                    continue

            step_results.append(StepResult(
                step=idx + 1, name=step_name, status="passed",
                duration_ms=_ms(step_start), detail=message,
            ))
        except Exception as e:
            overall_status = "failed"
            step_results.append(StepResult(
                step=idx + 1, name=step_def.get("name", f"Step {idx + 1}"),
                status="failed", duration_ms=_ms(step_start), error=str(e),
            ))

    return device_sn, virtual_user, step_results, overall_status


async def _execute_on_real_device(
    db: AsyncSession,
    device: Device,
    template: ScenarioTemplate,
    run_params: dict,
    uid: str,
) -> tuple[str, list[StepResult], str]:
    """在真实设备上通过 MQTT 执行场景，返回 (device_sn, steps, overall_status)"""
    from app.iot.mqtt_client import mqtt_client

    device_sn = device.device_sn
    steps_def = template.steps_definition or {"steps": []}
    step_list = steps_def.get("steps", [])
    step_results: list[StepResult] = []
    overall_status = "passed"

    # 标记设备为占用状态
    device.status = DeviceStatus.OCCUPIED
    device.occupied_by = None
    await db.flush()

    for idx, step_def in enumerate(step_list):
        step_start = time.time()
        try:
            step_name = step_def.get("name", f"Step {idx + 1}")
            event_type_str = step_def.get("event_type", "info")
            message = _resolve_message(step_def.get("message_tpl", step_def.get("message", "")), run_params)

            # 通过 MQTT 下发指令到真实设备
            mqtt_payload = {
                "scenario_id": uid,
                "step": idx + 1,
                "step_name": step_name,
                "event_type": event_type_str,
                "params": run_params,
            }
            mqtt_client.publish_command(device_sn, f"scenario_{event_type_str}", mqtt_payload)

            # 记录设备事件
            try:
                etype = DeviceEventType(event_type_str)
            except ValueError:
                etype = DeviceEventType.INFO
            db.add(DeviceEvent(device_id=device.id, event_type=etype, message=f"[场景测试] {message}"))
            await db.flush()

            # 支付步骤：调用 WireMock
            if event_type_str == "payment" and template.wiremock_mapping:
                wm = template.wiremock_mapping
                amount = run_params.get("total_price", wm.get("amount", 0))
                method = run_params.get("payment_method", wm.get("method", "wechat"))
                pay_result = await _call_wiremock_payment(
                    f"SCN-{uid}", float(amount), method, wm.get("payment_status", "success")
                )
                if not pay_result["success"]:
                    overall_status = "failed"
                    step_results.append(StepResult(
                        step=idx + 1, name=step_name, status="failed",
                        duration_ms=_ms(step_start), error=pay_result.get("error", "支付失败"),
                    ))
                    continue

            step_results.append(StepResult(
                step=idx + 1, name=step_name, status="passed",
                duration_ms=_ms(step_start), detail=f"[MQTT] {message}",
            ))
        except Exception as e:
            overall_status = "failed"
            step_results.append(StepResult(
                step=idx + 1, name=step_def.get("name", f"Step {idx + 1}"),
                status="failed", duration_ms=_ms(step_start), error=str(e),
            ))

    # 恢复设备状态
    device.status = DeviceStatus.ONLINE
    await db.flush()

    return device_sn, step_results, overall_status


# ── API 端点 ────────────────────────────────────────────────────


@router.get("/templates", response_model=list[ScenarioTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
):
    await _ensure_templates(db)
    result = await db.execute(
        select(ScenarioTemplate)
        .where(ScenarioTemplate.is_active == True)
        .order_by(ScenarioTemplate.sort_order)
    )
    return result.scalars().all()


@router.post("/templates", response_model=ScenarioTemplateResponse)
async def create_template(
    body: ScenarioTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a custom scenario template (manual scenario)."""
    template = ScenarioTemplate(
        name=body.name,
        description=body.description,
        category=body.category,
        icon=body.icon,
        color=body.color,
        steps_definition=body.steps_definition,
        params_schema=body.params_schema,
        wiremock_mapping=body.wiremock_mapping,
        sort_order=body.sort_order,
        is_active=body.is_active,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/templates/{template_id}", response_model=ScenarioTemplateResponse)
async def update_template(
    template_id: int,
    body: ScenarioTemplateCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing scenario template."""
    result = await db.execute(
        select(ScenarioTemplate).where(ScenarioTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("ScenarioTemplate", template_id)

    for field in ["name", "description", "category", "icon", "color", "steps_definition", "params_schema", "wiremock_mapping", "sort_order", "is_active"]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(template, field, val)
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete (soft-delete) a scenario template."""
    result = await db.execute(
        select(ScenarioTemplate).where(ScenarioTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("ScenarioTemplate", template_id)

    template.is_active = False
    await db.commit()
    return {"detail": "Template deleted", "id": template_id}


@router.get("/catalog")
async def get_catalog():
    return {
        "products": [{"key": k, **v} for k, v in PRODUCT_CATALOG.items()],
        "device_types": DEVICE_TYPES,
        "payment_methods": PAYMENT_METHODS,
    }


@router.get("/devices", response_model=list[DevicePickItem])
async def list_devices_for_pick(
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(None, description="搜索设备 SN / 名称"),
    status: str | None = Query(None, description="设备状态: online/offline/occupied"),
    device_type: str | None = Query(None, description="设备类型: real/virtual_l1/virtual_l2/virtual_l3"),
    region: str | None = Query(None, description="区域"),
    limit: int = Query(50, ge=1, le=200),
):
    """设备选择器 — 从 20 万台设备中搜索/筛选"""
    query = select(Device)

    if search:
        query = query.where(
            or_(
                Device.device_sn.ilike(f"%{search}%"),
                Device.name.ilike(f"%{search}%"),
            )
        )
    if status:
        try:
            query = query.where(Device.status == DeviceStatus(status))
        except ValueError:
            pass
    if device_type:
        try:
            query = query.where(Device.device_type == DeviceType(device_type))
        except ValueError:
            pass
    if region:
        query = query.where(Device.region == region)

    query = query.order_by(Device.last_heartbeat.desc().nullslast()).limit(limit)
    result = await db.execute(query)
    devices = result.scalars().all()

    return [
        DevicePickItem(
            id=d.id,
            device_sn=d.device_sn,
            name=d.name,
            device_type=d.device_type.value if hasattr(d.device_type, "value") else d.device_type,
            status=d.status.value if hasattr(d.status, "value") else d.status,
            region=d.region,
            temperature=d.temperature,
            last_heartbeat=d.last_heartbeat,
            firmware_version=d.firmware_version,
        )
        for d in devices
    ]


@router.post("/templates/{template_id}/run", response_model=ScenarioRunResponse)
async def run_scenario(
    template_id: int,
    req: ScenarioRunRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """单设备场景执行 — 支持虚拟设备和真实设备"""
    result = await db.execute(
        select(ScenarioTemplate).where(ScenarioTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("ScenarioTemplate", template_id)

    total_start = time.time()
    uid = uuid.uuid4().hex[:8]
    user_name = "anonymous"
    run_params = _build_run_params(req, template)

    # 判断是虚拟设备还是真实设备
    device_sns = (req.device_sns if req else None) or []
    is_real = len(device_sns) > 0

    if is_real:
        # 真实设备：查找第一台
        device_sn_query = device_sns[0]
        dev_result = await db.execute(
            select(Device).where(Device.device_sn == device_sn_query)
        )
        device = dev_result.scalar_one_or_none()
        if not device:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Device", device_sn_query)

        device_sn, step_results, overall_status = await _execute_on_real_device(
            db, device, template, run_params, uid,
        )
        virtual_user = ""
        device_name = device.name
    else:
        device_sn, virtual_user, step_results, overall_status = await _execute_on_virtual_device(
            db, template, run_params, uid,
        )
        device_name = f"场景沙箱-{uid}"

    # 记录执行历史
    execution = ScenarioExecution(
        template_id=template_id,
        device_sn=device_sn,
        device_name=device_name,
        is_real_device=is_real,
        run_params=run_params,
        status=ExecutionStatus(overall_status),
        steps_result=[s.model_dump() for s in step_results],
        total_duration_ms=_ms(total_start),
        triggered_by=None,
        triggered_by_name=user_name,
        finished_at=datetime.now(),
    )
    db.add(execution)
    await db.flush()
    await db.refresh(execution)

    return ScenarioRunResponse(
        execution_id=execution.id,
        template_id=template_id,
        template_name=template.name,
        device_sn=device_sn,
        device_name=device_name,
        is_real_device=is_real,
        run_params=run_params,
        status=overall_status,
        total_duration_ms=_ms(total_start),
        steps=step_results,
    )


@router.post("/templates/{template_id}/batch-run", response_model=BatchRunResponse)
async def batch_run_scenario(
    template_id: int,
    req: ScenarioRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量场景执行 — 多台设备并行执行同一场景"""
    result = await db.execute(
        select(ScenarioTemplate).where(ScenarioTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("ScenarioTemplate", template_id)

    device_sns = req.device_sns or []
    if not device_sns:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Devices", "device_sns 不能为空")

    uid = uuid.uuid4().hex[:8]
    user_name = "anonymous"
    run_params = _build_run_params(req, template)
    total_start = time.time()

    # 创建批次记录
    batch = ScenarioBatch(
        template_id=template_id,
        name=f"{template.name}-批次-{uid}",
        total_count=len(device_sns),
        run_params=run_params,
        triggered_by=None,
        triggered_by_name=user_name,
    )
    db.add(batch)
    await db.flush()
    await db.refresh(batch)

    executions_response: list[ScenarioRunResponse] = []
    passed_count = 0
    failed_count = 0

    for device_sn in device_sns:
        exec_start = time.time()
        uid_exec = uuid.uuid4().hex[:8]

        # 查找设备
        dev_result = await db.execute(
            select(Device).where(Device.device_sn == device_sn)
        )
        device = dev_result.scalar_one_or_none()

        if device and device.device_type == DeviceType.REAL:
            # 真实设备
            device_sn_val, step_results, overall_status = await _execute_on_real_device(
                db, device, template, run_params, uid_exec,
            )
            device_name = device.name
            is_real = True
        else:
            # 虚拟设备或不存在的设备
            device_sn_val, _, step_results, overall_status = await _execute_on_virtual_device(
                db, template, run_params, uid_exec,
            )
            device_name = f"场景沙箱-{uid_exec}"
            is_real = False
            device_sn = device_sn_val

        if overall_status == "passed":
            passed_count += 1
        else:
            failed_count += 1

        execution = ScenarioExecution(
            batch_id=batch.id,
            template_id=template_id,
            device_sn=device_sn_val,
            device_name=device_name,
            is_real_device=is_real,
            run_params=run_params,
            status=ExecutionStatus(overall_status),
            steps_result=[s.model_dump() for s in step_results],
            total_duration_ms=_ms(exec_start),
            triggered_by=None,
            triggered_by_name=user_name,
            finished_at=datetime.now(),
        )
        db.add(execution)
        await db.flush()
        await db.refresh(execution)

        executions_response.append(ScenarioRunResponse(
            execution_id=execution.id,
            batch_id=batch.id,
            template_id=template_id,
            template_name=template.name,
            device_sn=device_sn_val,
            device_name=device_name,
            is_real_device=is_real,
            run_params=run_params,
            status=overall_status,
            total_duration_ms=_ms(exec_start),
            steps=step_results,
        ))

    # 更新批次状态
    batch.passed_count = passed_count
    batch.failed_count = failed_count
    if failed_count == 0:
        batch.status = BatchStatus.PASSED
    elif passed_count == 0:
        batch.status = BatchStatus.FAILED
    else:
        batch.status = BatchStatus.PARTIAL
    batch.finished_at = datetime.now()
    await db.flush()

    return BatchRunResponse(
        batch_id=batch.id,
        template_id=template_id,
        template_name=template.name,
        total_count=len(device_sns),
        status=batch.status.value if hasattr(batch.status, "value") else batch.status,
        executions=executions_response,
    )


@router.get("/executions")
async def list_executions(
    db: AsyncSession = Depends(get_db),
    template_id: int | None = None,
    batch_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = select(ScenarioExecution)
    count_query = select(func.count(ScenarioExecution.id))
    if template_id:
        query = query.where(ScenarioExecution.template_id == template_id)
        count_query = count_query.where(ScenarioExecution.template_id == template_id)
    if batch_id:
        query = query.where(ScenarioExecution.batch_id == batch_id)
        count_query = count_query.where(ScenarioExecution.batch_id == batch_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit).order_by(ScenarioExecution.id.desc())
    result = await db.execute(query)
    rows = result.scalars().all()

    tpl_ids = list(set(r.template_id for r in rows))
    tpl_names: dict[int, str] = {}
    if tpl_ids:
        tpl_result = await db.execute(
            select(ScenarioTemplate.id, ScenarioTemplate.name).where(ScenarioTemplate.id.in_(tpl_ids))
        )
        for row in tpl_result:
            tpl_names[row[0]] = row[1]

    items = []
    for row in rows:
        items.append(ScenarioExecutionResponse(
            id=row.id,
            batch_id=row.batch_id,
            template_id=row.template_id,
            template_name=tpl_names.get(row.template_id, "未知场景"),
            device_sn=row.device_sn,
            device_name=row.device_name,
            is_real_device=row.is_real_device,
            run_params=row.run_params,
            status=row.status.value if hasattr(row.status, "value") else row.status,
            steps_result=row.steps_result,
            total_duration_ms=row.total_duration_ms,
            error_message=row.error_message,
            triggered_by_name=row.triggered_by_name,
            created_at=row.created_at,
            finished_at=row.finished_at,
        ))

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/batches")
async def list_batches(
    db: AsyncSession = Depends(get_db),
    template_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """查询批量执行记录"""
    query = select(ScenarioBatch)
    count_query = select(func.count(ScenarioBatch.id))
    if template_id:
        query = query.where(ScenarioBatch.template_id == template_id)
        count_query = count_query.where(ScenarioBatch.template_id == template_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset(skip).limit(limit).order_by(ScenarioBatch.id.desc())
    result = await db.execute(query)
    rows = result.scalars().all()

    tpl_ids = list(set(r.template_id for r in rows))
    tpl_names: dict[int, str] = {}
    if tpl_ids:
        tpl_result = await db.execute(
            select(ScenarioTemplate.id, ScenarioTemplate.name).where(ScenarioTemplate.id.in_(tpl_ids))
        )
        for row in tpl_result:
            tpl_names[row[0]] = row[1]

    items = []
    for row in rows:
        items.append(BatchResponse(
            id=row.id,
            template_id=row.template_id,
            template_name=tpl_names.get(row.template_id, "未知场景"),
            name=row.name,
            total_count=row.total_count,
            passed_count=row.passed_count,
            failed_count=row.failed_count,
            status=row.status.value if hasattr(row.status, "value") else row.status,
            run_params=row.run_params,
            triggered_by_name=row.triggered_by_name,
            created_at=row.created_at,
            finished_at=row.finished_at,
        ))

    return {"items": items, "total": total, "skip": skip, "limit": limit}


# ── 辅助函数 ────────────────────────────────────────────────────


async def _call_wiremock_payment(order_id: str, amount: float, method: str, status: str) -> dict:
    if status != "success":
        error_map = {
            "insufficient_funds": "INSUFFICIENT_FUNDS: 信用卡余额不足",
            "timeout": "PAYMENT_TIMEOUT: 支付超时",
            "card_expired": "CARD_EXPIRED: 银行卡已过期",
        }
        return {"success": False, "error": error_map.get(status, f"PAYMENT_FAILED: {status}")}

    from app.config import get_settings
    wiremock_url = get_settings().wiremock_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{wiremock_url}/api/v1/payment/create",
                json={"order_id": order_id, "amount": amount, "currency": "CNY", "method": method},
            )
            if resp.status_code != 200:
                return {"success": False, "error": f"WireMock HTTP {resp.status_code}"}
            data = resp.json()
            return {"success": data.get("success", False), "error": data.get("error_message")}
    except httpx.ConnectError:
        return {"success": False, "error": "WireMock 服务不可达"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _ms(start: float) -> float:
    return round((time.time() - start) * 1000, 1)
