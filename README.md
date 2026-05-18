# MiMo - 智能货柜全链路测试平台

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Vue 3](https://img.shields.io/badge/Vue-3-brightgreen.svg)](https://vuejs.org/)

智能货柜质量基础设施（Quality Infrastructure），覆盖从用户操作到 AI 识别到支付扣款的全链路测试。

## 架构概览

```
Test Portal (Vue 3)
    │
    ├── API 测试引擎
    ├── IoT 仿真引擎 (L1/L2/L3)
    ├── AI 识别验证中心
    ├── Web/App 自动化
    ├── 真实设备农场
    ├── 第三方 Mock 平台
    └── 全链路 Trace
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia |
| 后端 | Python + FastAPI + SQLAlchemy + Celery |
| IoT 仿真 | Python + paho-mqtt + asyncio |
| AI 评测 | Python + OpenCV + MLflow |
| 数据库 | PostgreSQL + Redis + ClickHouse |
| 消息队列 | Kafka + RocketMQ |
| 搜索 | Elasticsearch |
| 容器化 | Docker + Kubernetes |
| 监控 | Prometheus + Grafana |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/<your-username>/mimo.git
cd mimo

# 2. 初始化环境
cp .env.example .env
make setup

# 3. 启动基础设施
make infra-up

# 4. 启动后端
make backend-dev

# 5. 启动前端
make frontend-dev
```

### Docker 启动

```bash
make docker-up
```

访问 http://localhost:3100

## 项目结构

```
mimo/
├── backend/           # FastAPI 后端服务
├── frontend/          # Vue 3 前端
├── iot-simulator/     # IoT 仿真服务
├── ai-evaluator/      # AI 评测服务
├── deploy/            # 部署配置
├── docs/              # 文档
└── scripts/           # 工具脚本
```

## 文档

- [架构设计](docs/architecture.md)
- [API 文档](docs/api.md) - 启动后访问 http://localhost:8100/docs
- [部署指南](docs/deployment.md)
- [开发指南](docs/development.md)

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

请确保：
- 代码通过现有测试
- 新功能包含测试用例
- 遵循项目代码规范

## 许可证

本项目基于 [MIT License](LICENSE) 开源。
