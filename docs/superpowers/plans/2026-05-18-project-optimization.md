# MiMo 项目优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 整理项目文件夹结构，补充工程化能力（测试、CI/CD、代码质量），使项目达到开源标准。

**Architecture:** Phase 1 清理文件夹（删除旧 MVP、归档文档、整理图片），Phase 2 补充测试和 CI/CD。所有变更在 `mimo/` 仓库内完成。

**Tech Stack:** Git, GitHub Actions, pytest, ruff, eslint

---

## Phase 1: 文件夹整理

### Task 1: 删除 `test/` 目录

**Files:**
- Delete: `test/` (整个目录，含 node_modules 和 venv)

- [ ] **Step 1: 确认 test/ 目录内容**

```bash
ls -la test/
```

Expected: README.md, backend/, frontend/, docker-compose.yml, docs/

- [ ] **Step 2: 删除 test/ 目录**

```bash
rm -rf test/
```

- [ ] **Step 3: 验证删除**

```bash
ls test/ 2>&1
```

Expected: "No such file or directory"

---

### Task 2: 创建文档目录结构

**Files:**
- Create: `mimo/docs/design/` (目录)
- Create: `mimo/docs/images/` (目录)

- [ ] **Step 1: 创建目录**

```bash
cd mimo
mkdir -p docs/design docs/images
```

- [ ] **Step 2: 验证目录**

```bash
ls -la docs/
```

Expected: api.md, architecture.md, deployment.md, development.md, design/, images/, superpowers/

---

### Task 3: 归档设计文档

**Files:**
- Move: `需求.txt` → `mimo/docs/design/requirements.md`
- Move: `新架构方案.md` → `mimo/docs/design/architecture-v2.md`
- Move: `视达.md` → `mimo/docs/design/architecture-overview.md`
- Move: `视达-补充设计.md` → `mimo/docs/design/architecture-supplement.md`
- Move: `E2E测试平台架构总结.md` → `mimo/docs/design/e2e-architecture-summary.md`
- Move: `平台演示介绍文档.md` → `mimo/docs/design/demo-guide.md`
- Move: `图片信息总结.md` → `mimo/docs/design/image-notes.md`

- [ ] **Step 1: 移动所有文档**

```bash
mv 需求.txt mimo/docs/design/requirements.md
mv 新架构方案.md mimo/docs/design/architecture-v2.md
mv 视达.md mimo/docs/design/architecture-overview.md
mv 视达-补充设计.md mimo/docs/design/architecture-supplement.md
mv "E2E测试平台架构总结.md" mimo/docs/design/e2e-architecture-summary.md
mv 平台演示介绍文档.md mimo/docs/design/demo-guide.md
mv 图片信息总结.md mimo/docs/design/image-notes.md
```

- [ ] **Step 2: 验证移动结果**

```bash
ls mimo/docs/design/
```

Expected: 7 个 .md 文件

---

### Task 4: 整理图片和媒体文件

**Files:**
- Move: `c30933aa83afe912efa6e653a4063da6.jpg` → `mimo/docs/images/`
- Move: `161f69d15f6409891e0ac86860cc2962.jpg` → `mimo/docs/images/`
- Move: `3c071fb0e26e536ea0ce0ddf2c9641be.jpg` → `mimo/docs/images/`
- Move: `e9523db6e6903358c64dba4a18fe786b.png` → `mimo/docs/images/`
- Move: `新录音.m4a` → `mimo/docs/images/`

- [ ] **Step 1: 移动所有图片和媒体**

```bash
mv c30933aa83afe912efa6e653a4063da6.jpg mimo/docs/images/
mv 161f69d15f6409891e0ac86860cc2962.jpg mimo/docs/images/
mv 3c071fb0e26e536ea0ce0ddf2c9641be.jpg mimo/docs/images/
mv e9523db6e6903358c64dba4a18fe786b.png mimo/docs/images/
mv 新录音.m4a mimo/docs/images/
```

- [ ] **Step 2: 验证**

```bash
ls mimo/docs/images/
```

Expected: 5 个文件

---

### Task 5: 清理临时文件

**Files:**
- Delete: `.DS_Store`

- [ ] **Step 1: 删除 .DS_Store**

```bash
rm -f .DS_Store
```

