#!/bin/bash

# 快速推送脚本（已移除GitHub Actions文件）

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "GitHub 快速推送"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "GitHub用户名: tianh-ai"
echo "仓库名称: bidding-intelligence-system"
echo ""
echo "请输入您的Personal Access Token:"
read -rs GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Token不能为空"
    exit 1
fi

# 清理旧的remote
git remote remove origin 2>/dev/null || true

# 添加新的remote（带Token）
git remote add origin "https://tianh-ai:${GITHUB_TOKEN}@github.com/tianh-ai/bidding-intelligence-system.git"

echo "📤 正在推送代码..."
echo ""

# 推送
if git push -u origin main; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 上传成功！"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 访问您的项目:"
    echo "   https://github.com/tianh-ai/bidding-intelligence-system"
    echo ""
    echo "📝 后续操作:"
    echo "   1. 添加项目描述和Topics"
    echo "   2. 创建Release"
    echo ""
    echo "⚠️  如需添加GitHub Actions:"
    echo "   需要更新Token权限，添加 'workflow' scope"
    echo "   然后运行: git checkout .github/ && git add . && git commit && git push"
    echo ""
    
    # 清理Token
    git remote remove origin
    git remote add origin "https://github.com/tianh-ai/bidding-intelligence-system.git"
    echo "🔒 Token已清理"
else
    echo ""
    echo "❌ 推送失败"
    git remote remove origin
    git remote add origin "https://github.com/tianh-ai/bidding-intelligence-system.git"
    exit 1
fi
