#!/bin/bash

# 端口一致性检查脚本
# 用途：确保所有文件都使用正确的Docker端口18888，而不是8000

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 分隔线
LINE="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${BOLD}${BLUE}${LINE}${NC}"
echo -e "${BOLD}🔍 全面端口一致性检查${NC}"
echo -e "${BLUE}${LINE}${NC}\n"

# 检查计数
total_files=0
fixed_files=0
error_files=0

# 排除的目录
EXCLUDE_DIRS=".git|node_modules|__pycache__|.venv|venv|dist|build|uploads"

# 需要检查的文件类型
echo -e "${BOLD}1. 检查Python脚本${NC}"
echo -e "${BLUE}${LINE}${NC}"

# 检查Python文件
python_files=$(find . -type f -name "*.py" | grep -vE "$EXCLUDE_DIRS" || true)

for file in $python_files; do
    # 跳过某些特殊文件
    if [[ "$file" == *"check_ports.py"* ]]; then
        continue
    fi
    
    # 检查是否包含8000端口
    if grep -q "localhost:8000\|:8000" "$file" 2>/dev/null; then
        total_files=$((total_files + 1))
        
        # 尝试自动修复
        if sed -i.bak 's|localhost:8000|localhost:18888|g' "$file" 2>/dev/null; then
            # 检查是否真的修改了
            if diff "$file" "$file.bak" >/dev/null 2>&1; then
                echo -e "  ${YELLOW}⚠️  ${file} - 没有需要修复的内容${NC}"
            else
                echo -e "  ${GREEN}✅ ${file} - 已自动修复${NC}"
                fixed_files=$((fixed_files + 1))
            fi
            rm -f "$file.bak"
        else
            echo -e "  ${RED}❌ ${file} - 自动修复失败，需要手动检查${NC}"
            error_files=$((error_files + 1))
        fi
    fi
done

echo -e "\n${BOLD}2. 检查Shell脚本${NC}"
echo -e "${BLUE}${LINE}${NC}"

# 检查Shell文件
shell_files=$(find . -type f \( -name "*.sh" -o -name "*.bash" \) | grep -vE "$EXCLUDE_DIRS|check_ports.sh" || true)

for file in $shell_files; do
    if grep -q "localhost:8000\|:8000" "$file" 2>/dev/null; then
        total_files=$((total_files + 1))
        
        # 检查是否在docker-compose命令中（这些是容器内部端口，不需要改）
        if grep -q "docker-compose\|dockerfile" "$file" 2>/dev/null; then
            echo -e "  ${YELLOW}⚠️  ${file} - 包含Docker配置，需要手动检查${NC}"
            continue
        fi
        
        # 尝试自动修复
        if sed -i.bak 's|localhost:8000|localhost:18888|g' "$file" 2>/dev/null; then
            if diff "$file" "$file.bak" >/dev/null 2>&1; then
                echo -e "  ${YELLOW}⚠️  ${file} - 没有需要修复的内容${NC}"
            else
                echo -e "  ${GREEN}✅ ${file} - 已自动修复${NC}"
                fixed_files=$((fixed_files + 1))
            fi
            rm -f "$file.bak"
        else
            echo -e "  ${RED}❌ ${file} - 自动修复失败，需要手动检查${NC}"
            error_files=$((error_files + 1))
        fi
    fi
done

echo -e "\n${BOLD}3. 检查前端配置${NC}"
echo -e "${BLUE}${LINE}${NC}"

# 检查前端.env文件
if [ -f "frontend/.env" ]; then
    if grep -q "VITE_API_URL.*18888" "frontend/.env"; then
        echo -e "  ${GREEN}✅ frontend/.env - 端口配置正确 (18888)${NC}"
    elif grep -q "VITE_API_URL.*8000" "frontend/.env"; then
        total_files=$((total_files + 1))
        echo -e "  ${YELLOW}⚠️  frontend/.env - 端口错误 (8000)，正在修复...${NC}"
        
        sed -i.bak 's|:8000|:18888|g' "frontend/.env"
        
        if grep -q "VITE_API_URL.*18888" "frontend/.env"; then
            echo -e "  ${GREEN}✅ frontend/.env - 已自动修复为18888${NC}"
            fixed_files=$((fixed_files + 1))
            rm -f "frontend/.env.bak"
        else
            echo -e "  ${RED}❌ frontend/.env - 修复失败，请手动检查${NC}"
            error_files=$((error_files + 1))
        fi
    else
        echo -e "  ${YELLOW}⚠️  frontend/.env - 未找到VITE_API_URL配置${NC}"
    fi
else
    echo -e "  ${RED}❌ frontend/.env - 文件不存在${NC}"
    error_files=$((error_files + 1))
