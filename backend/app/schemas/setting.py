from __future__ import annotations
from typing import Optional

from datetime import datetime

from pydantic import BaseModel


class SettingCreate(BaseModel):
    key: str
    value: Optional[dict] = None
    category: str = "general"
    description: Optional[str] = None


class SettingUpdate(BaseModel):
    value: Optional[dict] = None
    category: Optional[str] = None
    description: Optional[str] = None


class SettingResponse(BaseModel):
    id: int
    key: str
    value: Optional[dict]
    category: str
    description: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True
