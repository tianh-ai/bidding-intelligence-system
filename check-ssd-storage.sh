#!/bin/bash

###############################################################################
# 标书智能系统 - SSD 存储验证和管理脚本
###############################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_DIR="/Volumes/ssd/files/bidding-system"

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}标书智能系统 - 存储状态检查${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# 1. 检查SSD挂载
echo -e "${BLUE}1. SSD磁盘状态${NC}"
if [ -d "/Volumes/ssd" ]; then
    echo -e "${GREEN}✓ SSD已挂载${NC}"
    AVAILABLE=$(df -h /Volumes/ssd | tail -1 | awk '{print $4}')
    USED=$(df -h /Volumes/ssd | tail -1 | awk '{print $3}')
    PERCENT=$(df -h /Volumes/ssd | tail -1 | awk '{print $5}')
    echo -e "  已使用: ${USED}"
    echo -e "  可用空间: ${AVAILABLE}"
    echo -e "  使用率: ${PERCENT}"
else
    echo -e "${RED}✗ SSD未挂载${NC}"
    exit 1
fi
echo ""

# 2. 检查数据目录
echo -e "${BLUE}2. 数据目录状态${NC}"
DIRECTORIES=(
    "$BASE_DIR/data/postgres:PostgreSQL数据"
    "$BASE_DIR/data/redis:Redis数据"
    "$BASE_DIR/uploads:上传文件"
    "$BASE_DIR/logs:日志文件"
    "$BASE_DIR/backups:备份文件"
)

for dir_info in "${DIRECTORIES[@]}"; do
    IFS=':' read -r dir_path dir_name <<< "$dir_info"
    if [ -d "$dir_path" ]; then
        SIZE=$(du -sh "$dir_path" 2>/dev/null | awk '{print $1}')
        FILES=$(find "$dir_path" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo -e "${GREEN}✓${NC} ${dir_name}: ${SIZE} (${FILES} 文件)"
    else
        echo -e "${YELLOW}○${NC} ${dir_name}: 不存在"
    fi
done
echo ""

# 3. 检查Docker容器
echo -e "${BLUE}3. Docker容器状态${NC}"
if command -v docker &> /dev/null; then
    CONTAINERS=("bidding_postgres" "bidding_redis" "bidding_backend" "bidding_celery_worker" "bidding_frontend")
    for container in "${CONTAINERS[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
            STATUS=$(docker ps --filter "name=${container}" --format "{{.Status}}")
            echo -e "${GREEN}✓${NC} ${container}: ${STATUS}"
        else
            echo -e "${RED}✗${NC} ${container}: 未运行"
        fi
    done
else
    echo -e "${YELLOW}Docker未安装${NC}"
fi
echo ""

# 4. 检查数据库连接
echo -e "${BLUE}4. 数据库连接测试${NC}"
if docker ps --filter "name=bidding_postgres" --format "{{.Names}}" | grep -q "bidding_postgres"; then
    DB_TEST=$(docker exec bidding_postgres pg_isready -U postgres 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PostgreSQL: 可连接${NC}"
        
        # 查询数据库大小
        DB_SIZE=$(docker exec bidding_postgres psql -U postgres -d bidding_db -t -c "SELECT pg_size_pretty(pg_database_size('bidding_db'));" 2>/dev/null | tr -d ' ')
        if [ -n "$DB_SIZE" ]; then
            echo -e "  数据库大小: ${DB_SIZE}"
        fi
        
        # 查询表数量
        TABLE_COUNT=$(docker exec bidding_postgres psql -U postgres -d bidding_db -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
        if [ -n "$TABLE_COUNT" ]; then
            echo -e "  表数量: ${TABLE_COUNT}"
        fi
    else
        echo -e "${RED}✗ PostgreSQL: 无法连接${NC}"
    fi
else
    echo -e "${YELLOW}PostgreSQL容器未运行${NC}"
fi
echo ""

# 5. 检查Redis
echo -e "${BLUE}5. Redis连接测试${NC}"
if docker ps --filter "name=bidding_redis" --format "{{.Names}}" | grep -q "bidding_redis"; then
    REDIS_PING=$(docker exec bidding_redis redis-cli ping 2>&1)
    if [ "$REDIS_PING" = "PONG" ]; then
        echo -e "${GREEN}✓ Redis: 可连接${NC}"
        
        # 查询Redis内存使用
        REDIS_MEM=$(docker exec bidding_redis redis-cli INFO memory | grep "used_memory_human" | cut -d':' -f2 | tr -d '\r')
        if [ -n "$REDIS_MEM" ]; then
            echo -e "  内存使用: ${REDIS_MEM}"
        fi
    else
        echo -e "${RED}✗ Redis: 无法连接${NC}"
    fi
else
    echo -e "${YELLOW}Redis容器未运行${NC}"
fi
echo ""

# 6. 检查API健康
echo -e "${BLUE}6. API服务检查${NC}"
API_HEALTH=$(curl -s http://localhost:18888/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 后端API: 正常${NC}"
    echo -e "  响应: ${API_HEALTH}"
else
    echo -e "${RED}✗ 后端API: 无响应${NC}"
fi
echo ""

# 7. 存储建议
echo -e "${BLUE}7. 存储建议${NC}"
USED_PERCENT=$(df -h /Volumes/ssd | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$USED_PERCENT" -gt 80 ]; then
    echo -e "${RED}⚠ 警告: 磁盘使用率超过80%，建议清理旧文件${NC}"
elif [ "$USED_PERCENT" -gt 70 ]; then
    echo -e "${YELLOW}⚠ 提示: 磁盘使用率超过70%，注意监控空间${NC}"
else
    echo -e "${GREEN}✓ 磁盘空间充足${NC}"
fi

# 检查备份
BACKUP_COUNT=$(find "$BASE_DIR/backups" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$BACKUP_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠ 提示: 未发现备份文件，建议定期备份${NC}"
else
    echo -e "${GREEN}✓ 备份文件数: ${BACKUP_COUNT}${NC}"
fi
echo ""

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}检查完成${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# 8. 快捷命令提示
echo -e "${YELLOW}常用命令:${NC}"
echo -e "  查看上传文件: ls -lh ${BASE_DIR}/uploads/"
echo -e "  查看日志: tail -f ${BASE_DIR}/logs/backend/*.log"
echo -e "  备份数据库: docker exec bidding_postgres pg_dump -U postgres bidding_db > backup.sql"
echo -e "  清理临时文件: rm -rf ${BASE_DIR}/uploads/temp/*"
echo -e "  磁盘使用详情: du -sh ${BASE_DIR}/*"
echo ""
