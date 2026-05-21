from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator

# Set env vars BEFORE importing app modules (settings uses lru_cache)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-jwt-signing")
os.environ.setdefault("APP_ENV", "test")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
import app.models  # noqa: F401  — register all models on Base.metadata

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    from app.main import app as test_app

    test_app.dependency_overrides[get_db] = override_get_db

    # Mock lifespan to avoid scheduler/MQTT startup
    async def mock_lifespan(app):
        yield

    test_app.router.lifespan_context = mock_lifespan

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Create test user and return auth headers"""
    await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}