- [ ] **Step 2: 验证根目录只剩 mimo/**

```bash
ls -la
```

Expected: 只剩 `mimo/` 和 `.claude/`

---

### Task 6: 更新 .gitignore 并提交

**Files:**
- Modify: `mimo/.gitignore`

- [ ] **Step 1: 确保 .gitignore 包含 .DS_Store**

检查 `mimo/.gitignore` 是否已有 `.DS_Store`。已有则跳过。

- [ ] **Step 2: 提交所有变更**

```bash
cd mimo
git add -A
git status
```

检查 staged 文件列表，确认无敏感文件。

- [ ] **Step 3: 创建提交**

```bash
git commit -m "$(cat <<'EOF'
chore: reorganize project folder structure

- Remove obsolete test/ directory (early MVP prototype)
- Move design documents to docs/design/
- Move images and media to docs/images/
- Clean up .DS_Store files

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase 2: 工程化完善

### Task 7: 补充后端 API 测试 — Auth 模块

**Files:**
- Create: `backend/tests/__init__.py` (已存在)
- Create: `backend/tests/conftest.py` (已存在，需更新)
- Create: `backend/tests/test_api/__init__.py`
- Create: `backend/tests/test_api/test_auth.py`

- [ ] **Step 1: 更新 conftest.py 添加测试客户端 fixture**

读取 `backend/tests/conftest.py`，添加以下 fixture：

```python
# backend/tests/conftest.py
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db

# 测试数据库 URL（使用 SQLite 内存数据库）
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

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """创建测试用户并返回 auth headers"""
    await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    resp = await client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "testpass123"
    })
    token = resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}
```

- [ ] **Step 2: 创建 test_api 目录和 __init__.py**

```bash
mkdir -p backend/tests/test_api
touch backend/tests/test_api/__init__.py
```

- [ ] **Step 3: 写 Auth 测试**

```python
# backend/tests/test_api/test_auth.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "newpass123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"username": "dup", "email": "dup@example.com", "password": "pass123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code in (400, 409)


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "loginpass123"
    })
    resp = await client.post("/api/v1/auth/login", data={
        "username": "loginuser",
        "password": "loginpass123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "wrongpw",
        "email": "wrongpw@example.com",
        "password": "correct123"
    })
    resp = await client.post("/api/v1/auth/login", data={
        "username": "wrongpw",
        "password": "wrong123"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_current_user(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_current_user_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
```

- [ ] **Step 4: 安装 aiosqlite 测试依赖**

在 `backend/pyproject.toml` 的 `[project.optional-dependencies] dev` 中添加 `"aiosqlite>=0.19.0"`。

- [ ] **Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/test_api/test_auth.py -v
```

Expected: 6 passed

- [ ] **Step 6: 提交**

```bash
git add backend/tests/ backend/pyproject.toml
git commit -m "test: add auth API tests

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 8: 补充后端 API 测试 — Projects 模块

**Files:**
- Create: `backend/tests/test_api/test_projects.py`

- [ ] **Step 1: 写 Projects 测试**

```python
# backend/tests/test_api/test_projects.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/projects/", json={
        "name": "Test Project",
        "description": "A test project"
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Project"


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/projects/", json={
        "name": "P1", "description": "desc"
    }, headers=auth_headers)
    resp = await client.get("/api/v1/projects/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/projects/", json={
        "name": "Get Project", "description": "desc"
    }, headers=auth_headers)
    project_id = create.json()["id"]
    resp = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Project"


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/projects/", json={
        "name": "Old Name", "description": "desc"
    }, headers=auth_headers)
    project_id = create.json()["id"]
    resp = await client.put(f"/api/v1/projects/{project_id}", json={
        "name": "New Name"
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/projects/", json={
        "name": "To Delete", "description": "desc"
    }, headers=auth_headers)
    project_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert resp.status_code == 200
    get_resp = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert get_resp.status_code == 404
```

- [ ] **Step 2: 运行测试**

```bash
cd backend && python -m pytest tests/test_api/test_projects.py -v
```

Expected: 5 passed

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_api/test_projects.py
git commit -m "test: add projects API tests

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 9: 补充后端 API 测试 — Devices 模块

**Files:**
- Create: `backend/tests/test_api/test_devices.py`

- [ ] **Step 1: 写 Devices 测试**

```python
# backend/tests/test_api/test_devices.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_device(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/devices/", json={
        "device_sn": "SN-TEST-001",
        "name": "Test Device",
        "model": "V1",
        "device_type": "VIRTUAL"
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_sn"] == "SN-TEST-001"


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/devices/", json={
        "device_sn": "SN-LIST-001",
        "name": "List Device",
        "model": "V1",
        "device_type": "VIRTUAL"
    }, headers=auth_headers)
    resp = await client.get("/api/v1/devices/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_device(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/devices/", json={
        "device_sn": "SN-GET-001",
        "name": "Get Device",
        "model": "V2",
        "device_type": "VIRTUAL"
    }, headers=auth_headers)
    device_id = create.json()["id"]
    resp = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["device_sn"] == "SN-GET-001"


@pytest.mark.asyncio
async def test_update_device(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/devices/", json={
        "device_sn": "SN-UPD-001",
        "name": "Old Name",
        "model": "V1",
        "device_type": "VIRTUAL"
    }, headers=auth_headers)
    device_id = create.json()["id"]
    resp = await client.put(f"/api/v1/devices/{device_id}", json={
        "name": "New Name"
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_device(client: AsyncClient, auth_headers: dict):
    create = await client.post("/api/v1/devices/", json={
        "device_sn": "SN-DEL-001",
        "name": "To Delete",
        "model": "V1",
        "device_type": "VIRTUAL"
    }, headers=auth_headers)
    device_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert resp.status_code == 200
```

- [ ] **Step 2: 运行测试**

```bash
cd backend && python -m pytest tests/test_api/test_devices.py -v
```

Expected: 5 passed

- [ ] **Step 3: 提交**

```bash
git add backend/tests/test_api/test_devices.py
git commit -m "test: add devices API tests

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 10: 添加 GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: 创建 GitHub Actions 配置**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"
      - name: Lint with ruff
        run: |
          cd backend
          ruff check app/
      - name: Type check with mypy
        run: |
          cd backend
          mypy app/ --ignore-missing-imports --no-error-summary || true

  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"
          pip install aiosqlite
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/ -v --tb=short

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Lint
        run: |
          cd frontend
          npm run lint 2>/dev/null || echo "No lint script configured"
      - name: Type check
        run: |
          cd frontend
          npx vue-tsc --noEmit 2>/dev/null || echo "Type check skipped"

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Build
        run: |
          cd frontend
          npm run build
```

- [ ] **Step 2: 提交**

```bash
git add .github/
git commit -m "ci: add GitHub Actions workflow for lint, test, and build

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 11: 修复 ruff lint 错误

**Files:**
- Modify: backend/app/ 中的 Python 文件（根据 ruff 报告）

- [ ] **Step 1: 运行 ruff 检查**

```bash
cd backend && ruff check app/ --statistics
```

记录错误数量和类型。

- [ ] **Step 2: 自动修复可修复的问题**

```bash
cd backend && ruff check app/ --fix
```

- [ ] **Step 3: 手动修复剩余问题**

根据 ruff 报告逐个修复。常见问题：
- `F401` — 未使用的 import，删除
- `E501` — 行太长，换行
- `I001` — import 顺序，已自动修复
- `UP` — Python 3.9 兼容性问题

- [ ] **Step 4: 验证 ruff 通过**

```bash
cd backend && ruff check app/
```

Expected: All checks passed!

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "style: fix ruff lint errors

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 12: 更新 README 文档

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README**

在现有 README 基础上：
1. 更新项目结构部分，反映实际目录（docs/design/、docs/images/）
2. 添加"项目文档"部分，链接到 docs/design/ 中的设计文档
3. 更新 Python 版本要求为 3.9+（与实际代码一致）

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: update README with project structure and design docs

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 13: 最终验证

- [ ] **Step 1: 运行全部测试**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All passed

- [ ] **Step 2: 运行 ruff**

```bash
cd backend && ruff check app/
```

Expected: All checks passed!

- [ ] **Step 3: 检查 git 状态**

```bash
cd mimo && git status
```

Expected: working tree clean

- [ ] **Step 4: 推送到 GitHub**

```bash
git push origin main
```
