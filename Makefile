.PHONY: help setup infra-up infra-down backend-dev frontend-dev celery-worker docker-up docker-down test lint

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## 初始化开发环境
	cp -n .env.example .env 2>/dev/null || true
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install
	@echo "环境初始化完成"

infra-up: ## 启动基础设施 (PostgreSQL, Redis, Kafka, ES, EMQX)
	docker-compose -f deploy/docker/docker-compose.dev.yml up -d
	@echo "基础设施已启动"

infra-down: ## 停止基础设施
	docker-compose -f deploy/docker/docker-compose.dev.yml down

backend-dev: ## 启动后端开发服务器
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8100

frontend-dev: ## 启动前端开发服务器
	cd frontend && npm run dev

iot-dev: ## 启动 IoT 仿真服务
	cd iot-simulator && python -m simulator.main

ai-dev: ## 启动 AI 评测服务
	cd ai-evaluator && python -m evaluator.main

celery-worker: ## 启动 Celery Worker
	cd backend && celery -A app.celery_app worker --loglevel=info -Q test,ai,report,celery -c 4

docker-up: ## Docker Compose 启动全部服务
	docker-compose -f deploy/docker/docker-compose.yml up -d --build

docker-down: ## Docker Compose 停止全部服务
	docker-compose -f deploy/docker/docker-compose.yml down

test: ## 运行全部测试
	cd backend && pytest
	cd frontend && npm run test

test-backend: ## 运行后端测试
	cd backend && pytest -v

test-frontend: ## 运行前端测试
	cd frontend && npm run test

lint: ## 代码检查
	cd backend && ruff check . && mypy app
	cd frontend && npm run lint

format: ## 代码格式化
	cd backend && ruff format .
	cd frontend && npm run format

db-migrate: ## 生成数据库迁移
	cd backend && alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## 执行数据库迁移
	cd backend && alembic upgrade head

db-downgrade: ## 回滚数据库迁移
	cd backend && alembic downgrade -1

seed: ## 初始化测试数据
	cd backend && python scripts/seed_data.py

clean: ## 清理临时文件
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/dist frontend/node_modules/.cache
