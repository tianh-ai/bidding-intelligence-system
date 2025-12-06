#!/bin/bash

# GitHub HTTPS 上传助手脚本

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     GitHub HTTPS 上传助手                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 检查是否在git仓库中
if [ ! -d ".git" ]; then
    echo "❌ 错误：当前目录不是Git仓库"
    exit 1
fi

# 步骤1：配置Git用户信息
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 1/4：配置Git用户信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CURRENT_USER=$(git config --global user.name 2>/dev/null || echo "")
CURRENT_EMAIL=$(git config --global user.email 2>/dev/null || echo "")

if [ -n "$CURRENT_USER" ] && [ -n "$CURRENT_EMAIL" ]; then
    echo "✅ 已配置Git用户信息："
    echo "   姓名: $CURRENT_USER"
    echo "   邮箱: $CURRENT_EMAIL"
    echo ""
    read -p "是否使用当前配置? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "请输入您的姓名:"
        read -r GIT_NAME
        echo "请输入您的邮箱:"
        read -r GIT_EMAIL
        git config --global user.name "$GIT_NAME"
        git config --global user.email "$GIT_EMAIL"
        echo "✅ Git用户信息已更新"
    fi
else
    echo "请输入您的GitHub用户名或姓名:"
    read -r GIT_NAME
    echo "请输入您的GitHub邮箱:"
    read -r GIT_EMAIL
    git config --global user.name "$GIT_NAME"
    git config --global user.email "$GIT_EMAIL"
    echo "✅ Git用户信息已配置"
fi

echo ""

# 步骤2：输入GitHub信息
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 2/4：GitHub仓库信息"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "请输入您的GitHub用户名:"
read -r GITHUB_USERNAME

echo "请输入仓库名称 (默认: bidding-intelligence-system):"
read -r REPO_NAME
REPO_NAME=${REPO_NAME:-bidding-intelligence-system}

REMOTE_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo ""
echo "仓库URL: $REMOTE_URL"
echo ""

# 步骤3：输入Personal Access Token
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 3/4：Personal Access Token"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 如果您还没有创建Token，请按以下步骤操作："
echo ""
echo "1. 访问: https://github.com/settings/tokens"
echo "2. 点击 'Generate new token' → 'Generate new token (classic)'"
echo "3. Note: 填写 'bidding-system-upload'"
echo "4. Expiration: 选择 '90 days'"
echo "5. Select scopes: 勾选 'repo'"
echo "6. 点击 'Generate token' 并复制Token"
echo ""
echo "⚠️  Token格式类似: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo ""
echo "请粘贴您的Personal Access Token:"
read -rs GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Token不能为空"
    exit 1
fi

echo "✅ Token已接收"
echo ""

# 步骤4：推送到GitHub
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 4/4：推送代码到GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 删除已存在的origin（如果有）
git remote remove origin 2>/dev/null || true

# 添加带Token的远程仓库
REMOTE_URL_WITH_TOKEN="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
git remote add origin "$REMOTE_URL_WITH_TOKEN"

echo "📤 正在推送代码..."
echo ""

# 推送代码
if git push -u origin main; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 上传成功！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 访问您的项目:"
    echo "   https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
    echo ""
    echo "📝 后续建议操作:"
    echo "   1. 在GitHub页面添加项目描述和Topics"
    echo "   2. 创建v1.0.0 Release"
    echo "   3. 检查GitHub Actions是否正常运行"
    echo ""
    
    # 清理含有Token的remote URL（安全考虑）
    git remote remove origin
    git remote add origin "$REMOTE_URL"
    
    echo "🔒 已自动清理Token信息，安全配置已更新"
    echo ""
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能的原因："
    echo "1. Token权限不足（需要 'repo' 权限）"
    echo "2. 仓库不存在（需要先在GitHub创建）"
    echo "3. Token已过期"
    echo "4. 网络问题"
    echo ""
    
    # 清理
    git remote remove origin 2>/dev/null || true
    git remote add origin "$REMOTE_URL"
    
    exit 1
fi
