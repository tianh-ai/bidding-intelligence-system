#!/bin/bash

echo "🚀 启动投标智能系统前端..."

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "📝 复制环境变量配置..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置 API 地址"
fi

# 启动开发服务器
echo "✅ 启动开发服务器..."
npm run dev
