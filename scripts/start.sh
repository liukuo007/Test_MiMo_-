#!/bin/bash
set -e

echo "=== 启动 MiMo 服务 ==="

# 启动基础设施
echo "启动基础设施..."
docker-compose -f deploy/docker/docker-compose.dev.yml up -d

# 等待数据库就绪
echo "等待数据库就绪..."
sleep 5

# 初始化数据库
echo "初始化数据库..."
cd backend && python scripts/seed_data.py && cd ..

# 启动后端
echo "启动后端服务..."
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8100 &
BACKEND_PID=$!

# 启动前端
echo "启动前端服务..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "=== 服务已启动 ==="
echo "后端: http://localhost:8100"
echo "前端: http://localhost:3100"
echo "API 文档: http://localhost:8100/docs"

wait $BACKEND_PID $FRONTEND_PID
