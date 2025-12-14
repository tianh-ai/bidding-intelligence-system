#!/bin/bash

# MCP 服务器快速提交脚本
# 用途: 一键将 MCP 服务器变更提交到 Git
# 作者: Copilot
# 日期: 2025-12-14

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 确保在项目根目录
cd "$(dirname "$0")"

print_header "MCP 服务器 Git 提交脚本"

# 1. 检查 Git 状态
print_info "检查 Git 状态..."
if ! git status &> /dev/null; then
    print_error "不是 Git 仓库！"
    exit 1
fi
print_success "Git 仓库正常"

# 2. 验证 MCP 目录结构
print_info "验证 MCP 目录结构..."
if [ ! -d "mcp-servers" ]; then
    print_error "mcp-servers/ 目录不存在！"
    exit 1
fi

if [ ! -f "mcp-servers/README.md" ]; then
    print_error "mcp-servers/README.md 不存在！"
    exit 1
fi

if [ ! -d "mcp-servers/document-parser" ]; then
    print_error "mcp-servers/document-parser/ 目录不存在！"
    exit 1
fi
print_success "MCP 目录结构验证通过"

# 3. 检查关键文件
print_info "检查关键文件..."
CRITICAL_FILES=(
    "mcp-servers/document-parser/src/index.ts"
    "mcp-servers/document-parser/python/document_parser.py"
    "mcp-servers/document-parser/test/test_parser.py"
    "mcp-servers/document-parser/package.json"
    "mcp-servers/document-parser/README.md"
    "MCP_PARSER_SETUP.md"
    "GIT_COMMIT_GUIDE_MCP.md"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "关键文件缺失: $file"
        exit 1
    fi
done
print_success "所有关键文件存在"

# 4. 检查敏感文件
print_info "检查敏感文件..."
SENSITIVE_PATTERNS=(
    "*.env"
    ".env.local"
    "backend/.env"
)

found_sensitive=0
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if git ls-files --error-unmatch "$pattern" &> /dev/null; then
        print_warning "发现敏感文件: $pattern"
        found_sensitive=1
    fi
done

if [ $found_sensitive -eq 1 ]; then
    print_error "请先移除敏感文件！"
    exit 1
fi
print_success "无敏感文件被追踪"

# 5. 显示待提交的文件
print_header "待提交的文件"
git status --short

# 6. 询问用户确认
echo ""
read -p "$(echo -e ${YELLOW}确认提交这些文件吗？ [y/N]: ${NC})" -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "已取消提交"
    exit 0
fi

# 7. 添加所有文件
print_info "添加文件到暂存区..."
git add .
print_success "文件已添加"

# 8. 提交
print_info "创建提交..."
git commit -m "feat(mcp): 添加 MCP 服务器模块化架构

主要变更:
- 重组 MCP 服务器到 mcp-servers/ 目录
- document-parser 提供文档解析能力（4个工具）
- 新增统一的 MCP 服务器索引和文档

架构优势:
✅ 统一管理所有 MCP 服务器
✅ 符合 Model Context Protocol 标准
✅ 便于集成到 Claude Desktop/VS Code
✅ 代码复用现有 backend/engines/

文档更新:
- README.md: 添加 MCP 集成章节
- mcp-servers/README.md: MCP 服务器索引
- MCP_PARSER_SETUP.md: 详细设置指南
- .gitignore: 添加 MCP 构建规则
- GIT_COMMIT_GUIDE_MCP.md: Git 提交指南
- MCP_MIGRATION_COMPLETE.md: 迁移完成总结
"

print_success "提交创建成功"

# 9. 询问是否推送
echo ""
read -p "$(echo -e ${YELLOW}是否推送到远程仓库？ [y/N]: ${NC})" -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "推送到远程..."
    
    # 获取当前分支
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    print_info "当前分支: $CURRENT_BRANCH"
    
    # 推送
    if git push origin "$CURRENT_BRANCH"; then
        print_success "推送成功！"
        
        # 显示仓库信息
        REMOTE_URL=$(git config --get remote.origin.url)
        print_info "远程仓库: $REMOTE_URL"
        
    else
        print_error "推送失败！请手动检查"
        exit 1
    fi
else
    print_warning "已跳过推送"
    print_info "稍后可以手动推送: git push origin main"
fi

# 10. 完成
print_header "完成"
print_success "MCP 服务器已成功提交到 Git！"

echo ""
print_info "下一步操作:"
echo "  1. 安装 MCP 服务器: cd mcp-servers/document-parser && ./setup.sh"
echo "  2. 测试 MCP 服务器: python test/test_parser.py"
echo "  3. 配置到 Claude Desktop: 见 mcp-config.example.json"
echo ""
print_info "详细文档:"
echo "  - MCP 设置指南: MCP_PARSER_SETUP.md"
echo "  - MCP 服务器索引: mcp-servers/README.md"
echo "  - 迁移总结: MCP_MIGRATION_COMPLETE.md"
echo ""

print_success "🎉 全部完成！"
