# MiMo 架构设计

详细架构设计请参考：

- [智能货柜全链路测试平台设计](../视达.md)
- [补充设计](../视达-补充设计.md)

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Element Plus |
| 后端 | Python + FastAPI + SQLAlchemy + Celery |
| IoT 仿真 | Python + paho-mqtt + asyncio |
| AI 评测 | Python + OpenCV |
| 数据库 | PostgreSQL + Redis + ClickHouse |
| 消息队列 | Kafka |
| 搜索 | Elasticsearch |
| 容器化 | Docker + Kubernetes |
| 监控 | Prometheus + Grafana |
