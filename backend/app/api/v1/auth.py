from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    token = await auth_service.login(db, req.username, req.password)
    return TokenResponse(access_token=token)


@router.post("/register", response_model=UserResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register(
        db,
        username=req.username,
        email=req.email,
        password=req.password,
        full_name=req.full_name,
        role=req.role,
    )
    return user
