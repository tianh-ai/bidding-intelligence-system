#!/bin/bash

###############################################################################
# 标书智能系统 - SSD 数据目录初始化脚本
# 功能：自动创建所有必需的数据存储目录
# 位置：/Volumes/ssd/files/bidding-system/
###############################################################################

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# SSD 基础路径
BASE_DIR="/Volumes/ssd/files/bidding-system"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}标书智能系统 - 数据目录初始化${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 SSD 是否挂载
if [ ! -d "/Volumes/ssd" ]; then
    echo -e "${RED}❌ 错误：SSD 磁盘未挂载到 /Volumes/ssd${NC}"
    echo -e "${YELLOW}   请确保外接 SSD 已连接并挂载${NC}"
    exit 1
fi

echo -e "${GREEN}✓ SSD 磁盘已挂载${NC}"
echo ""

# 检查可用空间
AVAILABLE=$(df -h /Volumes/ssd | tail -1 | awk '{print $4}')
echo -e "${BLUE}可用空间: ${AVAILABLE}${NC}"
echo ""

# 创建目录结构
echo -e "${BLUE}开始创建目录结构...${NC}"
echo ""

# 定义需要创建的目录列表
DIRECTORIES=(
    "$BASE_DIR"
    "$BASE_DIR/data"
    "$BASE_DIR/data/postgres"
    "$BASE_DIR/data/redis"
    "$BASE_DIR/uploads"
    "$BASE_DIR/uploads/temp"
    "$BASE_DIR/uploads/parsed"
    "$BASE_DIR/uploads/archive"
    "$BASE_DIR/uploads/archive/2024"
    "$BASE_DIR/uploads/archive/2025"
    "$BASE_DIR/logs"
    "$BASE_DIR/logs/backend"
    "$BASE_DIR/logs/celery"
    "$BASE_DIR/backups"
    "$BASE_DIR/backups/db"
    "$BASE_DIR/backups/files"
)

# 创建每个目录
for dir in "${DIRECTORIES[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✓ 创建: ${dir}${NC}"
    else
        echo -e "${YELLOW}○ 已存在: ${dir}${NC}"
    fi
done

echo ""

# 设置目录权限（确保Docker容器可以写入）
echo -e "${BLUE}设置目录权限...${NC}"
chmod -R 777 "$BASE_DIR/data/postgres" 2>/dev/null || true
chmod -R 777 "$BASE_DIR/data/redis" 2>/dev/null || true
chmod -R 777 "$BASE_DIR/uploads" 2>/dev/null || true
chmod -R 777 "$BASE_DIR/logs" 2>/dev/null || true
chmod -R 777 "$BASE_DIR/backups" 2>/dev/null || true

echo -e "${GREEN}✓ 权限设置完成${NC}"
echo ""

# 创建 README 文件
README_FILE="$BASE_DIR/README.md"
cat > "$README_FILE" << 'EOF'
# 标书智能系统 - 数据存储目录

此目录存储标书智能系统的所有数据文件。

## 目录结构

```
/Volumes/ssd/files/bidding-system/
├── data/              # 数据库数据
│   ├── postgres/      # PostgreSQL 数据文件
│   └── redis/         # Redis 持久化数据
├── uploads/           # 上传文件
│   ├── temp/          # 临时上传文件
│   ├── parsed/        # 解析后的文件
│   └── archive/       # 归档文件
│       ├── 2024/      # 按年份归档
│       └── 2025/
├── logs/              # 日志文件
│   ├── backend/       # 后端日志
│   └── celery/        # Celery 任务日志
└── backups/           # 备份文件
    ├── db/            # 数据库备份
    └── files/         # 文件备份
```

## 重要说明

1. **请勿手动删除** 此目录下的任何文件，除非你知道自己在做什么
2. **定期备份** data/ 目录到其他位置
3. **磁盘空间** 定期检查可用空间，建议保持至少 50GB 可用
4. **数据安全** 如需迁移系统，备份整个 bidding-system 目录

## 维护

- 清理临时文件：`rm -rf uploads/temp/*`
- 查看磁盘使用：`du -sh *`
- 备份数据库：使用系统提供的备份功能

---
创建时间: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo -e "${GREEN}✓ 创建 README 文件${NC}"
echo ""

# 创建 .gitignore (避免意外提交数据文件)
GITIGNORE_FILE="$BASE_DIR/.gitignore"
cat > "$GITIGNORE_FILE" << 'EOF'
# 忽略所有数据文件
data/
uploads/
logs/
backups/

# 保留目录结构
!**/.gitkeep
EOF

echo -e "${GREEN}✓ 创建 .gitignore 文件${NC}"
echo ""

# 显示目录树结构
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}目录结构预览:${NC}"
echo -e "${BLUE}========================================${NC}"
if command -v tree &> /dev/null; then
    tree -L 3 -d "$BASE_DIR"
else
    find "$BASE_DIR" -maxdepth 3 -type d | sort
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 初始化完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}数据存储位置: ${BASE_DIR}${NC}"
echo -e "${YELLOW}可用空间: $(df -h /Volumes/ssd | tail -1 | awk '{print $4}')${NC}"
echo ""
echo -e "${GREEN}下一步: 启动 Docker 容器${NC}"
echo -e "  ${BLUE}docker compose -f docker-compose.lan.yml up -d${NC}"
echo ""
