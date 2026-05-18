#!/bin/bash
set -e

echo "=== MiMo 环境初始化 ==="

# 复制环境变量
if [ ! -f .env ]; then
    cp .env.example .env
    echo "已创建 .env 文件"
fi

# 安装后端依赖
echo "安装后端依赖..."
cd backend && pip install -e ".[dev]" && cd ..

# 安装前端依赖
echo "安装前端依赖..."
cd frontend && npm install && cd ..

echo "=== 初始化完成 ==="
