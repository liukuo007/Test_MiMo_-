from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SettingCreate(BaseModel):
    key: str
    value: dict | None = None
    category: str = "general"
    description: str | None = None


class SettingUpdate(BaseModel):
    value: dict | None = None
    category: str | None = None
    description: str | None = None


class SettingResponse(BaseModel):
    id: int
    key: str
    value: dict | None
    category: str
    description: str | None
    updated_at: datetime

    class Config:
        from_attributes = True
