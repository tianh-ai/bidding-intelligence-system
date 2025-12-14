#!/bin/bash
# 自动备份系统 - 定期备份关键文件

set -e

BACKUP_ROOT="/Volumes/ssd/bidding-data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/backup_$TIMESTAMP"

echo "💾 自动备份系统"
echo "===================="
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 1. 备份配置文件
echo "📋 备份配置文件..."
mkdir -p "$BACKUP_DIR/config"
cp backend/.env "$BACKUP_DIR/config/backend.env" 2>/dev/null || echo "⚠️  backend/.env 不存在"
cp frontend/.env "$BACKUP_DIR/config/frontend.env" 2>/dev/null || echo "⚠️  frontend/.env 不存在"
cp docker-compose.yml "$BACKUP_DIR/config/" 2>/dev/null || true
cp .env.template "$BACKUP_DIR/config/" 2>/dev/null || true

# 2. 备份 Python 环境
echo "🐍 备份 Python 环境..."
pip3 freeze > "$BACKUP_DIR/requirements_$TIMESTAMP.txt"

# 3. 备份数据库架构
echo "🗄️  备份数据库架构..."
PGPASSWORD=postgres123 pg_dump -h localhost -p 5433 -U postgres -d bidding_db --schema-only > "$BACKUP_DIR/database_schema_$TIMESTAMP.sql" 2>/dev/null || echo "⚠️  数据库备份失败"

# 4. 备份关键脚本
echo "📜 备份管理脚本..."
mkdir -p "$BACKUP_DIR/scripts"
cp *.sh "$BACKUP_DIR/scripts/" 2>/dev/null || true
cp *.md "$BACKUP_DIR/scripts/" 2>/dev/null || true

# 5. 备份 Docker 配置
echo "🐳 备份 Docker 配置..."
docker-compose config > "$BACKUP_DIR/docker-compose.resolved.yml" 2>/dev/null || true
docker-compose ps --format json > "$BACKUP_DIR/docker_containers_$TIMESTAMP.json" 2>/dev/null || true

# 6. 创建备份清单
echo "📝 生成备份清单..."
cat > "$BACKUP_DIR/BACKUP_INFO.txt" << BACKUP_EOF
备份时间: $(date)
备份目录: $BACKUP_DIR

=== 系统状态 ===
Python 版本: $(python3 --version)
Node 版本: $(node --version 2>/dev/null || echo "未安装")
Docker 版本: $(docker --version)

=== 服务状态 ===
$(docker-compose ps 2>/dev/null || echo "Docker 未运行")

=== 环境检查 ===
后端配置: $([ -f backend/.env ] && echo "存在" || echo "缺失")
前端配置: $([ -f frontend/.env ] && echo "存在" || echo "缺失")
数据库: $(PGPASSWORD=postgres123 psql -h localhost -p 5433 -U postgres -d bidding_db -c "SELECT 1;" 2>/dev/null && echo "正常" || echo "异常")

=== 备份内容 ===
$(ls -lh "$BACKUP_DIR")
BACKUP_EOF

# 7. 压缩备份
echo "🗜️  压缩备份..."
cd "$BACKUP_ROOT"
tar -czf "backup_$TIMESTAMP.tar.gz" "backup_$TIMESTAMP" 2>/dev/null || echo "⚠️  压缩失败"

# 8. 清理旧备份（保留最近7天）
echo "🧹 清理旧备份..."
find "$BACKUP_ROOT" -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_ROOT" -name "backup_*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true

# 9. 显示备份信息
echo ""
echo "✅ 备份完成！"
echo ""
echo "备份位置: $BACKUP_DIR"
echo "压缩文件: $BACKUP_ROOT/backup_$TIMESTAMP.tar.gz"
echo "备份大小: $(du -sh "$BACKUP_DIR" | awk '{print $1}')"
echo ""
echo "恢复方法："
echo "  1. 解压: tar -xzf backup_$TIMESTAMP.tar.gz"
echo "  2. 查看清单: cat backup_$TIMESTAMP/BACKUP_INFO.txt"
echo "  3. 恢复配置: cp backup_$TIMESTAMP/config/*.env ."
echo "  4. 恢复数据库: psql -h localhost -p 5433 -U postgres -d bidding_db < backup_$TIMESTAMP/database_schema_*.sql"
echo ""

# 10. 列出最近的备份
echo "📚 最近的备份："
ls -lht "$BACKUP_ROOT"/backup_*.tar.gz 2>/dev/null | head -5 || echo "无备份"
