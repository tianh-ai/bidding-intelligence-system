#!/bin/bash
# 完整性检查系统 - 定期验证系统状态

set -e

echo "🔍 系统完整性检查"
echo "===================="
echo ""

FAILED=0

# 1. 检查关键文件是否存在
echo "📁 检查关键文件..."
check_file() {
    if [ -f "$1" ]; then
        echo "  ✅ $1"
    else
        echo "  ❌ $1 缺失！"
        FAILED=$((FAILED + 1))
    fi
}

check_file "backend/.env"
check_file "frontend/.env"
check_file "docker-compose.yml"
check_file "config-guard.sh"
check_file "backend/requirements.snapshot.txt"
check_file "AI_ASSISTANT_RULES.md"
check_file "ENVIRONMENT_SNAPSHOT.md"

echo ""

# 2. 检查 Docker 容器健康状态
echo "🐳 检查 Docker 容器..."
UNHEALTHY=$(docker-compose ps --format json | jq -r 'select(.Health != "healthy" and .Health != "") | .Name' 2>/dev/null)
if [ -z "$UNHEALTHY" ]; then
    echo "  ✅ 所有容器健康"
else
    echo "  ❌ 不健康的容器: $UNHEALTHY"
    FAILED=$((FAILED + 1))
fi

echo ""

# 3. 检查服务可访问性
echo "🌐 检查服务可访问性..."

# 后端健康检查
if curl -s http://localhost:18888/health | grep -q "healthy"; then
    echo "  ✅ 后端 API (18888)"
else
    echo "  ❌ 后端 API 不可访问"
    FAILED=$((FAILED + 1))
fi

# 前端可访问性
if curl -s -I http://localhost:13000 | grep -q "200 OK"; then
    echo "  ✅ 前端 Web (13000)"
else
    echo "  ❌ 前端不可访问"
    FAILED=$((FAILED + 1))
fi

# 数据库连接
if PGPASSWORD=postgres123 psql -h localhost -p 5433 -U postgres -d bidding_db -c "SELECT 1;" >/dev/null 2>&1; then
    echo "  ✅ 数据库 (5433)"
else
    echo "  ❌ 数据库连接失败"
    FAILED=$((FAILED + 1))
fi

# Redis 连接
if redis-cli -h localhost -p 6380 ping 2>/dev/null | grep -q "PONG"; then
    echo "  ✅ Redis (6380)"
else
    echo "  ❌ Redis 连接失败"
    FAILED=$((FAILED + 1))
fi

echo ""

# 4. 检查配置一致性
echo "⚙️  检查配置一致性..."
if ./config-guard.sh > /tmp/integrity-config-check.log 2>&1; then
    echo "  ✅ 配置一致"
else
    echo "  ⚠️  配置有差异（已自动修复）"
    grep "⚠️" /tmp/integrity-config-check.log || true
fi

echo ""

# 5. 检查磁盘空间
echo "💾 检查磁盘空间..."
SSD_USAGE=$(df -h /Volumes/ssd | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$SSD_USAGE" -lt 80 ]; then
    echo "  ✅ SSD 使用率: ${SSD_USAGE}%"
else
    echo "  ⚠️  SSD 使用率过高: ${SSD_USAGE}%"
fi

echo ""

# 6. 检查 Python 环境变化
echo "🐍 检查 Python 环境..."
if pip3 freeze | diff -q - backend/requirements.snapshot.txt >/dev/null 2>&1; then
    echo "  ✅ Python 包无变化"
else
    echo "  ⚠️  Python 包已变更"
    NEW_PKGS=$(comm -13 <(sort backend/requirements.snapshot.txt) <(sort <(pip3 freeze)) | head -3)
    if [ -n "$NEW_PKGS" ]; then
        echo "  新增包: $NEW_PKGS"
    fi
fi

echo ""

# 7. 检查日志文件大小
echo "📝 检查日志文件..."
find /Volumes/ssd/bidding-data/logs -name "*.log" -size +100M 2>/dev/null | while read logfile; do
    SIZE=$(du -sh "$logfile" | awk '{print $1}')
    echo "  ⚠️  大日志文件: $logfile ($SIZE)"
done || echo "  ✅ 日志文件大小正常"

echo ""

# 8. 总结
echo "===================="
if [ $FAILED -eq 0 ]; then
    echo "✅ 完整性检查通过！系统状态良好"
    exit 0
else
    echo "❌ 发现 $FAILED 个问题，请检查！"
    exit 1
fi
