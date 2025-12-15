#!/bin/bash
set -e

echo "=== Logic Learning MCP Server Setup ==="

# 1. 安装依赖
echo "Installing Node.js dependencies..."
npm install

# 2. 编译 TypeScript
echo "Building TypeScript..."
npm run build

# 3. 赋予可执行权限
echo "Setting executable permissions..."
chmod +x dist/index.js

# 4. 测试服务
echo "Testing MCP server..."
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | node dist/index.js || true

echo "✅ Setup complete!"
echo "To test: echo '{\"jsonrpc\": \"2.0\", \"method\": \"tools/list\", \"id\": 1}' | node dist/index.js"
