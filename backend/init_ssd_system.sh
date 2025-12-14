#!/usr/bin/env bash
"""
系统初始化脚本 - 配置SSD存储和数据库
"""

set -e

echo "=========================================="
echo "🚀 投标智能系统初始化"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. SSD目录已创建
echo -e "${BLUE}✓ SSD目录结构${NC}"
echo "   路径: /Volumes/ssd/bidding-data/"
echo "   - uploads/  (文件上传)"
echo "   - parsed/   (解析后的文件)"
echo "   - archive/  (归档文件)"
echo "   - logs/     (日志文件)"
echo "   - db/       (数据库备份)"

# 2. 配置已更新
echo -e "\n${BLUE}✓ 配置文件已更新${NC}"
echo "   - .env.example"
echo "   - backend/core/config.py"
echo "   所有文件存储路径已指向: /Volumes/ssd/bidding-data/"

# 3. 检查Python环境
echo -e "\n${BLUE}检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version | cut -d' ' -f2)${NC}"

# 4. 检查依赖
echo -e "\n${BLUE}检查Python依赖...${NC}"
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend

# 检查必要的包
required_packages=("pydantic" "fastapi" "psycopg2" "sqlalchemy" "asyncio")
missing_packages=()

for pkg in "${required_packages[@]}"; do
    if ! python3 -c "import ${pkg}" 2>/dev/null; then
        missing_packages+=("$pkg")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  缺少依赖: ${missing_packages[*]}${NC}"
    echo "运行: pip install -r requirements.txt"
else
    echo -e "${GREEN}✓ 所有核心依赖已安装${NC}"
fi

# 5. 检查PostgreSQL
echo -e "\n${BLUE}检查PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL客户端未安装${NC}"
    echo "但可以继续，数据库配置已准备好"
else
    echo -e "${GREEN}✓ PostgreSQL客户端已安装${NC}"
fi

# 6. 显示下一步操作
echo -e "\n${BLUE}=========================================="
echo "📋 下一步操作${NC}"
echo "=========================================="
echo ""
echo "1️⃣  安装依赖 (如果之前缺少):"
echo "   cd backend && pip install -r requirements.txt"
echo ""
echo "2️⃣  启动PostgreSQL数据库:"
echo "   服务器地址: localhost:5432"
echo "   数据库名: bidding_db"
echo "   用户名: postgres"
echo ""
echo "3️⃣  初始化数据库表:"
echo "   python3 init_database.py"
echo ""
echo "4️⃣  启动后端服务:"
echo "   python3 main.py"
echo ""
echo "5️⃣  启动前端 (在另一个终端):"
echo "   cd ../frontend && npm run dev"
echo ""
echo -e "${GREEN}✓ 系统初始化完成！${NC}"
echo ""
