#!/bin/bash
# Docker 环境启动脚本 - 避免端口冲突

set -e

echo "🐳 启动 Docker 环境..."
echo ""

# 0. 运行配置守护检查
if [ -f "./config-guard.sh" ]; then
    echo "🛡️  运行配置守护检查..."
    chmod +x ./config-guard.sh
    ./config-guard.sh
    echo ""
fi

# 1. 停止本地开发进程
echo "📦 停止本地开发进程..."
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "vite.*5173" 2>/dev/null || true
sleep 1

# 2. 检查并更新前端配置
echo "⚙️  配置前端连接 Docker 后端..."
if [ -f "frontend/.env" ]; then
    if grep -q "VITE_API_URL=http://localhost:8000" frontend/.env; then
        sed -i '' 's|VITE_API_URL=http://localhost:8000|VITE_API_URL=http://localhost:18888|g' frontend/.env
        echo "   ✅ 已更新 frontend/.env 指向 Docker 后端"
    fi
fi

# 3. 启动 Docker Compose
echo "🚀 启动 Docker 容器..."
docker-compose up -d

# 4. 等待服务就绪
echo "⏳ 等待服务启动..."
sleep 8

# 5. 健康检查
echo ""
echo "🔍 健康检查..."
if curl -s http://localhost:18888/health | grep -q "healthy"; then
    echo "   ✅ 后端运行正常 (端口 18888)"
else
    echo "   ❌ 后端未就绪，请检查日志: docker-compose logs backend"
fi

if curl -s http://localhost:13000 >/dev/null 2>&1; then
    echo "   ✅ 前端运行正常 (端口 13000)"
else
    echo "   ❌ 前端未就绪，请检查日志: docker-compose logs frontend"
fi

# 6. 显示访问地址
echo ""
echo "✨ 服务已启动："
echo "   📱 前端: http://localhost:13000"
echo "   🔧 后端API: http://localhost:18888"
echo "   📚 API文档: http://localhost:18888/docs"
echo "   🗄️  数据库: localhost:5433"
echo "   💾 Redis: localhost:6380"
echo ""
echo "💡 提示："
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo ""
