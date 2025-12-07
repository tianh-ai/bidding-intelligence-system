#!/bin/bash
set -e

echo "=== Frontend Dependencies Installation ==="
echo "Current directory: $(pwd)"
echo "Date: $(date)"
echo ""

# 确保在正确目录
cd "$(dirname "$0")"
echo "Working in: $(pwd)"

# 验证 package.json 存在
if [ ! -f "package.json" ]; then
    echo "ERROR: package.json not found!"
    exit 1
fi

echo "✓ package.json found"
echo ""

# 清理旧文件
echo "Cleaning old files..."
rm -rf node_modules package-lock.json
echo "✓ Cleanup complete"
echo ""

# 配置 npm
echo "Configuring npm..."
npm config set registry https://registry.npmjs.org/
npm config set strict-ssl true
npm cache clean --force
echo "✓ NPM configured"
echo ""

# 安装依赖
echo "Installing dependencies (this may take a few minutes)..."
echo "Using: npm install --legacy-peer-deps"
echo ""

npm install --legacy-peer-deps

echo ""
echo "=== Installation Complete! ==="
echo "You can now run: npm run dev"
