#!/bin/bash
#
# 快速验证脚本 - 一键检查整个系统状态
# 
# 使用方法：
#   ./scripts/quick_verify.sh
#

set -e  # 遇到错误立即退出

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 快速验证脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 检查代码是否被意外修改
echo "📝 1. 检查代码修改状态..."
echo ""

MODIFIED_FILES=$(git diff --name-only 2>/dev/null || echo "")

if [ -z "$MODIFIED_FILES" ]; then
  echo "✅ 没有未提交的修改"
else
  echo "⚠️  发现未提交的修改："
  echo "$MODIFIED_FILES" | sed 's/^/   /'
  echo ""
  
  # 检查是否修改了受保护的文件
  PROTECTED_MODIFIED=$(echo "$MODIFIED_FILES" | grep -E "(FileUpload.tsx|api.ts|files.py|preprocessor.py|smart_router.py)" || echo "")
  
  if [ -n "$PROTECTED_MODIFIED" ]; then
    echo "❌ 警告：修改了受保护的文件！"
    echo "$PROTECTED_MODIFIED" | sed 's/^/   /'
    echo ""
    echo "请运行以下命令查看详细修改："
    echo "  git diff"
    echo ""
    echo "如果修改不应该存在，请运行："
    echo "  git checkout -- <file>"
    echo ""
  fi
fi

# 2. 检查前端编译
echo "📦 2. 检查前端编译..."
echo ""

if [ -d "frontend" ]; then
  cd frontend
  
  # 检查 node_modules
  if [ ! -d "node_modules" ]; then
    echo "⚠️  node_modules 不存在，正在安装..."
    npm install
  else
    echo "✓ node_modules 存在"
  fi
  
  # 尝试编译
  echo "  正在编译..."
  if npm run build > /tmp/frontend_build.log 2>&1; then
    echo "✅ 前端编译成功"
  else
    echo "❌ 前端编译失败！"
    echo ""
    echo "错误日志："
    tail -20 /tmp/frontend_build.log | sed 's/^/  /'
    echo ""
    echo "完整日志: /tmp/frontend_build.log"
    exit 1
  fi
  
  cd ..
else
  echo "⚠️  frontend 目录不存在"
fi

echo ""

# 3. 检查后端服务
echo "🔧 3. 检查后端服务..."
echo ""

if curl -s http://localhost:18888/health > /dev/null 2>&1; then
  echo "✅ 后端服务运行正常"
  
  # 检查知识库API
  STATS=$(curl -s http://localhost:18888/api/knowledge/statistics 2>/dev/null || echo "{}")
  if [ "$STATS" != "{}" ]; then
    echo "✓ 知识库API响应正常"
    echo "  统计数据: $STATS"
  else
    echo "⚠️  知识库API无响应"
  fi
else
  echo "❌ 后端服务未运行！"
  echo ""
  echo "请启动后端服务："
  echo "  docker compose up -d backend"
  echo ""
fi

echo ""

# 4. 检查数据库
echo "🗄️  4. 检查数据库..."
echo ""

if command -v psql > /dev/null 2>&1; then
  # 检查数据库连接
  if psql -h localhost -p 5433 -U postgres -d bidding_db -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ 数据库连接正常"
    
    # 检查知识条目数量
    COUNT=$(psql -h localhost -p 5433 -U postgres -d bidding_db -t -c "SELECT COUNT(*) FROM knowledge_entries" 2>/dev/null | xargs || echo "0")
    echo "  知识条目数: $COUNT"
    
    if [ "$COUNT" -eq "0" ]; then
      echo "⚠️  数据库中没有知识条目"
      echo "  请上传文件并等待处理完成"
    fi
  else
    echo "❌ 数据库连接失败！"
    echo ""
    echo "请检查："
    echo "  1. PostgreSQL是否运行：pg_ctl status"
    echo "  2. 端口是否正确：5433"
    echo "  3. 数据库是否存在：psql -l | grep bidding_db"
    echo ""
  fi
else
  echo "⚠️  psql 命令不可用，跳过数据库检查"
fi

echo ""

# 5. 检查MCP服务器
echo "🔌 5. 检查MCP服务器..."
echo ""

MCP_SERVER="/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/knowledge-base/dist/index.js"

if [ -f "$MCP_SERVER" ]; then
  echo "✅ MCP服务器已构建"
  
  # 检查构建时间
  BUILD_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$MCP_SERVER" 2>/dev/null || stat -c "%y" "$MCP_SERVER" 2>/dev/null | cut -d' ' -f1-2)
  echo "  构建时间: $BUILD_TIME"
else
  echo "❌ MCP服务器未构建！"
  echo ""
  echo "请运行："
  echo "  cd mcp-servers/knowledge-base"
  echo "  npm install"
  echo "  npm run build"
  echo ""
fi

echo ""

# 6. 运行Python诊断脚本
echo "🔍 6. 运行完整诊断..."
echo ""

if [ -f "verify_knowledge_display.py" ]; then
  if command -v python3 > /dev/null 2>&1; then
    echo "  运行: python verify_knowledge_display.py"
    echo ""
    python3 verify_knowledge_display.py || echo "⚠️  诊断脚本执行失败（可能缺少依赖）"
  else
    echo "⚠️  Python3 不可用，跳过诊断脚本"
  fi
else
  echo "⚠️  诊断脚本不存在: verify_knowledge_display.py"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 验证完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 下一步操作："
echo ""
echo "  如果所有检查都通过："
echo "    1. 打开浏览器: http://localhost:13000"
echo "    2. 测试文件上传功能"
echo "    3. 检查知识库是否显示"
echo ""
echo "  如果有错误："
echo "    1. 查看上述错误信息"
echo "    2. 按照提示修复问题"
echo "    3. 重新运行此脚本验证"
echo ""
echo "  参考文档："
echo "    - CODE_PROTECTION.md - 代码保护规范"
echo "    - KNOWLEDGE_DISPLAY_DIAGNOSIS.md - 诊断报告"
echo "    - FRONTEND_BEHAVIOR.md - 前端行为规范"
echo ""
