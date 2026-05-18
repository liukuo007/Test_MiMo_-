# 开发指南

## 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

## 快速开始

```bash
# 1. 初始化环境
make setup

# 2. 启动基础设施
make infra-up

# 3. 初始化数据库
make db-upgrade
make seed

# 4. 启动后端
make backend-dev

# 5. 启动前端
make frontend-dev
```

## 项目结构

```
backend/
├── app/
│   ├── api/v1/        # API 路由
│   ├── models/        # 数据库模型
│   ├── schemas/       # Pydantic 模型
│   ├── services/      # 业务逻辑
│   ├── engines/       # 测试引擎
│   ├── orchestrator/  # 任务编排
│   ├── iot/           # IoT 仿真
│   ├── mock/          # Mock 服务
│   ├── core/          # 核心工具
│   └── tasks/         # 异步任务
├── tests/
└── scripts/
```

## 添加新 API

1. 在 `models/` 中定义数据库模型
2. 在 `schemas/` 中定义请求/响应模型
3. 在 `services/` 中实现业务逻辑
4. 在 `api/v1/` 中定义路由
5. 在 `api/v1/router.py` 中注册路由
