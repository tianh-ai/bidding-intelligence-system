#!/bin/bash

# 🚀 快速启动验证脚本
# 用于快速验证文档处理系统的就绪状态

set -e  # 任何错误都停止

echo "=================================="
echo "🚀 文档处理系统快速验证"
echo "=================================="

# 设置颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_file() {
    local file=$1
    local desc=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $desc: $file"
        return 0
    else
        echo -e "${RED}❌${NC} $desc: $file (缺失)"
        return 1
    fi
}

check_dir() {
    local dir=$1
    local desc=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅${NC} $desc: $dir"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC}  $desc: $dir (不存在，需要创建)"
        mkdir -p "$dir"
        echo -e "${GREEN}✅${NC} 已创建: $dir"
        return 0
    fi
}

# 进入后端目录
cd "$(dirname "$0")/backend" || exit 1

echo ""
echo "📋 检查代码模块..."
check_file "engines/smart_document_classifier.py" "文件分类器"
check_file "engines/ocr_extractor.py" "OCR 提取器"
check_file "engines/document_processor.py" "文档处理器"

echo ""
echo "📋 检查数据库脚本..."
check_file "database/document_processing_schema.sql" "数据库 Schema"

echo ""
echo "📋 检查文档..."
check_file "FILE_PROCESSING_STRATEGY.md" "处理策略文档"
check_file "IMPLEMENTATION_SUMMARY.md" "实现总结"
check_file "INTEGRATION_GUIDE.md" "集成指南"
check_file "test_document_processing.py" "测试脚本"
check_file "check_system_readiness.py" "系统检查脚本"

echo ""
echo "📋 检查目录结构..."
check_dir "uploads" "上传目录"
check_dir "documents" "文档目录"
check_dir "logs" "日志目录"
check_dir "documents/financial_reports" "财务报告目录"
check_dir "documents/licenses" "证件目录"

echo ""
echo "📋 检查依赖..."
grep -q "paddlepaddle" requirements.txt && \
    echo -e "${GREEN}✅${NC} paddlepaddle 已在 requirements.txt" || \
    echo -e "${RED}❌${NC} paddlepaddle 未找到"

grep -q "paddleocr" requirements.txt && \
    echo -e "${GREEN}✅${NC} paddleocr 已在 requirements.txt" || \
    echo -e "${RED}❌${NC} paddleocr 未找到"

grep -q "pillow" requirements.txt && \
    echo -e "${GREEN}✅${NC} pillow 已在 requirements.txt" || \
    echo -e "${RED}❌${NC} pillow 未找到"

echo ""
echo "🔍 尝试导入模块..."

python3 << 'EOF'
import sys
sys.path.insert(0, '.')

try:
    from engines.smart_document_classifier import SmartDocumentClassifier
    print("✅ SmartDocumentClassifier 导入成功")
except Exception as e:
    print(f"❌ SmartDocumentClassifier 导入失败: {e}")
    sys.exit(1)

try:
    from engines.ocr_extractor import HybridTextExtractor
    print("✅ HybridTextExtractor 导入成功")
except Exception as e:
    print(f"❌ HybridTextExtractor 导入失败: {e}")
    sys.exit(1)

try:
    from engines.document_processor import DocumentProcessor
    print("✅ DocumentProcessor 导入成功")
except Exception as e:
    print(f"❌ DocumentProcessor 导入失败: {e}")
    sys.exit(1)

print("")
print("✅ 所有模块导入成功！")
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo -e "${GREEN}✅ 系统检查完成！${NC}"
    echo "=================================="
    echo ""
    echo "📚 后续步骤:"
    echo "1. 运行完整检查: python3 check_system_readiness.py"
    echo "2. 运行自动化测试: python3 test_document_processing.py"
    echo "3. 查看集成指南: 阅读 INTEGRATION_GUIDE.md"
    echo ""
    echo "🎉 系统已就绪！可以进行集成工作了。"
    echo ""
else
    echo ""
    echo "=================================="
    echo -e "${RED}❌ 系统检查失败！${NC}"
    echo "=================================="
    echo ""
    echo "请检查以上错误并修复。"
    echo ""
    exit 1
fi
