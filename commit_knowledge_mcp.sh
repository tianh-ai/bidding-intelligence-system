#!/bin/bash

# Knowledge Base MCP Git 提交脚本

set -e

echo "======================================"
echo "Knowledge Base MCP Git 提交"
echo "======================================"
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 检查状态
echo "1. 检查 Git 状态..."
git status --short

echo ""
read -p "是否继续提交？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 2. 添加文件
echo ""
echo "2. 添加文件到暂存区..."
git add \
  mcp-servers/knowledge-base/ \
  backend/core/mcp_client.py \
  backend/routers/knowledge.py \
  backend/main.py \
  mcp-servers/README.md \
  KNOWLEDGE_BASE_MCP_COMPLETE.md \
  commit_knowledge_mcp.sh

echo -e "${GREEN}✓ 文件已添加${NC}"

# 3. 显示变更
echo ""
echo "3. 变更摘要："
git diff --cached --stat

# 4. 提交
echo ""
echo "4. 提交代码..."
git commit -m "feat: 实现知识库 MCP 服务器（主程序可调用）

核心特性：
- ✅ 创建 MCP 服务器（TypeScript + MCP SDK）
- ✅ 实现 Python 后端（6 个核心方法 + CLI）
- ✅ 创建 MCP 客户端桥接层（关键创新）
- ✅ 添加 FastAPI 路由（7 个 HTTP 端点）
- ✅ 注册路由到 main.py
- ✅ 添加完整文档和测试脚本

架构创新：
- 三层架构：FastAPI → MCP Client → MCP Server → Python Backend
- 双模式支持：主程序调用 + AI 助手调用
- MCP 客户端封装 JSON-RPC 协议复杂性
- 单例模式优化进程创建

文件清单：
- mcp-servers/knowledge-base/python/knowledge_base.py (460 行)
- mcp-servers/knowledge-base/src/index.ts (255 行)
- backend/core/mcp_client.py (178 行) - 关键桥接层
- backend/routers/knowledge.py (235 行)
- 配置文件：package.json, tsconfig.json, setup.sh
- 文档：README.md, QUICK_REFERENCE.md
- 测试：test_integration.sh, quick_verify.sh

API 端点：
- POST   /api/knowledge/search - 搜索知识
- POST   /api/knowledge/entries - 添加条目
- GET    /api/knowledge/entries/{id} - 获取详情
- POST   /api/knowledge/entries/list - 条目列表
- DELETE /api/knowledge/entries/{id} - 删除条目
- GET    /api/knowledge/statistics - 统计信息
- GET    /api/knowledge/health - 健康检查

与 document-parser 的区别：
- document-parser: AI 助手直接调用（独立运行）
- knowledge-base: 主程序 + AI 助手调用（集成模式）

验证方法：
cd mcp-servers/knowledge-base
./setup.sh && ./quick_verify.sh

参考文档：
- KNOWLEDGE_BASE_MCP_COMPLETE.md - 完整实现报告
- mcp-servers/knowledge-base/README.md - 使用文档
- mcp-servers/knowledge-base/QUICK_REFERENCE.md - 快速参考"

echo -e "${GREEN}✓ 提交成功${NC}"

# 5. 显示提交信息
echo ""
echo "5. 提交信息："
git log -1 --stat

echo ""
echo "======================================"
echo -e "${GREEN}✓ 提交完成！${NC}"
echo "======================================"
echo ""
echo "下一步："
echo "  1. 推送到远程: git push"
echo "  2. 验证 MCP: cd mcp-servers/knowledge-base && ./setup.sh"
echo "  3. 运行测试: ./quick_verify.sh"
echo ""
