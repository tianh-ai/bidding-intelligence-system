#!/bin/bash
# 快速验证脚本 - 演示Skills vs Legacy对比

set -e

echo "=========================================="
echo "🚀 Skills生产验证 - 快速演示"
echo "=========================================="

# 检查uploads目录
if [ ! -d "../uploads" ]; then
    echo "❌ uploads目录不存在，创建示例文件..."
    mkdir -p ../uploads
fi

# 查找测试文件
PDF_FILE=$(find ../uploads -name "*.pdf" -type f | head -1)
DOCX_FILE=$(find ../uploads -name "*.docx" -type f | head -1)

if [ -z "$PDF_FILE" ] && [ -z "$DOCX_FILE" ]; then
    echo "⚠️  未找到测试文件，请手动指定："
    echo ""
    echo "用法："
    echo "  python3 validate_skills_production.py --file path/to/file.pdf"
    echo ""
    echo "或批量测试："
    echo "  python3 validate_skills_production.py --batch uploads/"
    exit 1
fi

# 测试找到的文件
if [ -n "$PDF_FILE" ]; then
    echo ""
    echo "📄 测试PDF文件: $PDF_FILE"
    echo ""
    python3 validate_skills_production.py --file "$PDF_FILE"
fi

if [ -n "$DOCX_FILE" ]; then
    echo ""
    echo "📄 测试DOCX文件: $DOCX_FILE"
    echo ""
    python3 validate_skills_production.py --file "$DOCX_FILE"
fi

echo ""
echo "✅ 验证完成！查看validation_results/目录获取详细报告"
