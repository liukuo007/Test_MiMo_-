from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    async def login(self, db: AsyncSession, username: str, password: str) -> str:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise BadRequestError("Invalid username or password")
        return create_access_token({"sub": str(user.id), "username": user.username, "role": user.role.value})

    async def register(self, db: AsyncSession, username: str, email: str, password: str, **kwargs) -> User:
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ConflictError(f"Username '{username}' already exists")

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            **kwargs,
        )
        db.add(user)
        await db.flush()
        return user


auth_service = AuthService()
