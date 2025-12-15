#!/bin/bash
# 
# 代码保护 Pre-commit Hook
# 防止意外修改已验证的关键文件
#
# 安装方法：
#   cp scripts/pre-commit-protection.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#

echo "🔒 运行代码保护检查..."

# 定义受保护的文件
PROTECTED_FILES=(
  "frontend/src/pages/FileUpload.tsx"
  "frontend/src/services/api.ts"
  "backend/routers/files.py"
  "backend/agents/preprocessor.py"
  "backend/engines/smart_router.py"
)

# 获取暂存的文件
STAGED_FILES=$(git diff --cached --name-only)

# 检查是否修改了受保护的文件
MODIFIED_PROTECTED=""
for file in "${PROTECTED_FILES[@]}"; do
  if echo "$STAGED_FILES" | grep -q "^$file$"; then
    MODIFIED_PROTECTED="$MODIFIED_PROTECTED\n  - $file"
  fi
done

if [ -n "$MODIFIED_PROTECTED" ]; then
  echo ""
  echo "⚠️  警告：检测到修改了受保护的文件！"
  echo ""
  echo "以下文件已经过验证并正常工作，请确认修改是必要的："
  echo -e "$MODIFIED_PROTECTED"
  echo ""
  echo "修改前请确保："
  echo "  1. 已阅读 CODE_PROTECTION.md"
  echo "  2. 创建了备份或新分支"
  echo "  3. 有明确的bug报告或需求"
  echo "  4. 准备了测试用例"
  echo ""
  echo "如果确认要提交这些修改，请运行："
  echo "  git commit --no-verify -m \"你的提交信息\""
  echo ""
  echo "如果要取消暂存，请运行："
  echo "  git reset HEAD <file>"
  echo ""
  
  # 询问是否继续
  read -p "是否继续提交？(y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 提交已取消"
    exit 1
  fi
  
  echo "✅ 继续提交（已确认）"
fi

# 检查是否修改了 FileUpload.tsx 中的注释掉的函数
if echo "$STAGED_FILES" | grep -q "^frontend/src/pages/FileUpload.tsx$"; then
  echo ""
  echo "🔍 检查 FileUpload.tsx 中的关键注释..."
  
  # 检查是否取消了 loadUploadedFiles 等函数的注释
  if git diff --cached frontend/src/pages/FileUpload.tsx | grep -E "^\+.*loadUploadedFiles\(\)" | grep -v "//"; then
    echo ""
    echo "❌ 错误：检测到取消了 loadUploadedFiles() 的注释！"
    echo ""
    echo "这会导致页面自动加载历史文件，违反了设计规范！"
    echo "详见：FRONTEND_BEHAVIOR.md"
    echo ""
    echo "请撤销这个修改："
    echo "  git checkout -- frontend/src/pages/FileUpload.tsx"
    echo ""
    exit 1
  fi
  
  if git diff --cached frontend/src/pages/FileUpload.tsx | grep -E "^\+.*loadDatabaseStats\(\)" | grep -v "//"; then
    echo ""
    echo "❌ 错误：检测到取消了 loadDatabaseStats() 的注释！"
    echo ""
    echo "这会导致页面自动加载数据，违反了设计规范！"
    echo "详见：FRONTEND_BEHAVIOR.md"
    echo ""
    exit 1
  fi
  
  echo "✓ 未检测到违规修改"
fi

echo ""
echo "✅ 代码保护检查通过"
echo ""
