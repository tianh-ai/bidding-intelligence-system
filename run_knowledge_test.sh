#!/bin/bash
# 知识库 MCP 一键测试脚本（Docker/HTTP）
# 说明：本脚本不启动任何服务，仅验证 Docker 运行链路：FastAPI → MCP → Ollama

set -euo pipefail

cd "$(dirname "$0")"

API_BASE="http://localhost:18888"
OLLAMA_BASE="http://127.0.0.1:11434"

echo "=========================================="
echo "知识库 MCP 测试（Docker/HTTP）"
echo "=========================================="
echo ""

echo "步骤 1/4: 检查 Ollama 服务..."
if curl -s "$OLLAMA_BASE/api/tags" > /dev/null 2>&1; then
    echo "✓ Ollama 服务正常: $OLLAMA_BASE"
else
    echo "✗ Ollama 服务未运行: $OLLAMA_BASE"
    echo "请先启动（宿主机）: ollama serve"
    exit 1
fi

echo ""
echo "步骤 2/4: 检查后端服务 (Docker 对外端口 18888)..."
if curl -s "$API_BASE/health" > /dev/null 2>&1; then
    echo "✓ 后端服务可访问: $API_BASE"
else
    echo "✗ 后端服务不可访问: $API_BASE"
    echo "请先启动（Docker）："
    echo "  docker compose up -d backend"
    exit 1
fi

echo ""
echo "步骤 3/4: 检查知识库健康与统计..."
echo "- GET /api/knowledge/health"
curl -s "$API_BASE/api/knowledge/health" | python3 -m json.tool

echo ""
echo "- GET /api/knowledge/statistics"
curl -s "$API_BASE/api/knowledge/statistics" | python3 -m json.tool

echo ""
echo "步骤 4/4: 验证检索能力（关键词 + 语义）..."

echo "- POST /api/knowledge/entries/list (limit=3)"
curl -s -X POST "$API_BASE/api/knowledge/entries/list" \
    -H "Content-Type: application/json" \
    -d '{"limit": 3, "offset": 0}' | python3 -m json.tool

echo ""
echo "- POST /api/knowledge/search (query=测试, limit=3)"
curl -s -X POST "$API_BASE/api/knowledge/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "测试", "limit": 3, "min_score": 0.0}' | python3 -m json.tool

echo ""
echo "- POST /api/knowledge/search/semantic (query=测试, limit=3)"
curl -s -X POST "$API_BASE/api/knowledge/search/semantic" \
    -H "Content-Type: application/json" \
    -d '{"query": "测试", "limit": 3, "min_similarity": 0.6}' | python3 -m json.tool

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "可选：如需重建向量索引（使用 Ollama embeddings）:"
echo "  curl -s -X POST $API_BASE/api/knowledge/reindex | python3 -m json.tool"
echo ""
