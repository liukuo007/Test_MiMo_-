# MiMo — 智能货柜全链路测试平台 架构文档

## 一、全局定位

面向 20 万台智能货柜设备的**全链路测试平台**，覆盖 IoT 设备测试、AI 识别评测、支付链路验证、质量门禁、缺陷管理，服务于测试、开发、产品、运营全员。

---

## 二、系统架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3 + TS + Vite)                      │
│  端口 3100 │ 22 个页面 │ 9 个 Pinia Store │ ECharts │ vue-flow DAG   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ /api/v1/* (Vite Proxy)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    后端 FastAPI (端口 8000/8100)                      │
│                                                                     │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐  │
│  │ 21 个    │ │ 4 个     │ │ 6 个     │ │ 4 个      │ │ 3 个     │  │
│  │ API 路由 │ │ Service  │ │ Engine   │ │ Mock 服务 │ │ Celery   │  │
│  │ 模块     │ │ 层       │ │ 引擎     │ │           │ │ Task     │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘ └────┬─────┘  │
│       │            │            │              │            │        │
│  ┌────┴────────────┴────────────┴──────────────┴────────────┴─────┐  │
│  │              Orchestrator (DAG 工作流编排引擎)                   │  │
│  │     dag.py │ executor.py │ scheduler.py │ resource_manager.py  │  │
│  └────────────────────────────┬───────────────────────────────────┘  │
│                               │                                      │
│  ┌────────────────────────────┴───────────────────────────────────┐  │
│  │                    IoT 子系统 (MQTT)                            │  │
│  │  mqtt_client.py │ virtual_device.py │ fault_injector.py        │  │
│  │  scenarios/ (normal │ chaos │ stress)                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Middleware: CORS │ Metrics │ ShadowTraffic │ Trace │ RequestLog     │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│PostgreSQL│ │ Redis  │ │Mosquitto│ │ WireMock│ │Celery Worker │
│   5432   │ │  6479  │ │  1883  │ │  8080   │ │  (3 queues)  │
└──────────┘ └────────┘ └────────┘ └────────┘ └──────────────┘
```

---

## 三、后端架构 (`backend/`)

### 3.1 目录结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口, lifespan, 中间件注册
│   ├── config.py            # pydantic_settings 配置中心
│   ├── database.py          # SQLAlchemy async + asyncpg
│   ├── celery_app.py        # Celery 实例 (3 队列: test/ai/report)
│   ├── dependencies.py      # FastAPI 依赖注入 (CurrentUser 等)
│   │
│   ├── api/v1/              # 21 个路由模块
│   │   ├── router.py        # 路由聚合入口
│   │   ├── auth.py          # 登录/注册/Token
│   │   ├── users.py         # 用户管理
│   │   ├── projects.py      # 项目管理
│   │   ├── devices.py       # 设备管理 (含虚拟设备、MQTT 控制)
│   │   ├── test_cases.py    # 用例管理
│   │   ├── test_tasks.py    # 任务编排 (DAG 配置)
│   │   ├── test_results.py  # 测试结果
│   │   ├── ai_verify.py     # AI 评测
│   │   ├── scenarios.py     # 场景工作台 (虚拟/真实设备、批量执行)
│   │   ├── smoke_test.py    # 一键冒烟测试
│   │   ├── dashboard.py     # 数据看板
│   │   ├── defects.py       # 缺陷管理 (含 MeterSphere 同步)
│   │   ├── traces.py        # 链路追踪
│   │   ├── quality_gate.py  # 质量门禁
│   │   ├── quality_report.py# 质量报告
│   │   ├── datasets.py      # 数据集管理
│   │   ├── settings.py      # 系统设置
│   │   ├── schedules.py     # 定时任务
│   │   ├── simulator.py     # 压测模拟器
│   │   ├── webhooks.py      # CI/CD Webhook
│   │   └── metersphere.py   # MeterSphere 集成
│   │
│   ├── models/              # 16 个 SQLAlchemy ORM 模型
│   │   ├── user.py          # User (admin/manager/tester/viewer)
│   │   ├── project.py       # Project
│   │   ├── device.py        # Device (REAL/VIRTUAL, 状态机)
│   │   ├── device_event.py  # DeviceEvent (11 种事件类型)
│   │   ├── test_case.py     # TestCase
│   │   ├── test_task.py     # TestTask + TestTaskStep
│   │   ├── test_result.py   # TestResult
│   │   ├── ai_model.py      # AIModel + AIModelVersion + AIEvaluation
│   │   ├── defect.py        # Defect
│   │   ├── trace.py         # Trace + TraceSpan
│   │   ├── scenario.py      # ScenarioTemplate + ScenarioBatch + ScenarioExecution
│   │   ├── dataset.py       # Dataset
│   │   ├── quality_gate.py  # QualityGateRule
│   │   ├── quality_report.py# QualityReport
│   │   ├── schedule.py      # Schedule
│   │   └── setting.py       # SystemSetting
│   │
│   ├── schemas/             # 16 个 Pydantic Schema (与模型 1:1)
│   │
│   ├── services/            # 4 个业务服务
│   │   ├── auth_service.py      # JWT 签发/验证, 密码哈希
│   │   ├── device_service.py    # 设备 CRUD, 虚拟设备批量创建
│   │   ├── quality_gate_service.py # 门禁规则评估
│   │   └── scheduler_service.py # APScheduler 定时任务调度
│   │
│   ├── engines/             # 6 个测试引擎
│   │   ├── iot_engine.py    # IoT 设备测试 (心跳/指令/事件)
│   │   ├── ai_engine.py     # AI 模型推理评测
│   │   ├── api_engine.py    # API 接口测试
│   │   ├── web_engine.py    # Web UI 自动化
│   │   ├── app_engine.py    # App 端测试
│   │   └── chaos_engine.py  # 混沌工程 (故障注入)
│   │
│   ├── orchestrator/        # DAG 工作流编排
│   │   ├── dag.py           # DAG 定义 (节点/边/条件分支/循环)
│   │   ├── executor.py      # 节点执行器 (按类型分发到各 Engine)
│   │   ├── scheduler.py     # DAG 调度 (拓扑排序/并发控制)
│   │   └── resource_manager.py # 设备资源锁定/释放
│   │
│   ├── tasks/               # 3 个 Celery 异步任务
│   │   ├── test_execution.py    # 异步执行测试任务
│   │   ├── ai_evaluation.py     # 异步 AI 评测
│   │   └── report_generation.py # 异步报告生成
│   │
│   ├── iot/                 # IoT 子系统
│   │   ├── mqtt_client.py       # paho-mqtt 客户端 (单例)
│   │   ├── virtual_device.py    # 虚拟设备模型
│   │   ├── device_state.py      # 设备状态机
│   │   ├── fault_injector.py    # 故障注入器
│   │   ├── protocol.py          # IoT 协议定义
│   │   └── scenarios/           # normal/chaos/stress 场景
│   │
│   ├── mock/                # 3 个 Mock 服务 (通过 WireMock 路由)
│   │   ├── payment_mock.py  # 支付 Mock (微信/支付宝/信用卡)
│   │   ├── sms_mock.py      # 短信 Mock
│   │   └── sso_mock.py      # SSO Mock
│   │
│   └── core/                # 横切关注点
│       ├── security.py          # JWT 工具函数
│       ├── exceptions.py        # 自定义异常 (NotFoundError 等)
│       ├── middleware.py         # TraceMiddleware, RequestLoggingMiddleware
│       ├── metrics.py           # Prometheus 指标中间件
│       ├── shadow_traffic.py    # 流量染色中间件 (Takin 风格)
│       └── logging.py           # structlog 日志配置
│
├── integrations/            # 4 个外部工具集成
│   ├── wiremock/mappings/   # WireMock API Stub (支付/SMS/SSO)
│   ├── locust/locustfile.py # Locust 压测脚本
│   ├── metersphere/sync_to_ms.py # MeterSphere 同步
│   └── testkube/custom-test-crds.yaml # K8s 测试 CRD
│
├── alembic/                 # 数据库迁移
├── scripts/seed_data.py     # 种子数据
└── tests/                   # 单元测试 (test_api/test_engines/test_services)
```

### 3.2 核心数据流

```
用户请求 → API 路由 → Service 层 → Engine/Orchestrator → 设备/Mock/AI
                ↓
         Celery 异步任务 (test/ai/report 队列)
                ↓
         数据库持久化 + 事件上报
```

### 3.3 API 端点统计 (92 个路由)

| 模块 | 端点数 | 核心功能 |
|------|--------|---------|
| auth | 3 | 登录/注册/当前用户 |
| users | 4 | 用户 CRUD |
| projects | 5 | 项目 CRUD |
| devices | 8 | 设备管理 + MQTT 控制 + 虚拟设备 |
| test_cases | 5 | 用例 CRUD |
| test_tasks | 7 | 任务 CRUD + 执行/取消 + DAG 配置 |
| test_results | 3 | 结果查询 |
| ai_verify | 5 | 模型/评测/对比 |
| scenarios | 5 | 模板/目录/运行/批量/执行历史 |
| smoke_test | 1 | 一键冒烟 |
| dashboard | 4 | 概览/趋势/雷达/告警 |
| defects | 5 | 缺陷 CRUD + 统计 |
| traces | 2 | 链路查看 |
| quality_gate | 3 | 门禁规则 |
| quality_report | 3 | 报告生成/查询 |
| datasets | 4 | 数据集 CRUD |
| settings | 3 | 系统设置 |
| schedules | 5 | 定时任务 CRUD + 触发 |
| webhooks | 2 | CI/CD 回调 |
| metersphere | 2 | MS 同步 |
| simulator | 3 | 压测控制 |

---

## 四、前端架构 (`frontend/`)

### 4.1 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Vue 3.4 + TypeScript 5.3 |
| 构建 | Vite 5 |
| UI 库 | Element Plus 2.5 (全量图标注册) |
| 状态 | Pinia 2.1 (9 个 Store) |
| 路由 | Vue Router 4.2 (22 个页面) |
| HTTP | Axios (封装 request.ts) |
| 图表 | ECharts 5.5 + vue-echarts 6 |
| DAG | @vue-flow/core 1.26 |
| 样式 | SCSS |
| 测试 | Vitest |

### 4.2 目录结构

```
frontend/src/
├── main.ts                  # 入口: Pinia + Router + ElementPlus + Icons
├── App.vue
├── router/index.ts          # 22 路由, beforeEach 鉴权守卫
│
├── api/                     # 19 个 API 模块 (axios 封装)
│   └── request.ts           # 统一请求拦截 (Bearer Token, 错误处理)
│
├── stores/                  # 9 个 Pinia Store (Composition API)
│   ├── user.ts              # 登录状态, Token, 用户信息
│   ├── project.ts           # 当前项目
│   ├── device.ts / ai.ts / defect.ts / quality.ts / ...
│
├── views/                   # 24 个页面组件
│   ├── Layout.vue           # 侧边栏 + 顶栏 + router-view
│   ├── Login.vue            # 登录页
│   ├── dashboard/Index.vue  # 数据看板 (ECharts + 冒烟测试)
│   ├── device/Farm.vue      # 设备农场 (卡片列表 + MQTT 控制)
│   ├── device/Detail.vue    # 设备详情 (事件时间线)
│   ├── test_task/DAGEditor.vue # DAG 可视化编排 (vue-flow)
│   ├── scenario/Workbench.vue  # 场景工作台 (模板卡片 + 参数配置)
│   └── ...                  # 其余 17 个页面
│
├── components/              # 公共组件
│   ├── common/StatusBadge.vue
│   └── device/DeviceCard.vue
│
├── composables/             # 组合式函数
│   ├── useAuth.ts
│   └── useWebSocket.ts      # WebSocket 实时推送
│
├── types/                   # TypeScript 类型定义
│   ├── api.ts / device.ts / test.ts / ai.ts
│
├── utils/                   # 工具函数
│   ├── constants.ts         # 状态映射表 (DEVICE_STATUS_MAP 等)
│   └── format.ts            # 日期/时长格式化
│
└── styles/                  # 全局样式
    ├── global.scss
    └── variables.scss
```

### 4.3 页面路由一览

| 路径 | 页面 | 功能 |
|------|------|------|
| `/dashboard` | 数据看板 | 统计卡片 + 趋势图 + 雷达图 + 告警 + 冒烟测试 |
| `/scenarios` | 场景工作台 | 6 个场景模板卡片, 参数配置, 一键/批量运行 |
| `/projects` | 项目管理 | 项目列表/详情 |
| `/devices` | 设备农场 | 设备卡片, 状态筛选, MQTT 控制 |
| `/devices/:id` | 设备详情 | 设备信息 + 事件时间线 |
| `/test-cases` | 用例管理 | 用例列表/编辑 |
| `/test-tasks` | 任务管理 | 任务列表/创建/详情 |
| `/test-tasks/dag-editor` | DAG 编排 | vue-flow 可视化拖拽编排 |
| `/ai/datasets` | 数据集 | AI 数据集管理 |
| `/ai/evaluations` | AI 评测 | 模型评测任务 |
| `/ai/compare` | 模型对比 | 多模型指标对比 |
| `/defects` | 缺陷管理 | 缺陷生命周期 |
| `/quality/gate` | 质量门禁 | 门禁规则配置 |
| `/quality/report` | 质量报告 | 报告生成/查看 |
| `/schedules` | 定时任务 | Cron 定时配置 |
| `/settings` | 系统设置 | 全局配置 |
| `/traces/:id` | 链路追踪 | Trace/Span 可视化 |

---

## 五、基础设施层

### 5.1 Docker 服务编排 (docker-compose.yml)

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                         │
│                                                             │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐  │
│  │ backend  │  │  celery    │  │ frontend │  │    ai-    │  │
│  │ :8100    │  │  worker    │  │ :3100    │  │ evaluator │  │
│  │ FastAPI  │  │  3 queues  │  │ Vite Dev │  │  :8200    │  │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │              │              │         │
│  ┌────┴──────────────┴──────────────┴──────────────┴──────┐  │
│  │                    共享网络                             │  │
│  └──┬────────┬────────┬────────┬────────┬────────┬────────┘  │
│     │        │        │        │        │        │           │
│  ┌──┴──┐ ┌──┴──┐ ┌───┴───┐ ┌──┴───┐ ┌──┴───┐ ┌─┴──────┐   │
│  │ PG  │ │Redis│ │Mosquitto│ │WireMock│ │ iot- │ │        │   │
│  │:5432│ │:6479│ │ :1883  │ │ :8080 │ │simul.│ │        │   │
│  └─────┘ └─────┘ └────────┘ └──────┘ └──────┘ └────────┘   │
└─────────────────────────────────────────────────────────────┘
```

| 服务 | 镜像/构建 | 端口 | 职责 |
|------|----------|------|------|
| **backend** | ./backend (Python 3.11) | 8100→8000 | FastAPI 主服务 |
| **celery-worker** | ./backend | — | 异步任务 (test/ai/report) |
| **frontend** | ./frontend (Node 18) | 3100 | Vite 开发服务器 |
| **ai-evaluator** | ./ai-evaluator | 8200 | ML 模型推理评测 |
| **iot-simulator** | ./iot-simulator | — | 10 台虚拟设备仿真 |
| **wiremock** | wiremock:3.5.4-alpine | 8080 | 第三方 API Mock |
| **mosquitto** | eclipse-mosquitto:2 | 1883 | MQTT Broker |
| **postgres** | postgres:15-alpine | 5432 | 主数据库 |
| **redis** | redis:7-alpine | 6479→6379 | 缓存 + Celery Broker |

### 5.2 数据存储

| 存储 | 用途 | 数据 |
|------|------|------|
| **PostgreSQL** | 主库 | 16 张表, SQLAlchemy async + asyncpg |
| **Redis** | 缓存 + 消息队列 | Celery Broker/Result, 会话缓存 |
| **Mosquitto** | MQTT 消息 | 设备心跳/事件/指令 (device/{sn}/...) |

### 5.3 消息协议 (MQTT Topic)

```
device/{device_sn}/heartbeat    # 设备 → 服务端: 心跳上报
device/{device_sn}/event        # 设备 → 服务端: 事件上报
device/{device_sn}/command      # 服务端 → 设备: 指令下发
```

---

## 六、外部集成

| 工具 | 集成方式 | 用途 |
|------|---------|------|
| **WireMock** | Docker + JSON Mapping | 支付/SMS/SSO API Mock |
| **Locust** | locustfile.py | 压力测试脚本 |
| **MeterSphere** | sync_to_ms.py | 缺陷/用例/结果双向同步 |
| **TestKube** | CRD YAML | K8s 原生测试编排 |
| **Takin** | shadow_traffic.py | 流量染色中间件 |

---

## 七、核心业务模型关系

```
User ──┬── 创建 ──→ Project ── 包含 ──→ Device (20万台)
       │                                  │
       ├── 创建 ──→ TestCase              ├── DeviceEvent (事件流)
       │              │                   │
       ├── 创建 ──→ TestTask ── 包含 ──→ TestTaskStep
       │              │
       │              ├── 执行 → TestResult
       │              │
       │              └── DAG 编排 → Orchestrator → Engine
       │
       ├── 创建 ──→ ScenarioTemplate ── 批量执行 ──→ ScenarioBatch
       │                                              │
       │                                         ScenarioExecution
       │
       ├── 创建 ──→ Defect ── 同步 → MeterSphere
       │
       └── 配置 ──→ QualityGateRule
                       │
                    QualityReport
```

---

## 八、6 个测试引擎职责

| 引擎 | 文件 | 测试对象 |
|------|------|---------|
| **IoT** | iot_engine.py | 设备心跳、指令下发、事件采集、温控 |
| **AI** | ai_engine.py | 模型推理精度、召回率、混淆矩阵 |
| **API** | api_engine.py | 接口请求/响应/断言/性能 |
| **Web** | web_engine.py | 浏览器 UI 自动化 (Selenium/Playwright) |
| **App** | app_engine.py | 移动端 App 自动化 |
| **Chaos** | chaos_engine.py | 网络延迟、服务宕机、磁盘满等故障注入 |

---

## 九、DAG 编排能力

```
节点类型:
  ├── test_case   → 调用对应 Engine 执行测试
  ├── condition   → 条件分支 (12 种运算符: eq/neq/gt/regex/in/...)
  ├── loop        → 循环执行 (支持 break 条件)
  ├── delay       → 等待
  └── notify      → 通知

特性:
  ├── 拓扑排序执行
  ├── 条件分支路由
  ├── 循环 + 提前退出
  ├── 共享 context 字典
  └── 节点间数据传递
```

---

## 十、Makefile 快捷命令

```bash
make setup          # 安装依赖
make infra-up       # 启动基础设施 (PG + Redis + Mosquitto)
make backend-dev    # 启动后端开发服务
make frontend-dev   # 启动前端开发服务
make celery-worker  # 启动 Celery Worker
make docker-up      # 一键启动所有服务
make seed           # 写入种子数据
make test           # 运行测试
make db-migrate     # 生成迁移
```

---

## 十一、场景工作台（业务场景测试）

### 11.1 功能定位

零代码业务场景测试工作台，让非技术人员也能一键发起全链路业务测试。

### 11.2 预设场景模板

| 场景 | 分类 | 步骤数 | 说明 |
|------|------|--------|------|
| 常规购物全链路 | 正常 | 4 | 扫码→识别→关门→扣款成功 |
| 异常：余额不足 | 异常 | 4 | 扫码→识别→关门→扣款失败 |
| 异常：关门超时 | 异常 | 3 | 扫码→等待超时→系统报警 |
| 多商品混合购物 | 正常 | 6 | 多 SKU 识别+合并结算 |
| AI 误识别告警 | 异常 | 4 | 低置信度→触发人工复核 |
| 设备离线恢复 | 异常 | 4 | 心跳→断连→重连→恢复 |

### 11.3 参数化配置

每个场景运行前可配置：
- **货柜型号**: V1 标准柜 / V2 双温柜 / V3 旗舰柜
- **商品选择**: 8 种商品 (可乐/薯片/水/果汁/面包/牛奶/士力架/冰红茶)
- **购买数量**: 1-10
- **支付方式**: 微信/支付宝/信用卡/刷脸支付

### 11.4 运行模式

| 模式 | 说明 |
|------|------|
| 虚拟设备运行 | 自动创建沙箱设备，互不干扰，适合开发验证 |
| 真实设备运行 | 从 20 万台设备中手动选择，MQTT 下发指令，全链路验证 |
| 批量巡检 | 选择多台设备，并行执行同一场景，统计通过率 |

### 11.5 设备选择逻辑

```
手动指定:
  ├── 搜索框输入设备 SN / 名称
  ├── 按 型号 + 区域 + 状态 组合筛选
  └── 从设备列表中勾选一台或多台

自动匹配规则:
  ├── 只选 online 状态
  ├── 7 天内未巡检的优先
  ├── 温度异常的设备优先
  └── 日均订单高的设备优先
```

---

## 十二、冒烟测试

一键式全链路冒烟测试，3 个步骤顺序执行：

| 步骤 | 名称 | 说明 |
|------|------|------|
| 1 | 虚拟设备初始化 | 创建/激活 SMOKE-VIRTUAL-001 设备 |
| 2 | 模拟购物事件 | 上报 DOOR_OPEN → ITEM_DETECTED → DOOR_CLOSE |
| 3 | 校验支付 Mock | 调用 WireMock 创建订单+查询状态 |

入口：数据看板页面顶部「一键启动冒烟测试」按钮。

---

## 十三、技术约束

| 约束 | 说明 |
|------|------|
| Python 版本 | 3.9+ (需 `from __future__ import annotations`) |
| 类型注解 | 使用 `Optional[X]` 而非 `X \| None` |
| ORM 风格 | SQLAlchemy 2.0 声明式 (`Mapped[T]` + `mapped_column`) |
| Schema 风格 | Pydantic BaseModel + `from_attributes = True` |
| 前端风格 | Vue 3 Composition API (`<script setup lang="ts">`) |
| 代理配置 | Vite `/api` → `http://127.0.0.1:8100` |
