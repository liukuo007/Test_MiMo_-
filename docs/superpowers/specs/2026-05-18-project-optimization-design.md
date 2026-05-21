# MiMo 项目优化设计文档

## 目标

将 `/Users/liuwenzhu/Desktop/视达` 文件夹从散落的原型+文档，整理为一个规范的开源项目，并持续完善工程化能力和功能迭代。

## 现状

| 类别 | 内容 | 状态 |
|------|------|------|
| `mimo/` | 主项目（Vue 3 + FastAPI + IoT 仿真） | 功能完整，已推 GitHub |
| `test/` | 早期 MVP（React + MySQL + Kafka） | 已被 mimo 取代，代码不完整 |
| 根目录文档 | 需求.txt、新架构方案.md、视达.md 等 | 散落未归档 |
| 根目录图片 | 架构图、参考图 | 未整理 |

## Phase 1: 文件夹整理

### 1.1 删除 `test/` 目录

- 原因：早期 MVP 原型，使用 React + MySQL + Kafka 技术栈，已被 `mimo/`（Vue 3 + PostgreSQL + MQTT）完全取代
- 包含 `node_modules/` 和 `venv/`，体积大且无用

### 1.2 归档设计文档

将根目录文档移入 `mimo/docs/design/`：

| 源文件 | 目标位置 | 说明 |
|--------|----------|------|
| `需求.txt` | `mimo/docs/design/requirements.md` | 原始需求文档 |
| `新架构方案.md` | `mimo/docs/design/architecture-v2.md` | P8 级架构方案 |
| `视达.md` | `mimo/docs/design/architecture-overview.md` | 架构总览 |
| `视达-补充设计.md` | `mimo/docs/design/architecture-supplement.md` | 补充设计 |
| `E2E测试平台架构总结.md` | `mimo/docs/design/e2e-architecture-summary.md` | MVP 架构总结 |
| `平台演示介绍文档.md` | `mimo/docs/design/demo-guide.md` | 演示介绍 |
| `图片信息总结.md` | `mimo/docs/design/image-notes.md` | 图片信息总结 |

### 1.3 整理图片

将根目录图片移入 `mimo/docs/images/`：

- `c30933aa83afe912efa6e653a4063da6.jpg`
- `161f69d15f6409891e0ac86860cc2962.jpg`
- `3c071fb0e26e536ea0ce0ddf2c9641be.jpg`
- `e9523db6e6903358c64dba4a18fe786b.png`
- `新录音.m4a`

### 1.4 清理临时文件

- `.DS_Store`
- `test/` 删除后不残留

### 1.5 提交到 Git

所有变更提交到 mimo 仓库的 main 分支。

## Phase 2: 工程化完善

### 2.1 单元测试

补充 backend 测试：

- `tests/test_api/` — API 端点测试（使用 httpx.AsyncClient）
- `tests/test_services/` — Service 层测试
- `tests/test_engines/` — Engine 层测试

### 2.2 CI/CD

添加 GitHub Actions：

- `.github/workflows/ci.yml` — lint + test + build
- Python: ruff check + pytest
- Frontend: eslint + vitest + build

### 2.3 代码质量工具

- Python: `ruff` (替代 flake8 + isort + black)
- Frontend: `eslint` + `prettier`

### 2.4 文档完善

- README 添加实际功能截图
- 添加 CHANGELOG.md
- 添加 CONTRIBUTING.md

## Phase 3: P8 功能迭代

根据 `新架构方案.md`，继续实现未落地的功能。优先级：

1. 质量健康分系统（7 维加权评分）
2. 环境治理中心（环境快照、健康检测）
3. 设备资源网格（标签化、池化、调度）
4. 稳定性治理（Flaky 检测、故障聚类）
5. AI 测试助手（故障分析、测试生成）
6. 质量闭环（自动检测→定位→创建缺陷→回归）
7. 全球区域运营（多区域质量地图）
8. 增强压测（流量模型、数字孪生）

## 验证方案

- Phase 1: 文件夹结构清晰，根目录只剩 `mimo/` 和整理后的文档
- Phase 2: `make test` 通过，CI 绿色，代码无 lint 错误
- Phase 3: 每个功能模块有对应的 API + 前端页面 + 测试
