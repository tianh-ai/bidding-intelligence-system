#!/bin/bash
# ==============================================
# 标书智能系统 - 局域网部署 - 数据目录初始化脚本
# ==============================================

set -e  # 遇到错误立即退出

echo "========================================"
echo "  标书智能系统 - 数据目录初始化"
echo "========================================"
echo ""

# 读取.env.lan配置
if [ -f .env.lan ]; then
    export $(grep -v '^#' .env.lan | xargs)
else
    echo "⚠️  警告: .env.lan 文件不存在，使用默认配置"
fi

# 设置默认数据目录（如果环境变量未设置）
DATA_BASE_DIR="${HOST_DATA_BASE:-$HOME/bidding-data}"
POSTGRES_DIR="${HOST_DATA_POSTGRES:-$DATA_BASE_DIR/postgres}"
REDIS_DIR="${HOST_DATA_REDIS:-$DATA_BASE_DIR/redis}"
UPLOADS_DIR="${HOST_DATA_UPLOADS:-$DATA_BASE_DIR/uploads}"
LOGS_DIR="${HOST_DATA_LOGS:-$DATA_BASE_DIR/logs}"

echo "📁 数据存储基础目录: $DATA_BASE_DIR"
echo ""
echo "将创建以下目录:"
echo "  - PostgreSQL: $POSTGRES_DIR"
echo "  - Redis:      $REDIS_DIR"
echo "  - 上传文件:   $UPLOADS_DIR"
echo "  - 日志文件:   $LOGS_DIR"
echo ""

read -p "是否继续? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消操作"
    exit 1
fi

# 创建数据目录
echo ""
echo "🔨 创建数据目录..."

mkdir -p "$POSTGRES_DIR"
echo "✅ 已创建: $POSTGRES_DIR"

mkdir -p "$REDIS_DIR"
echo "✅ 已创建: $REDIS_DIR"

mkdir -p "$UPLOADS_DIR"
echo "✅ 已创建: $UPLOADS_DIR"

mkdir -p "$LOGS_DIR"
echo "✅ 已创建: $LOGS_DIR"

# 设置权限（确保Docker容器可以访问）
echo ""
echo "🔧 设置目录权限..."

chmod -R 755 "$DATA_BASE_DIR"
echo "✅ 已设置权限: $DATA_BASE_DIR"

# 创建README文件
cat > "$DATA_BASE_DIR/README.txt" << EOF
标书智能系统 - 数据存储目录
================================

此目录包含标书智能系统的所有持久化数据：

1. postgres/    - PostgreSQL数据库文件（24张表+向量索引）
2. redis/       - Redis缓存和任务队列数据
3. uploads/     - 用户上传的标书文件（PDF、Word等）
4. logs/        - 系统日志文件

⚠️ 重要提示：
- 请勿手动修改 postgres/ 和 redis/ 目录下的文件
- 定期备份此目录以防数据丢失
- 删除此目录将导致所有数据丢失

创建时间: $(date)
存储路径: $DATA_BASE_DIR
EOF

echo "✅ 已创建说明文件: $DATA_BASE_DIR/README.txt"

# 显示磁盘空间
echo ""
echo "💾 当前磁盘空间:"
df -h "$DATA_BASE_DIR" | tail -1 | awk '{print "  可用空间: " $4 " / " $2 " (已用 " $5 ")"}'

# 更新.env.lan文件中的路径
echo ""
echo "🔄 更新配置文件..."

if [ -f .env.lan ]; then
    # 备份原文件
    cp .env.lan .env.lan.backup
    
    # 更新路径（如果不存在则添加）
    sed -i '' "s|^HOST_DATA_POSTGRES=.*|HOST_DATA_POSTGRES=$POSTGRES_DIR|" .env.lan || \
        echo "HOST_DATA_POSTGRES=$POSTGRES_DIR" >> .env.lan
    
    sed -i '' "s|^HOST_DATA_REDIS=.*|HOST_DATA_REDIS=$REDIS_DIR|" .env.lan || \
        echo "HOST_DATA_REDIS=$REDIS_DIR" >> .env.lan
    
    sed -i '' "s|^HOST_DATA_UPLOADS=.*|HOST_DATA_UPLOADS=$UPLOADS_DIR|" .env.lan || \
        echo "HOST_DATA_UPLOADS=$UPLOADS_DIR" >> .env.lan
    
    sed -i '' "s|^HOST_DATA_LOGS=.*|HOST_DATA_LOGS=$LOGS_DIR|" .env.lan || \
        echo "HOST_DATA_LOGS=$LOGS_DIR" >> .env.lan
    
    echo "✅ 已更新 .env.lan 配置文件"
    echo "   (原文件已备份为 .env.lan.backup)"
fi

echo ""
echo "========================================" 
echo "✅ 数据目录初始化完成!"
echo "========================================"
echo ""
echo "📊 目录结构:"
tree -L 2 "$DATA_BASE_DIR" 2>/dev/null || ls -la "$DATA_BASE_DIR"
echo ""
echo "💡 下一步:"
echo "   1. 编辑 .env.lan 文件，设置API密钥和密码"
echo "   2. 运行 ./deploy-lan.sh 启动服务"
echo ""
