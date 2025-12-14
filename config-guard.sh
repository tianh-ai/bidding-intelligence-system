#!/bin/bash
# 配置守护脚本 - 防止配置被错误修改
# 每次启动前自动验证和修复配置

set -e

CONFIG_DIR="/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system"
BACKUP_DIR="$CONFIG_DIR/.config-backups"
LOCK_FILE="$CONFIG_DIR/.config.lock"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo "🛡️  配置守护检查"
echo "===================="
echo ""

# 检查并修复 .env 文件
check_env_file() {
    local file=$1
    local key=$2
    local expected_value=$3
    local full_path="$CONFIG_DIR/$file"
    
    if [ ! -f "$full_path" ]; then
        echo "❌ 文件不存在: $file"
        return 1
    fi
    
    # 读取当前值
    local current_value=$(grep "^$key=" "$full_path" 2>/dev/null | cut -d'=' -f2-)
    
    if [ "$current_value" != "$expected_value" ]; then
        echo "⚠️  [$file] $key 配置错误"
        echo "   当前值: $current_value"
        echo "   期望值: $expected_value"
        
        # 备份原文件
        cp "$full_path" "$BACKUP_DIR/$(basename $file).$(date +%Y%m%d_%H%M%S).bak"
        
        # 修复配置
        if grep -q "^$key=" "$full_path"; then
            # 替换现有行
            sed -i '' "s|^$key=.*|$key=$expected_value|" "$full_path"
        else
            # 添加新行
            echo "$key=$expected_value" >> "$full_path"
        fi
        echo "   ✅ 已自动修复"
        return 0
    else
        echo "✅ [$file] $key = $expected_value"
        return 0
    fi
}

# 检查代码文件中的硬编码
check_code_file() {
    local file=$1
    local check_type=$2
    local full_path="$CONFIG_DIR/$file"
    
    case $check_type in
        "port_default")
            if grep -q 'DB_PORT.*5432' "$full_path"; then
                echo "❌ [$file] 发现错误的默认端口 5432"
                cp "$full_path" "$BACKUP_DIR/$(basename $file).$(date +%Y%m%d_%H%M%S).bak"
                sed -i '' 's/DB_PORT.*5432/DB_PORT", 5433/g' "$full_path"
                echo "   ✅ 已修复为 5433"
            else
                echo "✅ [$file] 端口默认值正确"
            fi
            ;;
        "password_default")
            if grep -q 'your-super-secret-and-long-postgres-password' "$full_path"; then
                echo "❌ [$file] 发现错误的默认密码"
                cp "$full_path" "$BACKUP_DIR/$(basename $file).$(date +%Y%m%d_%H%M%S).bak"
                sed -i '' 's/your-super-secret-and-long-postgres-password/postgres123/g' "$full_path"
                echo "   ✅ 已修复密码"
            else
                echo "✅ [$file] 密码默认值正确"
            fi
            ;;
        "database_default")
            if grep -q 'DB_NAME.*"postgres"' "$full_path"; then
                echo "❌ [$file] 发现错误的默认数据库名"
                cp "$full_path" "$BACKUP_DIR/$(basename $file).$(date +%Y%m%d_%H%M%S).bak"
                sed -i '' 's/DB_NAME", "postgres"/DB_NAME", "bidding_db"/g' "$full_path"
                echo "   ✅ 已修复数据库名"
            else
                echo "✅ [$file] 数据库名默认值正确"
            fi
            ;;
    esac
}

# 生成配置锁文件（记录正确状态的哈希）
generate_lock() {
    echo "# 配置文件哈希值 - 用于检测意外修改" > "$LOCK_FILE"
    echo "# 生成时间: $(date)" >> "$LOCK_FILE"
    echo "" >> "$LOCK_FILE"
    
    for file in "backend/.env" "frontend/.env" "backend/database/connection.py"; do
        if [ -f "$CONFIG_DIR/$file" ]; then
            local hash=$(shasum -a 256 "$CONFIG_DIR/$file" | awk '{print $1}')
            echo "$file:$hash" >> "$LOCK_FILE"
        fi
    done
    
    echo "🔒 已生成配置锁文件"
}

# 检查配置是否被意外修改
check_lock() {
    if [ ! -f "$LOCK_FILE" ]; then
        return
    fi
    
    echo ""
    echo "🔍 检查配置文件完整性..."
    
    while IFS=: read -r file expected_hash; do
        if [[ $file == \#* ]] || [ -z "$file" ]; then
            continue
        fi
        
        if [ -f "$CONFIG_DIR/$file" ]; then
            local current_hash=$(shasum -a 256 "$CONFIG_DIR/$file" | awk '{print $1}')
            if [ "$current_hash" != "$expected_hash" ]; then
                echo "⚠️  检测到 $file 被修改"
            fi
        fi
    done < "$LOCK_FILE"
}

# 主检查流程
echo "📋 检查环境变量配置..."
while IFS= read -r line; do
    [[ $line =~ ^([^:]+):([^:]+):(.+)$ ]] || continue
    file="${BASH_REMATCH[1]}"
    key="${BASH_REMATCH[2]}"
    value="${BASH_REMATCH[3]}"
    check_env_file "$file" "$key" "$value"
done << 'EOF'
backend/.env:DB_HOST:localhost
backend/.env:DB_PORT:5433
backend/.env:DB_USER:postgres
backend/.env:DB_PASSWORD:postgres123
backend/.env:DB_NAME:bidding_db
backend/.env:REDIS_HOST:localhost
backend/.env:REDIS_PORT:6379
frontend/.env:VITE_API_URL:http://localhost:18888
frontend/.env:VITE_DEFAULT_ADMIN_USERNAME:admin
frontend/.env:VITE_DEFAULT_ADMIN_PASSWORD:bidding2024
EOF

echo ""
echo "📋 检查代码文件硬编码..."
while IFS= read -r line; do
    [[ $line =~ ^([^:]+):(.+)$ ]] || continue
    file="${BASH_REMATCH[1]}"
    check_type="${BASH_REMATCH[2]}"
    check_code_file "$file" "$check_type"
done << 'EOF'
backend/database/connection.py:port_default
backend/database/connection.py:password_default
backend/database/connection.py:database_default
EOF

# 检查是否有意外修改
check_lock

# 生成新的锁文件
generate_lock

echo ""
echo "🎯 配置验证完成！"
echo ""
echo "💾 备份文件位置: $BACKUP_DIR"
echo "   如需恢复: cp $BACKUP_DIR/xxx.bak $CONFIG_DIR/xxx"
echo ""
