#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "   投标智能系统 - 完整启动脚本"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 显示菜单
echo "请选择启动模式："
echo ""
echo "1. 🐳 Docker 启动（推荐）"
echo "2. 💻 本地启动（已禁用）"
echo "3. 📊 查看系统信息"
echo "4. 🛑 停止 Docker 服务"
echo "5. ❌ 退出"
echo ""
read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "   🐳 Docker 容器化启动"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        
        # 检查 Docker
        if ! command -v docker &> /dev/null; then
            echo "❌ 错误：未安装 Docker"
            echo "请访问 https://www.docker.com/get-started 安装 Docker"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            echo "❌ 错误：未安装 docker-compose"
            echo "请安装 docker-compose"
            exit 1
        fi
        
        # 检查环境变量
        if [ ! -f ".env" ]; then
            echo "📝 创建环境变量文件..."
            cp .env.docker .env
            echo "⚠️  请编辑 .env 文件填写 API Keys"
            echo ""
            read -p "是否现在编辑 .env? (y/n): " edit_env
            if [ "$edit_env" = "y" ]; then
                ${EDITOR:-nano} .env
            fi
        fi
        
        echo ""
        echo "🚀 启动 Docker 容器..."
        docker-compose up -d
        
        echo ""
        echo "✅ 启动完成！"
        echo ""
        echo "📊 服务状态:"
        docker-compose ps
        echo ""
        echo "🌐 访问地址:"
        echo "   前端: http://localhost:13000"
        echo "   后端: http://localhost:18888"
        echo "   API文档: http://localhost:18888/docs"
        echo ""
        echo "📝 查看日志: docker-compose logs -f"
        echo "🛑 停止服务: docker-compose down"
        ;;
        
    2)
        echo ""
        echo "❌ 本地启动已禁用（本项目强制使用 Docker）。"
        echo "   启动：docker compose up -d"
        echo "   访问：前端 http://localhost:13000  后端 http://localhost:18888"
        exit 1
        ;;
        
    3)
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "   系统信息"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        echo "📁 项目结构:"
        echo "   ├── backend/     (后端 - FastAPI + PostgreSQL)"
        echo "   └── frontend/    (前端 - React + TypeScript)"
        echo ""
        echo "🌐 访问地址:"
        echo "   前端: http://localhost:13000"
        echo "   后端: http://localhost:18888"
        echo "   API 文档: http://localhost:18888/docs"
        echo ""
        echo "🔑 默认登录:"
        echo "   用户名: admin"
        echo "   密码: admin123"
        echo ""
        echo "📊 前端功能:"
        echo "   ✅ 文件上传及存档"
        echo "   ✅ 逻辑学习（完整工作流）"
        echo ""
        ;;
        
    4)
        echo ""
        echo "═══════════════════════════════════════════════════════════"
        echo "   🛑 停止 Docker 服务"
        echo "═══════════════════════════════════════════════════════════"
        echo ""
        
        if ! command -v docker-compose &> /dev/null; then
            echo "❌ 未安装 docker-compose"
            exit 1
        fi
        
        echo "🛑 停止所有容器..."
        docker-compose down
        
        echo ""
        read -p "是否删除数据卷（将清空所有数据）? (y/n): " delete_volumes
        if [ "$delete_volumes" = "y" ]; then
            echo "⚠️  删除数据卷..."
            docker-compose down -v
            echo "✅ 已删除所有数据"
        else
            echo "✅ 数据已保留"
        fi
        ;;
        
    5)
        echo "👋 再见！"
        exit 0
        ;;
        
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
