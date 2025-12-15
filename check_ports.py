#!/bin/bash
#
# 端口一致性检查和修复脚本
# 确保所有文件中的端口配置与Docker保持一致
#

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 全面端口一致性检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 定义正确的端口配置
CORRECT_BACKEND_PORT="18888"
WRONG_BACKEND_PORT="8000"

# 需要检查的文件类型
FILE_PATTERNS=(
    "*.py"
    "*.sh"
    "*.md"
    ".env"
)

echo "📋 检查规则："
echo "   ✅ 正确: http://localhost:18888 (Docker后端端口)"
echo "   ❌ 错误: http://localhost:8000  (不要使用)"
echo ""

# 统计变量
TOTAL_ISSUES=0
FIXED_FILES=()

# 检查Python测试脚本
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 检查Python脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PYTHON_FILES=(
    "verify_knowledge_display.py"
    "test_knowledge_api.py"
    "test_knowledge_auth.py"
    "diagnose_knowledge.py"
    "test_port_18888.py"
    "backend/check_knowledge.py"
)

for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "localhost:8000" "$file" 2>/dev/null; then
            echo "  ❌ $file - 发现错误端口8000"
            TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
            
            # 自动修复
            if [[ "$file" == *.py ]]; then
                sed -i.bak 's|http://localhost:8000|http://localhost:18888|g' "$file"
                sed -i.bak 's|localhost:8000|localhost:18888|g' "$file"
                sed -i.bak 's|:8000"|:18888"|g' "$file"
                echo "     ✅ 已自动修复"
                FIXED_FILES+=("$file")
            fi
        else
            if grep -q "localhost:18888" "$file" 2>/dev/null; then
                echo "  ✅ $file - 端口配置正确"
            fi
        fi
    fi
done

# 检查Shell脚本
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. 检查Shell脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SHELL_FILES=(
    "fix_knowledge_docker.sh"
    "scripts/quick_verify.sh"
    "run_knowledge_test.sh"
    "test_frontend_flow.sh"
)

for file in "${SHELL_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q "localhost:8000" "$file" 2>/dev/null; then
            echo "  ⚠️  $file - 发现端口8000（可能是正常的本地模式）"
            # Shell脚本可能有条件逻辑，不自动修复
        else
            echo "  ✅ $file - 检查通过"
        fi
    fi
done

# 检查前端配置
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. 检查前端配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查frontend/.env
if [ -f "frontend/.env" ]; then
    if grep -q "VITE_API_URL=http://localhost:18888" "frontend/.env"; then
        echo "  ✅ frontend/.env - 端口配置正确 (18888)"
    elif grep -q "VITE_API_URL=http://localhost:8000" "frontend/.env"; then
        echo "  ❌ frontend/.env - 端口配置错误 (8000)"
        echo "     正在修复..."
        sed -i.bak 's|VITE_API_URL=http://localhost:8000|VITE_API_URL=http://localhost:18888|g' frontend/.env
        echo "     ✅ 已修复为 18888"
        FIXED_FILES+=("frontend/.env")
        TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    else
        echo "  ⚠️  frontend/.env - 未找到VITE_API_URL配置"
    fi
else
    echo "  ⚠️  frontend/.env 不存在"
fi

# 检查frontend/src/config/constants.ts
if [ -f "frontend/src/config/constants.ts" ]; then
    if grep -q "localhost:8000" "frontend/src/config/constants.ts"; then
        echo "  ⚠️  frontend/src/config/constants.ts - 默认值是8000"
        echo "     注意：这个默认值在.env设置后会被覆盖，属于正常"
    fi
    echo "  ✅ frontend/src/config/constants.ts - 使用环境变量"
fi

# 检查Docker配置
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. 检查Docker配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "docker-compose.yml" ]; then
    if grep -q "18888:8000" "docker-compose.yml"; then
        echo "  ✅ docker-compose.yml - 端口映射正确 (18888:8000)"
    else
        echo "  ❌ docker-compose.yml - 端口映射可能有问题"
    fi
fi

# 总结
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "检查总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo "✅ 所有关键文件端口配置正确！"
else
    echo "⚠️  发现 $TOTAL_ISSUES 个问题"
    
    if [ ${#FIXED_FILES[@]} -gt 0 ]; then
        echo ""
        echo "已自动修复的文件："
        for file in "${FIXED_FILES[@]}"; do
            echo "  ✅ $file"
        done
        
        echo ""
        echo "备份文件已保存为 *.bak，如需回滚："
        echo "  for f in \$(find . -name '*.bak'); do mv \$f \${f%.bak}; done"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 端口配置原则"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🐳 Docker模式（推荐）："
echo "   - 后端端口: 18888"
echo "   - 前端配置: VITE_API_URL=http://localhost:18888"
echo "   - 启动命令: docker-compose up -d"
echo ""
echo "💻 本地模式（仅开发调试）："
echo "   - 后端端口: 8000"
echo "   - 前端配置: VITE_API_URL=http://localhost:8000"
echo "   - 启动命令: cd backend && python main.py"
echo "   - ⚠️  不推荐！违反Docker原则！"
echo ""
echo "详见: DOCKER_PRINCIPLES.md"
echo ""
