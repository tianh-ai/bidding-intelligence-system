#!/bin/bash

# GitHub 自动上传脚本
# 帮助您快速将项目上传到GitHub

set -e

echo "=========================================="
echo "📤 GitHub 自动上传工具"
echo "=========================================="
echo ""

# 检查是否在git仓库中
if [ ! -d ".git" ]; then
    echo "❌ 错误：当前目录不是Git仓库"
    echo "请先运行: git init"
    exit 1
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 检测到未提交的更改"
    echo ""
    git status --short
    echo ""
    read -p "是否要提交所有更改? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        echo ""
        echo "请输入提交信息:"
        read -r COMMIT_MSG
        if [ -z "$COMMIT_MSG" ]; then
            COMMIT_MSG="chore: update code"
        fi
        git commit -m "$COMMIT_MSG"
        echo "✅ 更改已提交"
    else
        echo "⚠️  跳过提交"
    fi
fi

# 检查是否已配置远程仓库
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

if [ -z "$REMOTE_URL" ]; then
    echo ""
    echo "📍 配置GitHub远程仓库"
    echo ""
    echo "请输入您的GitHub用户名:"
    read -r GITHUB_USERNAME
    
    echo "请输入仓库名称 (默认: bidding-intelligence-system):"
    read -r REPO_NAME
    REPO_NAME=${REPO_NAME:-bidding-intelligence-system}
    
    echo ""
    echo "选择连接方式:"
    echo "1) HTTPS (推荐)"
    echo "2) SSH"
    read -p "请选择 (1 或 2): " -n 1 -r
    echo ""
    
    if [[ $REPLY == "2" ]]; then
        REMOTE_URL="git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git"
    else
        REMOTE_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
    fi
    
    git remote add origin "$REMOTE_URL"
    echo "✅ 远程仓库已配置: $REMOTE_URL"
else
    echo "✅ 远程仓库: $REMOTE_URL"
fi

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo ""
    read -p "当前分支是 '$CURRENT_BRANCH'，是否切换到 main? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout -b main 2>/dev/null || git checkout main
        echo "✅ 已切换到 main 分支"
    fi
fi

# 推送到GitHub
echo ""
echo "🚀 准备推送到GitHub..."
echo ""

if git ls-remote --exit-code origin &>/dev/null; then
    # 远程仓库存在，正常推送
    echo "推送到远程仓库..."
    git push -u origin main
else
    # 首次推送
    echo "首次推送到远程仓库..."
    git push -u origin main
fi

echo ""
echo "=========================================="
echo "✅ 上传成功！"
echo "=========================================="
echo ""
echo "🌐 访问您的项目:"
echo "   $REMOTE_URL"
echo ""
echo "📝 后续操作:"
echo "   1. 访问GitHub查看项目"
echo "   2. 创建Release发布版本"
echo "   3. 邀请协作者"
echo "   4. 配置GitHub Actions"
echo ""
echo "📚 更多信息请查看: GITHUB_UPLOAD_GUIDE.md"
echo "=========================================="
