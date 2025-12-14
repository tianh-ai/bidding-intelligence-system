#!/bin/bash
# 端口占用检查脚本

echo "🔍 端口占用情况检查"
echo "===================="
echo ""

check_port() {
    PORT=$1
    SERVICE=$2
    
    if lsof -i :$PORT >/dev/null 2>&1; then
        echo "❌ 端口 $PORT ($SERVICE) 被占用："
        lsof -i :$PORT | grep LISTEN
        echo ""
    else
        echo "✅ 端口 $PORT ($SERVICE) 空闲"
    fi
}

# 检查关键端口
check_port 8000 "本地后端"
check_port 5173 "本地前端"
check_port 18888 "Docker后端"
check_port 13000 "Docker前端"
check_port 5433 "PostgreSQL"
check_port 6380 "Redis"

echo ""
echo "🐳 Docker 容器状态："
echo "===================="
docker-compose ps 2>/dev/null || echo "Docker Compose 未运行"

echo ""
echo "💡 清理建议："
echo "   - 停止本地进程: pkill -f 'python3 main.py' && pkill -f 'vite'"
echo "   - 停止 Docker: docker-compose down"
echo "   - 释放特定端口: lsof -ti :8000 | xargs kill -9"
