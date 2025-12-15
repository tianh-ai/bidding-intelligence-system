#!/bin/bash

# Ollama + mxbai-embed-large 一键安装脚本
# 高精度向量搜索配置

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "======================================"
echo "Ollama 高精度模型一键安装"
echo "======================================"
echo ""

# 1. 检查 Ollama 是否已安装
echo -e "${BLUE}步骤 1/6: 检查 Ollama 安装状态...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama 已安装${NC}"
    ollama --version
else
    echo -e "${YELLOW}⚠ Ollama 未安装，开始安装...${NC}"
    
    # 检测操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "检测到 macOS 系统"
        echo "下载并安装 Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "检测到 Linux 系统"
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo -e "${RED}✗ 不支持的操作系统: $OSTYPE${NC}"
        echo "请访问 https://ollama.com 手动下载安装"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Ollama 安装完成${NC}"
fi

echo ""

# 2. 启动 Ollama 服务
echo -e "${BLUE}步骤 2/6: 启动 Ollama 服务...${NC}"

# 检查服务是否已运行
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama 服务已运行${NC}"
else
    echo -e "${YELLOW}⚠ 启动 Ollama 服务...${NC}"
    
    # 后台启动服务
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    
    # 等待服务启动
    echo "等待服务启动（最多 10 秒）..."
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ollama 服务启动成功 (PID: $OLLAMA_PID)${NC}"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${RED}✗ 服务启动失败${NC}"
        echo "请手动运行: ollama serve"
        exit 1
    fi
fi

echo ""

# 3. 下载 mxbai-embed-large 模型
echo -e "${BLUE}步骤 3/6: 下载 mxbai-embed-large 模型（669MB）...${NC}"
echo -e "${YELLOW}这可能需要几分钟，请耐心等待...${NC}"

if ollama list | grep -q "mxbai-embed-large"; then
    echo -e "${GREEN}✓ mxbai-embed-large 模型已安装${NC}"
else
    echo "开始下载..."
    ollama pull mxbai-embed-large
    echo -e "${GREEN}✓ 模型下载完成${NC}"
fi

echo ""

# 4. 验证模型
echo -e "${BLUE}步骤 4/6: 验证模型功能...${NC}"

TEST_RESPONSE=$(curl -s http://localhost:11434/api/embeddings -d '{
  "model": "mxbai-embed-large",
  "prompt": "这是一个高精度测试"
}')

if echo "$TEST_RESPONSE" | grep -q "embedding"; then
    EMBEDDING_DIM=$(echo "$TEST_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['embedding']))" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ 模型测试成功${NC}"
    echo "  向量维度: $EMBEDDING_DIM"
else
    echo -e "${RED}✗ 模型测试失败${NC}"
    echo "响应: $TEST_RESPONSE"
    exit 1
fi

echo ""

# 5. 测试 Python 客户端
echo -e "${BLUE}步骤 5/6: 测试 Python 集成...${NC}"

cd "$(dirname "$0")/backend"

python3 << 'EOF'
import asyncio
import sys

async def test():
    try:
        from core.ollama_client import get_ollama_client
        
        client = get_ollama_client()
        
        # 健康检查
        is_healthy = await client.check_health()
        if not is_healthy:
            print("❌ Ollama 健康检查失败")
            return False
        
        print("✓ Ollama 客户端连接成功")
        
        # 生成 embedding
        embedding = await client.generate_embedding("这是一个高精度测试")
        print(f"✓ Embedding 生成成功，维度: {len(embedding)}")
        
        # 验证配置
        from core.config import get_settings
        settings = get_settings()
        print(f"✓ 配置模型: {settings.OLLAMA_EMBEDDING_MODEL}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python 集成测试通过${NC}"
else
    echo -e "${RED}✗ Python 集成测试失败${NC}"
    exit 1
fi

cd ..

echo ""

# 6. 检查数据库扩展
echo -e "${BLUE}步骤 6/6: 检查 PostgreSQL pgvector 扩展...${NC}"

# 尝试连接数据库（如果配置了环境变量）
if [ -n "$DB_PASSWORD" ]; then
    PGVECTOR_CHECK=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -U postgres -d bidding_db -tAc "SELECT COUNT(*) FROM pg_extension WHERE extname='vector';" 2>/dev/null || echo "0")
    
    if [ "$PGVECTOR_CHECK" = "1" ]; then
        echo -e "${GREEN}✓ pgvector 扩展已启用${NC}"
    else
        echo -e "${YELLOW}⚠ pgvector 扩展未启用${NC}"
        echo "请运行以下命令启用:"
        echo "  psql -h localhost -U postgres -d bidding_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
    fi
else
    echo -e "${YELLOW}⚠ 未配置数据库连接，跳过检查${NC}"
    echo "如需启用 pgvector，请运行:"
    echo "  psql -h localhost -U postgres -d bidding_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
fi

echo ""

# 完成总结
echo "======================================"
echo -e "${GREEN}✓ 安装完成！${NC}"
echo "======================================"
echo ""
echo "配置摘要:"
echo "  • Ollama 服务: http://localhost:11434"
echo "  • Embedding 模型: mxbai-embed-large"
echo "  • 向量维度: 1024 (高精度)"
echo "  • 模型大小: 669MB"
echo ""
echo "下一步操作:"
echo "  1. 启动后端服务:"
echo "     cd backend && python main.py"
echo ""
echo "  2. 测试语义搜索:"
echo "     curl -X POST http://localhost:18888/api/knowledge/search/semantic \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"query\": \"投标要求\", \"limit\": 5}'"
echo ""
echo "  3. 重建知识库索引（如果有现有数据）:"
echo "     curl -X POST http://localhost:18888/api/knowledge/reindex \\"
echo "       -d '{\"batch_size\": 10}'"
echo ""
echo "性能说明:"
echo "  • mxbai-embed-large 提供最高精度"
echo "  • 向量维度 1024 (vs 768)"
echo "  • 生成速度: ~2-3秒/条（首次），~1-2秒/条（后续）"
echo "  • 准确率提升: 比 nomic-embed-text 高 10-15%"
echo ""
echo -e "${GREEN}准备就绪！开始使用高精度向量搜索吧！${NC} 🚀"
echo ""
