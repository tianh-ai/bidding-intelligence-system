#!/bin/bash

# 深度验证测试脚本
# 测试四大问题的修复情况

set -e

echo "========================================="
echo "深度验证测试 - 四大问题修复"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试结果统计
PASS=0
FAIL=0
TOTAL=0

# 测试函数
test_api() {
    TOTAL=$((TOTAL + 1))
    echo -n "测试 $1 ... "
    
    if eval "$2" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 通过${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗ 失败${NC}"
        FAIL=$((FAIL + 1))
        echo "  命令: $2"
    fi
}

# ========== 1. 后端API测试 ==========
echo -e "${BLUE}[1/4] 后端API测试${NC}"
echo "-----------------------------------"

# 检查后端服务
test_api "后端服务运行" "lsof -i :8000 | grep LISTEN"

# Auth API测试
test_api "登录API - Admin" "curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}' | grep -q '\"role\":\"admin\"'"

test_api "登录API - 普通用户" "curl -s -X POST http://localhost:8000/api/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"test\",\"password\":\"test123\"}' | grep -q '\"role\":\"user\"'"

# Prompts API测试
test_api "提示词列表API" "curl -s http://localhost:8000/api/prompts/templates | grep -q '\['"

echo ""

# ========== 2. 前端服务测试 ==========
echo -e "${BLUE}[2/4] 前端服务测试${NC}"
echo "-----------------------------------"

test_api "前端服务运行" "lsof -i :5173 | grep LISTEN"

test_api "前端首页加载" "curl -s http://localhost:5173 | grep -q '投标智能系统'"

test_api "前端资源加载" "curl -s http://localhost:5173/src/main.tsx | grep -q 'import'"

echo ""

# ========== 3. 代码检查 ==========
echo -e "${BLUE}[3/4] 代码静态检查${NC}"
echo "-----------------------------------"

# 检查关键文件是否存在
test_api "MainLayout.tsx 存在" "test -f frontend/src/layouts/MainLayout.tsx"

test_api "AIChatPanel.tsx 存在" "test -f frontend/src/components/AIChatPanel.tsx"

test_api "PromptManagement.tsx 存在" "test -f frontend/src/pages/PromptManagement.tsx"

# 检查关键代码
test_api "三栏布局代码" "grep -q 'sizes={' frontend/src/layouts/MainLayout.tsx"

test_api "输入框高度代码" "grep -q 'minRows: 3' frontend/src/components/AIChatPanel.tsx"

test_api "提示词管理路由" "grep -q 'prompts' frontend/src/App.tsx"

test_api "侧边栏菜单项" "grep -q 'ThunderboltOutlined' frontend/src/components/AppSidebar.tsx"

echo ""

# ========== 4. 功能验证 ==========
echo -e "${BLUE}[4/4] 功能验证测试${NC}"
echo "-----------------------------------"

# 获取admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' | \
    grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -n "$ADMIN_TOKEN" ]; then
    echo -e "${GREEN}✓ Admin Token 获取成功${NC}"
    PASS=$((PASS + 1))
    
    # 测试提示词CRUD
    test_api "创建提示词" "curl -s -X POST http://localhost:8000/api/prompts/templates \
        -H 'Content-Type: application/json' \
        -H 'Authorization: Bearer $ADMIN_TOKEN' \
        -d '{\"title\":\"测试提示词\",\"category\":\"其他\",\"content\":\"测试内容\"}' | grep -q 'id'"
    
    # 获取提示词列表
    PROMPT_LIST=$(curl -s http://localhost:8000/api/prompts/templates)
    PROMPT_COUNT=$(echo "$PROMPT_LIST" | grep -o '"id"' | wc -l)
    
    if [ "$PROMPT_COUNT" -ge 1 ]; then
        echo -e "${GREEN}✓ 提示词列表查询成功 (共 $PROMPT_COUNT 条)${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗ 提示词列表查询失败${NC}"
        FAIL=$((FAIL + 1))
    fi
else
    echo -e "${RED}✗ Admin Token 获取失败${NC}"
    FAIL=$((FAIL + 2))
fi

TOTAL=$((TOTAL + 2))

echo ""

# ========== 测试总结 ==========
echo "========================================="
echo -e "${BLUE}测试总结${NC}"
echo "========================================="
echo "总计: $TOTAL 项测试"
echo -e "通过: ${GREEN}$PASS${NC} 项"
echo -e "失败: ${RED}$FAIL${NC} 项"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！${NC}"
    echo ""
    echo "========================================="
    echo "浏览器验证指南"
    echo "========================================="
    echo "1. 打开浏览器访问: http://localhost:5173"
    echo "2. 使用 admin / admin123 登录"
    echo "3. 验证Header显示 '管理员' 标签"
    echo "4. 拖动侧边栏、主内容区、AI助手的分隔线"
    echo "5. 打开AI助手，测试输入框高度（默认3行）"
    echo "6. 点击侧边栏'提示词管理'，测试CRUD功能"
    echo ""
    echo -e "${YELLOW}提示：如果Admin仍显示'访客'，请清除浏览器LocalStorage后重新登录${NC}"
    exit 0
else
    echo -e "${RED}✗ 有 $FAIL 项测试失败，请检查日志${NC}"
    exit 1
fi
