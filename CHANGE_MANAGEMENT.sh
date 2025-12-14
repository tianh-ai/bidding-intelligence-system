#!/bin/bash
# 变更管理系统 - 防止随意修改环境

set -e

SNAPSHOT_DIR=".environment-snapshots"
mkdir -p "$SNAPSHOT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔍 环境变更管理系统"
echo "===================="
echo ""

# 显示菜单
show_menu() {
    echo "请选择操作："
    echo "1) 创建环境快照（安装包前必须执行）"
    echo "2) 对比环境变化"
    echo "3) 回滚到上一个快照"
    echo "4) 查看变更历史"
    echo "5) 验证当前环境"
    echo "0) 退出"
    echo ""
}

# 创建快照
create_snapshot() {
    echo "📸 创建环境快照..."
    
    SNAPSHOT_FILE="$SNAPSHOT_DIR/snapshot_$TIMESTAMP.txt"
    
    {
        echo "=== 快照时间 ==="
        date
        echo ""
        
        echo "=== Python 包 ==="
        pip3 freeze
        echo ""
        
        echo "=== Docker 容器 ==="
        docker-compose ps
        echo ""
        
        echo "=== 端口占用 ==="
        lsof -i :5173 -i :8000 -i :18888 -i :13000 -i :5433 -i :6380 2>/dev/null || echo "无占用"
        echo ""
        
        echo "=== 配置文件哈希 ==="
        [ -f backend/.env ] && echo "backend/.env: $(shasum -a 256 backend/.env | awk '{print $1}')"
        [ -f frontend/.env ] && echo "frontend/.env: $(shasum -a 256 frontend/.env | awk '{print $1}')"
        [ -f docker-compose.yml ] && echo "docker-compose.yml: $(shasum -a 256 docker-compose.yml | awk '{print $1}')"
        
    } > "$SNAPSHOT_FILE"
    
    echo "✅ 快照已保存: $SNAPSHOT_FILE"
    echo ""
    echo "⚠️  现在可以进行变更，完成后请运行选项 2 对比差异"
}

# 对比变化
compare_changes() {
    echo "🔍 对比环境变化..."
    
    LATEST_SNAPSHOT=$(ls -t $SNAPSHOT_DIR/snapshot_*.txt 2>/dev/null | head -1)
    
    if [ -z "$LATEST_SNAPSHOT" ]; then
        echo "❌ 没有找到快照文件，请先创建快照"
        return 1
    fi
    
    echo "📋 基准快照: $LATEST_SNAPSHOT"
    echo ""
    
    # 对比 Python 包
    echo "=== Python 包变化 ==="
    SNAPSHOT_PKGS=$(sed -n '/=== Python 包 ===/,/^$/p' "$LATEST_SNAPSHOT" | grep -v "===" | grep -v "^$")
    CURRENT_PKGS=$(pip3 freeze)
    
    echo "$SNAPSHOT_PKGS" > /tmp/snapshot_pkgs.txt
    echo "$CURRENT_PKGS" > /tmp/current_pkgs.txt
    
    NEW_PKGS=$(comm -13 <(sort /tmp/snapshot_pkgs.txt) <(sort /tmp/current_pkgs.txt))
    REMOVED_PKGS=$(comm -23 <(sort /tmp/snapshot_pkgs.txt) <(sort /tmp/current_pkgs.txt))
    
    if [ -n "$NEW_PKGS" ]; then
        echo "➕ 新增包:"
        echo "$NEW_PKGS"
    else
        echo "✅ 没有新增包"
    fi
    
    if [ -n "$REMOVED_PKGS" ]; then
        echo "➖ 删除包:"
        echo "$REMOVED_PKGS"
    else
        echo "✅ 没有删除包"
    fi
    
    echo ""
    
    # 对比配置文件
    echo "=== 配置文件变化 ==="
    for file in backend/.env frontend/.env docker-compose.yml; do
        if [ -f "$file" ]; then
            SNAPSHOT_HASH=$(grep "$file:" "$LATEST_SNAPSHOT" 2>/dev/null | awk '{print $2}')
            CURRENT_HASH=$(shasum -a 256 "$file" | awk '{print $1}')
            
            if [ "$SNAPSHOT_HASH" != "$CURRENT_HASH" ]; then
                echo "⚠️  $file 已修改"
            else
                echo "✅ $file 未改变"
            fi
        fi
    done
    
    echo ""
    echo "💡 如需回滚，请运行选项 3"
}

# 回滚
rollback_snapshot() {
    echo "⚠️  回滚环境..."
    echo "此功能仅供参考，实际回滚请手动执行"
    echo ""
    
    LATEST_SNAPSHOT=$(ls -t $SNAPSHOT_DIR/snapshot_*.txt 2>/dev/null | head -1)
    
    if [ -z "$LATEST_SNAPSHOT" ]; then
        echo "❌ 没有找到快照文件"
        return 1
    fi
    
    echo "建议回滚步骤："
    echo "1. 恢复配置文件: cp .config-backups/.env.xxx backend/.env"
    echo "2. 卸载新增的包: pip3 uninstall xxx"
    echo "3. 重启 Docker: docker-compose restart"
    echo "4. 运行验证: ./config-guard.sh"
}

# 查看历史
show_history() {
    echo "📜 变更历史..."
    echo ""
    
    if [ ! -d "$SNAPSHOT_DIR" ] || [ -z "$(ls $SNAPSHOT_DIR/snapshot_*.txt 2>/dev/null)" ]; then
        echo "❌ 没有变更历史"
        return 1
    fi
    
    ls -lt $SNAPSHOT_DIR/snapshot_*.txt | while read -r line; do
        FILE=$(echo $line | awk '{print $NF}')
        SNAPSHOT_TIME=$(grep "^$(date)" "$FILE" 2>/dev/null | head -1 || echo "未知时间")
        echo "📸 $FILE - $SNAPSHOT_TIME"
    done
}

# 验证环境
verify_environment() {
    echo "🔍 验证当前环境..."
    echo ""
    
    # 检查 Docker
    echo "=== Docker 状态 ==="
    docker-compose ps
    echo ""
    
    # 检查健康
    echo "=== 健康检查 ==="
    if curl -s http://localhost:18888/health | grep -q "healthy"; then
        echo "✅ 后端健康"
    else
        echo "❌ 后端异常"
    fi
    
    if curl -s http://localhost:13000 >/dev/null 2>&1; then
        echo "✅ 前端可访问"
    else
        echo "❌ 前端不可访问"
    fi
    echo ""
    
    # 运行配置守护
    echo "=== 配置验证 ==="
    ./config-guard.sh
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 [0-5]: " choice
    
    case $choice in
        1)
            create_snapshot
            ;;
        2)
            compare_changes
            ;;
        3)
            rollback_snapshot
            ;;
        4)
            show_history
            ;;
        5)
            verify_environment
            ;;
        0)
            echo "👋 退出"
            exit 0
            ;;
        *)
            echo "❌ 无效选项"
            ;;
    esac
    
    echo ""
    read -p "按回车继续..."
    echo ""
done
