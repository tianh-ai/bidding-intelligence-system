#!/bin/bash

# Knowledge Base MCP 快速验证脚本

set -e

echo "======================================"
echo "Knowledge Base MCP 快速验证"
echo "======================================"
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 检查构建
echo "1. 检查 MCP 服务器构建状态..."
if [ -f "dist/index.js" ]; then
    echo -e "${GREEN}✓ MCP 服务器已构建${NC}"
else
    echo -e "${YELLOW}⚠ MCP 服务器未构建，开始构建...${NC}"
    npm install
    npm run build
    echo -e "${GREEN}✓ MCP 服务器构建完成${NC}"
fi
echo ""

# 2. 测试 Python 后端
echo "2. 测试 Python 后端..."
if python3 python/knowledge_base.py stats > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Python 后端正常${NC}"
    python3 python/knowledge_base.py stats
else
    echo -e "${RED}✗ Python 后端测试失败${NC}"
    echo "可能原因: 数据库未配置或主程序依赖缺失"
    exit 1
fi
echo ""

# 3. 检查后端服务
echo "3. 检查主程序后端服务..."
if curl -s http://localhost:18888/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行中${NC}"
    
    # 4. 测试知识库 API
    echo ""
    echo "4. 测试知识库 API..."
    
    # 健康检查
    echo "4.1 健康检查"
    HEALTH=$(curl -s http://localhost:18888/api/knowledge/health)
    if echo "$HEALTH" | grep -q "healthy"; then
        echo -e "${GREEN}✓ 健康检查通过${NC}"
    else
        echo -e "${RED}✗ 健康检查失败${NC}"
        echo "$HEALTH"
        exit 1
    fi
    
    # 统计信息
    echo "4.2 统计信息"
    STATS=$(curl -s http://localhost:18888/api/knowledge/statistics)
    if echo "$STATS" | grep -q "total_entries"; then
        echo -e "${GREEN}✓ 统计 API 正常${NC}"
        echo "$STATS" | python3 -m json.tool
    else
        echo -e "${RED}✗ 统计 API 失败${NC}"
        exit 1
    fi
    
    # 搜索测试
    echo "4.3 搜索功能"
    SEARCH=$(curl -s -X POST http://localhost:18888/api/knowledge/search \
      -H "Content-Type: application/json" \
      -d '{"query": "测试", "limit": 5}')
    if echo "$SEARCH" | grep -q "status"; then
        echo -e "${GREEN}✓ 搜索 API 正常${NC}"
        RESULT_COUNT=$(echo "$SEARCH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))")
        echo "搜索结果数: $RESULT_COUNT"
    else
        echo -e "${RED}✗ 搜索 API 失败${NC}"
        exit 1
    fi
    
    echo ""
    echo "======================================"
    echo -e "${GREEN}✓ 所有验证通过！${NC}"
    echo "======================================"
    echo ""
    echo "Knowledge Base MCP 已准备就绪："
    echo "  ✓ MCP 服务器已构建"
    echo "  ✓ Python 后端正常"
    echo "  ✓ 后端服务运行中"
    echo "  ✓ 健康检查通过"
    echo "  ✓ 统计 API 正常"
    echo "  ✓ 搜索 API 正常"
    echo ""
    echo "API 端点："
    echo "  - POST   /api/knowledge/search"
    echo "  - POST   /api/knowledge/entries"
    echo "  - GET    /api/knowledge/entries/{id}"
    echo "  - POST   /api/knowledge/entries/list"
    echo "  - DELETE /api/knowledge/entries/{id}"
    echo "  - GET    /api/knowledge/statistics"
    echo "  - GET    /api/knowledge/health"
    
else
    echo -e "${YELLOW}⚠ 后端服务未启动${NC}"
    echo ""
    echo "请先通过 Docker 启动后端服务："
    echo "  cd ../.."
    echo "  docker compose up -d backend"
    echo ""
    echo "然后重新运行本脚本"
    exit 1
fi
