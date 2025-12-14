#!/bin/bash
# 本地开发环境启动脚本 - 避免端口冲突

set -e

echo "💻 启动本地开发环境..."
echo ""

# 0. 运行配置守护检查
if [ -f "./config-guard.sh" ]; then
    echo "🛡️  运行配置守护检查..."
    chmod +x ./config-guard.sh
    ./config-guard.sh
    echo ""
fi

# 1. 停止 Docker 前后端服务（保留数据库）
echo "🛑 停止 Docker 前后端服务..."
docker-compose stop backend frontend 2>/dev/null || true

# 2. 确保数据库和 Redis 运行
echo "🗄️  启动数据库和 Redis..."
docker-compose up -d postgres redis
sleep 3

# 3. 检查并释放端口
echo "🔍 检查端口占用..."
if lsof -i :8000 >/dev/null 2>&1; then
    echo "   ⚠️  端口 8000 被占用，正在释放..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -i :5173 >/dev/null 2>&1; then
    echo "   ⚠️  端口 5173 被占用，正在释放..."
    lsof -ti :5173 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 4. 更新前端配置指向本地后端
echo "⚙️  配置前端连接本地后端..."
if [ -f "frontend/.env" ]; then
    if grep -q "VITE_API_URL=http://localhost:18888" frontend/.env; then
        sed -i '' 's|VITE_API_URL=http://localhost:18888|VITE_API_URL=http://localhost:8000|g' frontend/.env
        echo "   ✅ 已更新 frontend/.env 指向本地后端"
    fi
fi

# 5. 启动后端
echo "🚀 启动后端服务 (端口 8000)..."
cd backend
python3 main.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 6. 等待后端就绪
echo "⏳ 等待后端启动..."
for i in {1..15}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "   ✅ 后端运行正常"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "   ❌ 后端启动失败，查看日志: tail -50 /tmp/backend.log"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 7. 启动前端
echo "🚀 启动前端服务 (端口 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 3

# 8. 显示访问地址
echo ""
echo "✨ 本地开发环境已启动："
echo "   📱 前端: http://localhost:5173"
echo "   🔧 后端API: http://localhost:8000"
echo "   📚 API文档: http://localhost:8000/docs"
echo "   🗄️  数据库: localhost:5433 (Docker)"
echo "   💾 Redis: localhost:6380 (Docker)"
echo ""
echo "💡 提示："
echo "   - 后端日志: tail -f /tmp/backend.log"
echo "   - 停止服务: Ctrl+C 或 pkill -f 'python3 main.py'"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "🛑 停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ 已停止"
}

trap cleanup EXIT INT TERM

# 保持脚本运行
wait
