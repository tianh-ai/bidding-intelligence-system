#!/bin/bash

# Docker 服务状态查看脚本

echo "==========================================="
echo "  标书智能系统 - 服务状态"
echo "==========================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行"
    exit 1
fi

# 显示容器状态
echo "📊 容器状态:"
docker compose ps
echo ""

# 检查各服务健康状况
echo "🏥 健康检查:"

# 后端
if curl -s http://localhost:8000/health > /dev/null; then
    echo "  ✅ 后端 API:    http://localhost:8000"
else
    echo "  ❌ 后端 API:    http://localhost:8000 (无响应)"
fi

# 前端
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "  ✅ 前端界面:    http://localhost:5173"
else
    echo "  ⚠️  前端界面:    http://localhost:5173 (可能未启动)"
fi

# PostgreSQL
if docker exec bidding_postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL:  localhost:5433"
else
    echo "  ❌ PostgreSQL:  localhost:5433 (连接失败)"
fi

# Redis
if docker exec bidding_redis redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Redis:       localhost:6380"
else
    echo "  ❌ Redis:       localhost:6380 (连接失败)"
fi

echo ""
echo "📝 常用命令:"
echo "  - 查看日志:     docker compose logs -f backend"
echo "  - 重启服务:     docker compose restart"
echo "  - 停止服务:     docker compose down"
echo "  - 启动服务:     ./docker-start.sh"
echo ""
