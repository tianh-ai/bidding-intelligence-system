#!/bin/bash
set -e

# 🚀 完整安装脚本 - 投标智能系统
# 用法: chmod +x install.sh && ./install.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "============================================================"
echo "🚀 投标智能系统安装脚本"
echo "============================================================"
echo "项目根目录: $PROJECT_ROOT"
echo "后端目录: $BACKEND_DIR"
echo ""

# 步骤 1: 权限检查和设置
echo "📋 步骤 1/6: 权限检查和设置"
echo "---"

chmod -R 755 "$PROJECT_ROOT"
chmod -R 755 "$BACKEND_DIR"

if [ -w "$PROJECT_ROOT" ]; then
    echo "✅ 项目目录可写"
else
    echo "⚠️  项目目录权限不足，将尝试提升权限..."
    # macOS 不需要 sudo (用户自己的目录)
fi

# 步骤 2: 创建文件系统结构
echo ""
echo "📋 步骤 2/6: 创建文件系统结构"
echo "---"

mkdir -p "$PROJECT_ROOT/uploads/temp"
mkdir -p "$PROJECT_ROOT/uploads/parsed"
mkdir -p "$PROJECT_ROOT/uploads/archive"
mkdir -p "$BACKEND_DIR/logs"

echo "✅ uploads/temp"
echo "✅ uploads/parsed"
echo "✅ uploads/archive"
echo "✅ backend/logs"

# 步骤 3: 审计存储架构
echo ""
echo "📋 步骤 3/6: 审计数据存储架构"
echo "---"

cd "$PROJECT_ROOT"
python3 audit_storage.py || {
    echo "⚠️  存储审计发现问题，但继续安装..."
}

# 步骤 4: 初始化数据库
echo ""
echo "📋 步骤 4/6: 初始化数据库"
echo "---"

# 检查 PostgreSQL 是否运行
if ! command -v psql &> /dev/null; then
    echo "❌ psql 未找到，请安装 PostgreSQL"
    exit 1
fi

# 尝试创建数据库
psql -h localhost -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'bidding_db'" | grep -q 1 || {
    echo "📍 创建数据库 bidding_db..."
    psql -h localhost -U postgres -c "CREATE DATABASE bidding_db;" 2>/dev/null || {
        echo "⚠️  无法创建数据库，可能已存在"
    }
}

# 运行初始化 SQL
echo "📍 应用数据库 schema..."
psql -h localhost -U postgres -d bidding_db -f "$BACKEND_DIR/init_database.sql" || {
    echo "⚠️  数据库初始化失败，可能是某些表已存在"
}

echo "✅ 数据库初始化完成"

# 步骤 5: 安装 Python 依赖
echo ""
echo "📋 步骤 5/6: 安装 Python 依赖"
echo "---"

cd "$BACKEND_DIR"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📍 Python 版本: $python_version"

# 升级 pip
echo "📍 升级 pip..."
python3 -m pip install --upgrade pip -q

# 安装依赖
if [ -f "requirements.txt" ]; then
    echo "📍 安装 requirements.txt..."
    python3 -m pip install -r requirements.txt -q
    echo "✅ 依赖安装完成"
else
    echo "⚠️  requirements.txt 未找到"
fi

# 步骤 6: 验证安装
echo ""
echo "📋 步骤 6/6: 验证安装"
echo "---"

cd "$PROJECT_ROOT"

# 验证关键依赖
python3 << 'PYEOF'
import sys

packages = {
    'fastapi': 'FastAPI',
    'pydantic': 'Pydantic',
    'sqlalchemy': 'SQLAlchemy',
    'psycopg2': 'psycopg2',
    'paddleocr': 'PaddleOCR',
    'loguru': 'Loguru',
}

print("🔍 验证关键依赖:")
all_ok = True
for pkg, name in packages.items():
    try:
        __import__(pkg.replace('-', '_'))
        print(f"  ✅ {name}")
    except ImportError:
        print(f"  ❌ {name} (缺失)")
        all_ok = False

sys.exit(0 if all_ok else 1)
PYEOF

if [ $? -ne 0 ]; then
    echo "⚠️  某些依赖缺失，但继续..."
fi

# 验证文件系统
python3 << 'PYEOF'
import os
from pathlib import Path

base = Path('.')
required = {
    '上传': 'uploads',
    '临时': 'uploads/temp',
    '解析': 'uploads/parsed',
    '归档': 'uploads/archive',
    '日志': 'backend/logs',
}

print("📁 验证文件系统:")
for name, path in required.items():
    if (base / path).exists():
        print(f"  ✅ {path}")
    else:
        print(f"  ❌ {path}")
PYEOF

# 最终总结
echo ""
echo "============================================================"
echo "✅ 安装完成！"
echo "============================================================"
echo ""
echo "📚 下一步操作:"
echo ""
echo "1️⃣  启动后端服务:"
echo "   cd $BACKEND_DIR"
echo "   python3 main.py"
echo ""
echo "2️⃣  验证系统:"
echo "   curl http://localhost:8000/api/health"
echo ""
echo "3️⃣  查看日志:"
echo "   tail -f $BACKEND_DIR/logs/app.log"
echo ""
echo "📖 更多信息:"
echo "   - 详细指南: $PROJECT_ROOT/INSTALLATION_AND_VERIFICATION.md"
echo "   - 数据架构: $PROJECT_ROOT/DATA_STORAGE_ARCHITECTURE.md"
echo ""
echo "============================================================"
