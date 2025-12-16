#!/bin/bash
# Skills使用情况监控脚本
# 用于观察Skills vs Legacy的使用情况

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   📊 Skills使用情况监控"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 检查MCP使用ImageProcessor Skill的次数
echo "=== 1. MCP图片提取方法统计 ==="
echo ""
echo "ImageProcessor Skill调用次数:"
docker compose logs backend 2>/dev/null | grep -c "extraction_method.*ImageProcessor Skill" || echo "0"

echo ""
echo "Legacy ImageExtractor调用次数:"
docker compose logs backend 2>/dev/null | grep -c "extraction_method.*Legacy ImageExtractor" || echo "0"

echo ""
echo "Fallback警告次数:"
docker compose logs backend 2>/dev/null | grep -c "Warning.*Skill failed.*using legacy" || echo "0"

# 2. 检查TableExtractor使用情况
echo ""
echo "=== 2. TableExtractor使用统计 ==="
echo ""
echo "TableExtractor初始化次数:"
docker compose logs backend 2>/dev/null | grep -c "TableExtractor initialized" || echo "0"

echo ""
echo "TableExtractor执行次数:"
docker compose logs backend 2>/dev/null | grep -c "TableExtractor execution completed" || echo "0"

# 3. 检查ImageProcessor使用情况
echo ""
echo "=== 3. ImageProcessor使用统计 ==="
echo ""
echo "ImageProcessor初始化次数:"
docker compose logs backend 2>/dev/null | grep -c "ImageProcessor initialized" || echo "0"

echo ""
echo "ImageProcessor执行次数:"
docker compose logs backend 2>/dev/null | grep -c "ImageProcessor execution completed" || echo "0"

# 4. 最近的Skills调用日志
echo ""
echo "=== 4. 最近的Skills调用（最后10条） ==="
echo ""
docker compose logs --tail=200 backend 2>/dev/null | \
  grep -E "ImageProcessor|TableExtractor|extraction_method|Skill failed" | \
  tail -10 || echo "无相关日志"

# 5. 系统健康检查
echo ""
echo "=== 5. 系统健康状态 ==="
echo ""
curl -s http://localhost:18888/health | python3 -m json.tool 2>/dev/null || echo "❌ 健康检查失败"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   ✅ 监控完成 ($(date '+%Y-%m-%d %H:%M:%S'))"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 提示:"
echo "   - 如果Fallback警告次数 > 0，需要检查日志"
echo "   - 建议定期运行此脚本监控Skills使用情况"
echo "   - 观察一周后，可考虑完全切换到Skills"
echo ""
