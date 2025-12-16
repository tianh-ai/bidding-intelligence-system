#!/bin/bash
# Docker环境完整验证脚本

set -e

echo "=========================================="
echo "🐳 Docker环境Skills完整验证"
echo "=========================================="

# 1. 确保Docker容器运行
echo ""
echo "步骤 1: 检查Docker容器..."
docker compose ps backend | grep -q "Up" || {
    echo "❌ backend容器未运行，请先启动: docker compose up -d"
    exit 1
}

# 2. 准备测试文件
echo ""
echo "步骤 2: 查找测试文件（在Docker容器中）..."
TEST_PDF=$(docker compose exec -T backend sh -c "find /app/uploads -name '*.pdf' -type f 2>/dev/null | head -1")
TEST_DOCX=$(docker compose exec -T backend sh -c "find /app/uploads -name '*.docx' -type f 2>/dev/null | head -1")

if [ -z "$TEST_PDF" ]; then
    echo "⚠️  未找到PDF测试文件"
    echo "   提示: 请确保uploads目录有测试文件"
else
    echo "✅ 找到PDF: $(basename "$TEST_PDF")"
fi

if [ -z "$TEST_DOCX" ]; then
    echo "⚠️  未找到DOCX测试文件"
else
    echo "✅ 找到DOCX: $(basename "$TEST_DOCX")"
fi

# 3. 在Docker中运行验证
echo ""
echo "步骤 3: 在Docker容器中运行验证..."
echo ""

if [ -n "$TEST_PDF" ]; then
    echo "📄 测试PDF: $(basename "$TEST_PDF")"
    docker compose exec -T backend python3 validate_skills_production.py \
        --file "$TEST_PDF" \
        --output /app/validation_results
    echo ""
fi

if [ -n "$TEST_DOCX" ]; then
    echo "📄 测试DOCX: $(basename "$TEST_DOCX")"
    docker compose exec -T backend python3 validate_skills_production.py \
        --file "$TEST_DOCX" \
        --output /app/validation_results
    echo ""
fi

# 4. 批量测试
echo ""
echo "步骤 4: 批量测试uploads目录..."
docker compose exec -T backend python3 validate_skills_production.py \
    --batch /app/uploads \
    --pattern "*.pdf" \
    --output /app/validation_results

echo ""
echo "=========================================="
echo "✅ 验证完成！"
echo "=========================================="
echo ""
echo "查看详细报告:"
echo "  ls -lh backend/validation_results/"
echo ""
