#!/bin/bash

# 标书智能系统启动脚本
# 一键启动所有服务

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     标书智能系统 - 服务启动                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python环境
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 1/5：检查Python环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✅ Python版本: ${PYTHON_VERSION}${NC}"

# 检查Poetry
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}⚠️  Poetry未安装，正在安装...${NC}"
    pip install poetry
fi

echo -e "${GREEN}✅ Poetry已安装${NC}"
echo ""

# 安装依赖
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 2/5：安装依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ pyproject.toml不存在${NC}"
    exit 1
fi

echo "正在安装Python依赖..."
poetry install
echo -e "${GREEN}✅ 依赖安装完成${NC}"
echo ""

# 检查环境变量
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 3/5：检查环境配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env文件不存在，从模板创建...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ 已创建.env文件（请编辑配置）${NC}"
        echo -e "${YELLOW}⚠️  请配置以下必需项：${NC}"
        echo "   - OPENAI_API_KEY"
        echo "   - DB_PASSWORD"
        echo "   - SECRET_KEY"
        echo ""
        read -p "按Enter继续（确保已配置）..."
    else
        echo -e "${RED}❌ .env.example不存在${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env文件已存在${NC}"
fi
echo ""

# 创建必要目录
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 4/5：创建必要目录"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p uploads
mkdir -p logs
mkdir -p backend/uploads

echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

# 检查Redis
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 5/5：检查服务依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis已运行${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis未运行，尝试启动...${NC}"
        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes
            sleep 2
            if redis-cli ping &> /dev/null; then
                echo -e "${GREEN}✅ Redis已启动${NC}"
            else
                echo -e "${RED}❌ Redis启动失败${NC}"
            fi
        else
            echo -e "${RED}❌ Redis未安装${NC}"
            echo "请安装Redis: brew install redis 或 apt-get install redis-server"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Redis未安装（缓存功能将不可用）${NC}"
fi

# 检查PostgreSQL
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL已安装${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL未安装${NC}"
fi

echo ""

# 询问启动模式
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "选择启动模式："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 完整模式（FastAPI + Celery Worker）"
echo "2. 仅启动API服务"
echo "3. 仅启动Celery Worker"
echo ""
read -p "请选择 (1/2/3): " MODE

case $MODE in
    1)
        echo ""
        echo "🚀 启动完整服务..."
        echo ""
        
        # 启动Celery Worker（后台）
        echo "启动Celery Worker..."
        poetry run celery -A backend.worker worker --loglevel=info --detach
        sleep 2
        echo -e "${GREEN}✅ Celery Worker已启动${NC}"
        
        # 启动FastAPI
        echo ""
        echo "启动FastAPI服务..."
        echo -e "${GREEN}📡 API服务: http://localhost:8001${NC}"
        echo -e "${GREEN}📖 API文档: http://localhost:8001/docs${NC}"
        echo ""
        poetry run uvicorn backend.main:app --reload --port 8001
        ;;
    
    2)
        echo ""
        echo "🚀 启动API服务..."
        echo -e "${GREEN}📡 API服务: http://localhost:8001${NC}"
        echo -e "${GREEN}📖 API文档: http://localhost:8001/docs${NC}"
        echo ""
        poetry run uvicorn backend.main:app --reload --port 8001
        ;;
    
    3)
        echo ""
        echo "🚀 启动Celery Worker..."
        poetry run celery -A backend.worker worker --loglevel=info
        ;;
    
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac
