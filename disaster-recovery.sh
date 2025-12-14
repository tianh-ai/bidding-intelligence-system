#!/bin/bash
# 灾难恢复脚本 - 系统崩溃时的快速恢复

set -e

echo "🚨 灾难恢复系统"
echo "===================="
echo ""

show_menu() {
    echo "选择恢复场景："
    echo "1) 配置文件损坏 - 从备份恢复配置"
    echo "2) Docker 容器异常 - 重启容器"
    echo "3) 数据库损坏 - 恢复数据库"
    echo "4) Python 环境混乱 - 重建环境"
    echo "5) 完全恢复 - 从最新备份完整恢复"
    echo "6) 健康检查 - 诊断问题"
    echo "0) 退出"
    echo ""
}

# 1. 恢复配置文件
recover_config() {
    echo "🔧 恢复配置文件..."
    
    # 查找最新备份
    LATEST_BACKUP=$(ls -t /Volumes/ssd/bidding-data/backups/backup_*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        echo "❌ 未找到备份文件"
        echo "尝试从配置备份恢复..."
        LATEST_CONFIG=$(ls -t .config-backups/.env.* 2>/dev/null | head -1)
        if [ -n "$LATEST_CONFIG" ]; then
            cp "$LATEST_CONFIG" backend/.env
            echo "✅ 已恢复 backend/.env"
        fi
        return
    fi
    
    echo "📦 使用备份: $LATEST_BACKUP"
    
    # 解压到临时目录
    TEMP_DIR=$(mktemp -d)
    tar -xzf "$LATEST_BACKUP" -C "$TEMP_DIR"
    
    # 恢复配置
    BACKUP_DIR=$(ls -d "$TEMP_DIR"/backup_* | head -1)
    cp "$BACKUP_DIR"/config/backend.env backend/.env 2>/dev/null && echo "✅ backend/.env 已恢复"
    cp "$BACKUP_DIR"/config/frontend.env frontend/.env 2>/dev/null && echo "✅ frontend/.env 已恢复"
    
    # 清理
    rm -rf "$TEMP_DIR"
    
    # 验证
    ./config-guard.sh
}

# 2. 重启 Docker
recover_docker() {
    echo "🐳 重启 Docker 容器..."
    
    echo "⚠️  这将重启所有服务，可能需要几分钟"
    read -p "确认继续? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    docker-compose restart
    
    echo "⏳ 等待服务启动..."
    sleep 10
    
    # 验证
    ./integrity-check.sh
}

# 3. 恢复数据库
recover_database() {
    echo "🗄️  恢复数据库..."
    
    LATEST_BACKUP=$(ls -t /Volumes/ssd/bidding-data/backups/backup_*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        echo "❌ 未找到备份文件"
        return
    fi
    
    echo "⚠️  这将覆盖当前数据库架构！"
    read -p "确认继续? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    # 解压
    TEMP_DIR=$(mktemp -d)
    tar -xzf "$LATEST_BACKUP" -C "$TEMP_DIR"
    
    # 恢复
    BACKUP_DIR=$(ls -d "$TEMP_DIR"/backup_* | head -1)
    SQL_FILE=$(ls "$BACKUP_DIR"/database_schema_*.sql | head -1)
    
    if [ -n "$SQL_FILE" ]; then
        PGPASSWORD=postgres123 psql -h localhost -p 5433 -U postgres -d bidding_db < "$SQL_FILE"
        echo "✅ 数据库架构已恢复"
    fi
    
    rm -rf "$TEMP_DIR"
}

# 4. 重建 Python 环境
recover_python() {
    echo "🐍 重建 Python 环境..."
    
    echo "⚠️  这将卸载所有包并重新安装！"
    read -p "确认继续? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    if [ ! -f "backend/requirements.snapshot.txt" ]; then
        echo "❌ 未找到 requirements.snapshot.txt"
        return
    fi
    
    # 先创建快照
    ./CHANGE_MANAGEMENT.sh << INPUT
1

INPUT
    
    # 卸载所有包（保留 pip）
    pip3 freeze | grep -v "^pip==" | xargs pip3 uninstall -y
    
    # 重新安装
    pip3 install -r backend/requirements.snapshot.txt
    
    echo "✅ Python 环境已重建"
}

# 5. 完全恢复
full_recovery() {
    echo "🚨 完全恢复..."
    
    echo "⚠️  这将恢复所有配置和服务！"
    read -p "确认继续? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    echo "1/4 恢复配置..."
    recover_config
    
    echo "2/4 重启 Docker..."
    docker-compose restart
    sleep 10
    
    echo "3/4 验证配置..."
    ./config-guard.sh
    
    echo "4/4 完整性检查..."
    ./integrity-check.sh
    
    echo ""
    echo "✅ 完全恢复完成！"
}

# 6. 健康检查
health_check() {
    echo "🔍 运行健康检查..."
    ./integrity-check.sh
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 [0-6]: " choice
    
    case $choice in
        1) recover_config ;;
        2) recover_docker ;;
        3) recover_database ;;
        4) recover_python ;;
        5) full_recovery ;;
        6) health_check ;;
        0) echo "👋 退出"; exit 0 ;;
        *) echo "❌ 无效选项" ;;
    esac
    
    echo ""
    read -p "按回车继续..."
    echo ""
done
