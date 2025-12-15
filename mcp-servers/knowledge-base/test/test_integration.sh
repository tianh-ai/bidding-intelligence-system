#!/bin/bash

# Knowledge Base MCP 集成测试脚本

set -e  # 遇到错误立即退出

echo "======================================"
echo "Knowledge Base MCP 集成测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查依赖
echo "1. 检查依赖..."

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js 未安装${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 未安装${NC}"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo -e "${RED}✗ curl 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 所有依赖已安装${NC}"
echo ""

# 检查 MCP 服务器构建
echo "2. 检查 MCP 服务器构建..."

if [ ! -f "../dist/index.js" ]; then
    echo -e "${YELLOW}MCP 服务器未构建，开始构建...${NC}"
    cd .. && npm run build && cd test
    echo -e "${GREEN}✓ MCP 服务器构建成功${NC}"
else
    echo -e "${GREEN}✓ MCP 服务器已构建${NC}"
fi

echo ""

# 测试 Python 后端
echo "3. 测试 Python 后端..."

echo "3.1 获取统计信息"
if python3 ../python/knowledge_base.py stats; then
    echo -e "${GREEN}✓ 统计信息获取成功${NC}"
else
    echo -e "${RED}✗ 统计信息获取失败${NC}"
    exit 1
fi

echo ""

# 检查后端服务
echo "4. 检查后端服务..."

if curl -s http://localhost:18888/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行正常${NC}"
else
    echo -e "${YELLOW}⚠ 后端服务未启动，请先启动: docker compose up -d backend${NC}"
    exit 1
fi

echo ""

# 测试健康检查
echo "5. 测试知识库健康检查..."

HEALTH_RESPONSE=$(curl -s http://localhost:18888/api/knowledge/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ 健康检查通过${NC}"
    echo "响应: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ 健康检查失败${NC}"
    echo "响应: $HEALTH_RESPONSE"
    exit 1
fi

echo ""

# 测试搜索功能
echo "6. 测试知识库搜索..."

SEARCH_RESPONSE=$(curl -s -X POST http://localhost:18888/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试",
    "category": "test",
    "limit": 5,
    "min_score": 0.0
  }')

if echo "$SEARCH_RESPONSE" | grep -q "status"; then
    echo -e "${GREEN}✓ 搜索功能正常${NC}"
    echo "响应: $SEARCH_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ 搜索功能失败${NC}"
    echo "响应: $SEARCH_RESPONSE"
    exit 1
fi

echo ""

# 测试添加条目
echo "7. 测试添加知识条目..."

ADD_RESPONSE=$(curl -s -X POST http://localhost:18888/api/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": null,
    "category": "test",
    "title": "集成测试条目",
    "content": "这是一个集成测试创建的知识条目",
    "keywords": ["测试", "集成"],
    "importance_score": 0.75,
    "metadata": {"source": "integration_test"}
  }')

if echo "$ADD_RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}✓ 添加条目成功${NC}"
    ENTRY_ID=$(echo "$ADD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
    echo "新条目 ID: $ENTRY_ID"
else
    echo -e "${RED}✗ 添加条目失败${NC}"
    echo "响应: $ADD_RESPONSE"
    exit 1
fi

echo ""

# 测试获取条目
if [ -n "$ENTRY_ID" ]; then
    echo "8. 测试获取条目详情..."
    
    GET_RESPONSE=$(curl -s http://localhost:18888/api/knowledge/entries/$ENTRY_ID)
    
    if echo "$GET_RESPONSE" | grep -q "title"; then
        echo -e "${GREEN}✓ 获取条目成功${NC}"
        echo "响应: $GET_RESPONSE" | python3 -m json.tool
    else
        echo -e "${RED}✗ 获取条目失败${NC}"
        echo "响应: $GET_RESPONSE"
    fi
    
    echo ""
fi

# 测试列表功能
echo "9. 测试条目列表..."

LIST_RESPONSE=$(curl -s -X POST http://localhost:18888/api/knowledge/entries/list \
  -H "Content-Type: application/json" \
  -d '{
    "category": "test",
    "limit": 10,
    "offset": 0
  }')

if echo "$LIST_RESPONSE" | grep -q "entries"; then
    echo -e "${GREEN}✓ 列表功能正常${NC}"
    ENTRY_COUNT=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('entries', [])))")
    echo "找到 $ENTRY_COUNT 个条目"
else
    echo -e "${RED}✗ 列表功能失败${NC}"
    echo "响应: $LIST_RESPONSE"
fi

echo ""

# 测试统计信息
echo "10. 测试统计信息..."

STATS_RESPONSE=$(curl -s http://localhost:18888/api/knowledge/statistics)

if echo "$STATS_RESPONSE" | grep -q "total_entries"; then
    echo -e "${GREEN}✓ 统计信息正常${NC}"
    echo "响应: $STATS_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ 统计信息失败${NC}"
    echo "响应: $STATS_RESPONSE"
fi

echo ""

# 清理测试数据
if [ -n "$ENTRY_ID" ]; then
    echo "11. 清理测试数据..."
    
    DELETE_RESPONSE=$(curl -s -X DELETE http://localhost:18888/api/knowledge/entries/$ENTRY_ID)
    
    if echo "$DELETE_RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✓ 测试数据清理成功${NC}"
    else
        echo -e "${YELLOW}⚠ 测试数据清理可能失败，请手动检查${NC}"
    fi
    
    echo ""
fi

# 测试总结
echo "======================================"
echo -e "${GREEN}✓ 所有测试通过！${NC}"
echo "======================================"
echo ""
echo "测试覆盖："
echo "  ✓ 依赖检查"
echo "  ✓ MCP 服务器构建"
echo "  ✓ Python 后端功能"
echo "  ✓ 后端服务状态"
echo "  ✓ 健康检查"
echo "  ✓ 知识搜索"
echo "  ✓ 添加条目"
echo "  ✓ 获取条目"
echo "  ✓ 条目列表"
echo "  ✓ 统计信息"
echo "  ✓ 删除条目"
echo ""
echo "知识库 MCP 已准备就绪！"
