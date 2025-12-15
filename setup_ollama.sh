#!/bin/bash

# Ollama 设置和测试脚本

set -e

echo "======================================"
echo "Ollama 向量搜索设置指南"
echo "======================================"
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. 检查 Ollama 是否安装
echo "1. 检查 Ollama 安装状态..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama 已安装${NC}"
    ollama --version
else
    echo -e "${YELLOW}⚠ Ollama 未安装${NC}"
    echo ""
    echo "请访问 https://ollama.com 下载安装"
    echo "或使用以下命令安装（macOS）："
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    exit 1
fi

echo ""

# 2. 检查 Ollama 服务状态
echo "2. 检查 Ollama 服务..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama 服务运行正常${NC}"
else
    echo -e "${YELLOW}⚠ Ollama 服务未启动${NC}"
    echo "启动 Ollama："
    echo "  ollama serve"
    echo ""
    exit 1
fi

echo ""

# 3. 检查/安装 embedding 模型
echo "3. 检查 embedding 模型..."
if ollama list | grep -q "nomic-embed-text"; then
    echo -e "${GREEN}✓ nomic-embed-text 模型已安装${NC}"
else
    echo -e "${YELLOW}⚠ nomic-embed-text 模型未安装${NC}"
    echo "正在下载模型（约 274MB）..."
    ollama pull nomic-embed-text
    echo -e "${GREEN}✓ 模型下载完成${NC}"
fi

echo ""

# 4. 测试 embedding 生成
echo "4. 测试 embedding 生成..."
TEST_RESPONSE=$(curl -s http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "测试文本"
}')

if echo "$TEST_RESPONSE" | grep -q "embedding"; then
    EMBEDDING_DIM=$(echo "$TEST_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['embedding']))")
    echo -e "${GREEN}✓ Embedding 生成成功${NC}"
    echo "  维度: $EMBEDDING_DIM"
else
    echo -e "${RED}✗ Embedding 生成失败${NC}"
    echo "响应: $TEST_RESPONSE"
    exit 1
fi

echo ""

# 5. 可选：安装聊天模型
echo "5. 可选聊天模型（用于 AI 增强功能）..."
if ollama list | grep -q "qwen2.5"; then
    echo -e "${GREEN}✓ qwen2.5 模型已安装${NC}"
else
    echo -e "${YELLOW}⚠ qwen2.5 模型未安装${NC}"
    read -p "是否下载 qwen2.5 模型（约 4.7GB）？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ollama pull qwen2.5:latest
        echo -e "${GREEN}✓ 模型下载完成${NC}"
    else
        echo "跳过聊天模型安装"
    fi
fi

echo ""

# 6. 测试 Python 客户端
echo "6. 测试 Python Ollama 客户端..."
cd backend
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from core.ollama_client import get_ollama_client
    
    client = get_ollama_client()
    
    # 健康检查
    is_healthy = await client.check_health()
    if not is_healthy:
        print('❌ Ollama 健康检查失败')
        return False
    
    print('✓ Ollama 客户端连接成功')
    
    # 生成 embedding
    embedding = await client.generate_embedding('这是一个测试')
    print(f'✓ Embedding 维度: {len(embedding)}')
    
    return True

result = asyncio.run(test())
sys.exit(0 if result else 1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python 客户端测试通过${NC}"
else
    echo -e "${RED}✗ Python 客户端测试失败${NC}"
    exit 1
fi

cd ..

echo ""

# 7. 检查数据库 vector 扩展
echo "7. 检查 PostgreSQL pgvector 扩展..."
PGVECTOR_CHECK=$(PGPASSWORD=postgres123 psql -h localhost -p 5433 -U postgres -d bidding_db -tAc "SELECT COUNT(*) FROM pg_extension WHERE extname='vector';" 2>/dev/null || echo "0")

if [ "$PGVECTOR_CHECK" = "1" ]; then
    echo -e "${GREEN}✓ pgvector 扩展已启用${NC}"
else
    echo -e "${YELLOW}⚠ pgvector 扩展未启用${NC}"
    echo "启用扩展："
    echo '  psql -h localhost -U postgres -d bidding_db -c "CREATE EXTENSION IF NOT EXISTS vector;"'
fi

echo ""

# 8. 总结
echo "======================================"
echo -e "${GREEN}✓ Ollama 向量搜索配置完成！${NC}"
echo "======================================"
echo ""
echo "配置摘要："
echo "  • Ollama 服务: http://localhost:11434"
echo "  • Embedding 模型: nomic-embed-text (${EMBEDDING_DIM}维)"
echo "  • 配置文件: backend/core/config.py"
echo "  • USE_OLLAMA_FOR_EMBEDDINGS: True"
echo ""
echo "下一步："
echo "  1. 启动后端服务（Docker）: docker compose up -d backend"
echo "  2. 测试语义搜索: curl -X POST http://localhost:18888/api/knowledge/search/semantic \\"
echo "                   -H 'Content-Type: application/json' \\"
echo "                   -d '{\"query\": \"投标要求\", \"limit\": 5}'"
echo "  3. 重建现有知识库索引: curl -X POST http://localhost:18888/api/knowledge/reindex"
echo ""
echo "性能建议："
echo "  • 首次生成 embedding 较慢（约 1-2秒/条）"
echo "  • 建议批量重建索引（batch_size=10）"
echo "  • 向量搜索比关键词搜索慢，但准确率高 30-50%"
echo ""