fi

# 检查TypeScript配置
if [ -f "frontend/src/services/api.ts" ]; then
    if grep -q "localhost:8000" "frontend/src/services/api.ts"; then
        total_files=$((total_files + 1))
        echo -e "  ${YELLOW}⚠️  frontend/src/services/api.ts - 包含8000端口引用（可能是默认值）${NC}"
        echo -e "     ${BLUE}ℹ️  前端应该从.env读取配置，不需要修改${NC}"
    else
        echo -e "  ${GREEN}✅ frontend/src/services/api.ts - 未发现硬编码端口${NC}"
    fi
fi

echo -e "\n${BOLD}4. 检查Markdown文档${NC}"
echo -e "${BLUE}${LINE}${NC}"

# 检查Markdown文件中的示例代码
md_files=$(find . -type f -name "*.md" | grep -vE "$EXCLUDE_DIRS|PORT_CONSISTENCY.md" || true)
md_count=0

for file in $md_files; do
    if grep -q "localhost:8000\|:8000" "$file" 2>/dev/null; then
        md_count=$((md_count + 1))
        # 文档文件不自动修复，只报告
        echo -e "  ${YELLOW}⚠️  ${file} - 包含8000端口引用（文档需要手动审查）${NC}"
    fi
done

if [ $md_count -eq 0 ]; then
    echo -e "  ${GREEN}✅ 所有Markdown文档端口配置正确${NC}"
fi

# 总结
echo -e "\n${BOLD}${BLUE}${LINE}${NC}"
echo -e "${BOLD}📊 检查总结${NC}"
echo -e "${BLUE}${LINE}${NC}\n"

echo -e "  总共检查: ${BOLD}${total_files}${NC} 个文件有端口问题"
echo -e "  已修复:   ${GREEN}${BOLD}${fixed_files}${NC} 个文件"
echo -e "  需手动:   ${RED}${BOLD}${error_files}${NC} 个文件"

if [ $md_count -gt 0 ]; then
    echo -e "  文档:     ${YELLOW}${BOLD}${md_count}${NC} 个文档需要审查"
fi

echo ""

# 运行验证检查
echo -e "${BOLD}5. 验证关键文件${NC}"
echo -e "${BLUE}${LINE}${NC}"

# 关键文件列表
declare -a critical_files=(
    "verify_knowledge_display.py"
    "test_knowledge_api.py"
    "test_knowledge_auth.py"
    "diagnose_knowledge.py"
    "frontend/.env"
)

all_ok=true

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "localhost:8000" "$file" 2>/dev/null; then
            echo -e "  ${RED}❌ ${file} - 仍然包含8000端口！${NC}"
            all_ok=false
        else
            echo -e "  ${GREEN}✅ ${file} - 端口配置正确${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  ${file} - 文件不存在${NC}"
    fi
done

echo ""

# 最终状态
echo -e "${BOLD}${BLUE}${LINE}${NC}"

if [ "$all_ok" = true ] && [ $error_files -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ 所有关键文件端口配置正确！${NC}\n"
    
    # 提供快速测试命令
    echo -e "${BOLD}💡 建议测试${NC}"
    echo -e "${BLUE}${LINE}${NC}"
    echo -e "  1. 检查Docker服务:"
    echo -e "     ${YELLOW}docker-compose ps${NC}"
    echo -e ""
    echo -e "  2. 测试后端健康检查:"
    echo -e "     ${YELLOW}curl http://localhost:18888/health${NC}"
    echo -e ""
    echo -e "  3. 运行知识库验证:"
    echo -e "     ${YELLOW}python verify_knowledge_display.py${NC}"
    echo ""
    
    exit 0
else
    echo -e "${RED}${BOLD}⚠️  发现端口配置问题！${NC}\n"
    
    echo -e "${BOLD}🔧 修复建议${NC}"
    echo -e "${BLUE}${LINE}${NC}"
    
    if [ $error_files -gt 0 ]; then
        echo -e "  1. 手动检查以下类型的文件:"
        echo -e "     - Docker配置文件 (docker-compose.yml)"
        echo -e "     - 包含复杂逻辑的脚本"
        echo -e ""
    fi
    
    if [ $md_count -gt 0 ]; then
        echo -e "  2. 审查文档中的示例代码:"
        echo -e "     - 区分Docker模式(18888)和本地模式(8000)"
        echo -e "     - 确保推荐的是Docker模式"
        echo -e ""
    fi
    
    echo -e "  3. 详细指南:"
    echo -e "     ${YELLOW}cat PORT_CONSISTENCY.md${NC}"
    echo ""
    
    exit 1
fi
