#!/bin/bash

# Docker 一键启动脚本
# 启动所有服务（PostgreSQL + Redis + 后端 + 前端）

set -e

echo "========================================="
echo "  标书智能系统 - Docker 启动"
echo "========================================="

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi

# 停止旧容器
echo ""
echo "🧹 清理旧容器..."
docker compose down 2>/dev/null || true

# 构建并启动所有服务
echo ""
echo "🚀 启动 Docker 服务..."
docker compose up -d --build

# 等待服务就绪
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker compose ps

echo ""
echo "========================================="
echo "  ✅ 启动完成！"
echo "========================================="
echo "  📦 PostgreSQL: localhost:5433"
echo "  🔴 Redis:      localhost:6380"
echo "  🐍 后端 API:   http://localhost:8000"
echo ""
echo "  📝 查看日志:"
echo "     docker compose logs -f backend"
echo ""
echo "  🛑 停止服务:"
echo "     docker compose down"
echo "========================================="

# 显示后端日志
echo ""
echo "📋 后端日志（Ctrl+C 退出）:"
docker-compose logs -f backend
