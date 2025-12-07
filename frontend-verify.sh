#!/bin/bash

# 前端功能验证脚本
# 生成时间: 2025-12-07

echo "========================================="
echo "前端功能验证检查"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    local name=$1
    local url=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name 运行正常"
        return 0
    else
        echo -e "${RED}✗${NC} $name 未运行"
        return 1
    fi
}

# 1. 检查后端服务
echo "1. 检查后端服务..."
check_service "后端API" "http://localhost:8000/health"
echo ""

# 2. 检查前端服务
echo "2. 检查前端服务..."
check_service "前端服务" "http://localhost:5173"
echo ""

# 3. 检查LLM API
echo "3. 检查LLM模型API..."
response=$(curl -s http://localhost:8000/api/llm/models)
if echo "$response" | grep -q "models"; then
    model_count=$(echo "$response" | grep -o "\"id\"" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓${NC} LLM API正常 (返回 $model_count 个模型)"
    echo "  响应: $(echo "$response" | head -c 150)..."
else
    echo -e "${RED}✗${NC} LLM API异常"
    echo "  响应: $response"
fi
echo ""

# 4. 检查提示词API
echo "4. 检查提示词API..."
response=$(curl -s http://localhost:8000/api/prompts/templates)
if echo "$response" | grep -q "templates"; then
    template_count=$(echo "$response" | grep -o "\"id\"" | wc -l | tr -d ' ')
    echo -e "${GREEN}✓${NC} 提示词API正常 (返回 $template_count 个模板)"
else
    echo -e "${RED}✗${NC} 提示词API异常"
fi
echo ""

# 5. 浏览器测试指南
echo "========================================="
echo "浏览器验证步骤"
echo "========================================="
echo ""
echo "1. 打开浏览器访问: ${YELLOW}http://localhost:5173${NC}"
echo ""
echo "2. 使用以下凭据登录:"
echo "   用户名: ${YELLOW}admin${NC}"
echo "   密码: ${YELLOW}admin123${NC}"
echo ""
echo "3. 按 ${YELLOW}F12${NC} 打开开发者工具"
echo ""
echo "4. 检查 Console 标签，应该看到:"
echo "   ${GREEN}[AIChatPanel] 开始获取模型列表...${NC}"
echo "   ${GREEN}[AIChatPanel] 解析后的模型列表: [...]${NC}"
echo "   ${GREEN}[AIChatPanel] 设置默认模型: {...}${NC}"
echo ""
echo "5. 检查 Network 标签："
echo "   找到 ${YELLOW}/api/llm/models${NC} 请求"
echo "   状态码应为 ${GREEN}200${NC}"
echo "   响应应包含 2 个模型"
echo ""
echo "6. 检查右侧AI助手面板："
echo "   - 应该看到模型选择下拉框"
echo "   - 下拉框旁边显示 ${YELLOW}(2 个模型)${NC}"
echo "   - 点击下拉框应显示两个选项："
echo "     • DeepSeek Chat"
echo "     • 通义千问 Plus"
echo ""
echo "========================================="
echo "验证清单"
echo "========================================="
echo ""
echo "□ 后端服务正常"
echo "□ 前端服务正常"
echo "□ LLM API返回2个模型"
echo "□ 提示词API返回4个模板"
echo "□ 登录成功，显示admin角色"
echo "□ Console无错误信息"
echo "□ 模型选择下拉框可见"
echo "□ 可以切换模型"
echo "□ 文件上传功能正常"
echo ""
echo "========================================="
echo "如果仍有问题，请查看:"
echo "  - FRONTEND_FIXES.md (详细修复方案)"
echo "  - CURRENT_STATUS_AND_VALIDATION.md (状态报告)"
echo "========================================="
