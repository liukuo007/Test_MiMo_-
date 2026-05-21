from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import SystemSetting
from app.models.user import User
from app.schemas.setting import SettingResponse
from app.dependencies import CurrentUser

router = APIRouter()

# 默认设置（首次运行时写入 DB）
_DEFAULT_SETTINGS = {
    "basic": {
        "name": "MiMo - 智能货柜全链路测试平台",
        "description": "智能货柜质量基础设施",
        "default_env": "dev",
        "timezone": "Asia/Shanghai",
    },
    "notify": {
        "email_enabled": True,
        "smtp_host": "smtp.mimo.local",
        "smtp_from": "noreply@mimo.local",
        "webhook_enabled": False,
        "webhook_url": "",
        "events": ["task_completed", "task_failed"],
    },
    "engine": {
        "api_timeout": 30,
        "iot_max_concurrent": 1000,
        "ai_device": "cuda",
        "web_engine_type": "playwright",
        "appium_url": "http://localhost:4723",
    },
}


async def _ensure_defaults(db: AsyncSession):
    """首次访问时将默认设置写入数据库"""
    count = (await db.execute(select(func.count(SystemSetting.id)))).scalar()
    if count == 0:
        for category, values in _DEFAULT_SETTINGS.items():
            setting = SystemSetting(
                key=category,
                value=values,
                category=category,
                description=f"{category} 配置",
            )
            db.add(setting)
        await db.flush()


@router.get("")
async def get_settings(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    count = (await db.execute(select(func.count(SystemSetting.id)))).scalar() or 0
    if count == 0:
        await _ensure_defaults(db)

    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}


@router.put("")
async def update_settings(data: dict, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    count = (await db.execute(select(func.count(SystemSetting.id)))).scalar() or 0
    if count == 0:
        await _ensure_defaults(db)

    for key, values in data.items():
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            if isinstance(setting.value, dict) and isinstance(values, dict):
                setting.value.update(values)
            else:
                setting.value = values
        else:
            setting = SystemSetting(key=key, value=values, category=key)
            db.add(setting)

    await db.flush()

    result = await db.execute(select(SystemSetting))
    settings = result.scalars().all()
    return {s.key: s.value for s in settings}


@router.get("/users")
async def list_users(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "email": u.email,
        }
        for u in users
    ]
