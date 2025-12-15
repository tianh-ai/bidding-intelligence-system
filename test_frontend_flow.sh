#!/bin/bash
# 测试前端知识库和文档索引显示的完整流程

echo "======================================"
echo "前端知识库和文档索引显示测试"
echo "======================================"

cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system

# 1. 检查前端文件
echo ""
echo "1️⃣ 检查前端文件..."
if [ -f "frontend/src/pages/FileUpload.tsx" ]; then
    echo "✓ FileUpload.tsx 存在"
    
    # 检查关键导入
    if grep -q "knowledgeAPI" frontend/src/pages/FileUpload.tsx; then
        echo "✓ 已导入 knowledgeAPI"
    else
        echo "❌ 缺少 knowledgeAPI 导入"
    fi
    
    # 检查MCP调用
    if grep -q "knowledgeAPI.listEntries" frontend/src/pages/FileUpload.tsx; then
        echo "✓ 使用 MCP API (knowledgeAPI.listEntries)"
    else
        echo "❌ 未使用 MCP API"
    fi
else
    echo "❌ FileUpload.tsx 不存在"
fi

# 2. 检查API定义
echo ""
echo "2️⃣ 检查API定义..."
if [ -f "frontend/src/services/api.ts" ]; then
    if grep -q "export const knowledgeAPI" frontend/src/services/api.ts; then
        echo "✓ knowledgeAPI 已定义"
        
        # 检查listEntries方法
        if grep -q "listEntries:" frontend/src/services/api.ts; then
            echo "✓ listEntries 方法存在"
        else
            echo "❌ listEntries 方法缺失"
        fi
    else
        echo "❌ knowledgeAPI 未定义"
    fi
else
    echo "❌ api.ts 不存在"
fi

# 3. 检查后端API
echo ""
echo "3️⃣ 检查后端知识库API..."
if curl -s http://localhost:18888/api/knowledge/statistics > /dev/null 2>&1; then
    echo "✓ 后端知识库API可访问"
    
    # 获取统计信息
    stats=$(curl -s http://localhost:18888/api/knowledge/statistics)
    echo "   统计: $stats"
else
    echo "⚠ 后端API不可访问（可能未启动）"
fi

# 4. 检查重复文件处理
echo ""
echo "4️⃣ 检查重复文件处理逻辑..."
if grep -q "existing_size" backend/routers/files.py && \
   grep -q "existing_uploaded_at" backend/routers/files.py; then
    echo "✓ 后端返回完整的重复文件信息"
else
    echo "❌ 后端重复文件信息不完整"
fi

# 5. 检查前端构建
echo ""
echo "5️⃣ 检查前端编译状态..."
if [ -d "frontend/node_modules" ]; then
    echo "✓ node_modules 存在"
else
    echo "⚠ node_modules 不存在，需要运行: cd frontend && npm install"
fi

# 6. 显示测试建议
echo ""
echo "======================================"
echo "📋 测试建议："
echo "======================================"
echo ""
echo "1. 启动后端服务："
echo "   docker compose up -d backend"
echo ""
echo "2. 启动前端服务："
echo "   docker compose up -d frontend"
echo ""
echo "3. 浏览器访问："
echo "   http://localhost:13000"
echo ""
echo "4. 测试步骤："
echo "   a) 上传一个新文件"
echo "   b) 等待处理完成（右侧会显示文档目录和知识条目）"
echo "   c) 再次上传相同文件（测试重复文件显示）"
echo "   d) 检查左侧表格是否显示'重复文件'标签"
echo "   e) 检查右侧是否显示知识库条目（通过MCP）"
echo ""
echo "5. 查看控制台日志："
echo "   应该看到: '✓ 通过 MCP 加载了 X 条知识条目'"
echo "   应该看到: '✓ 总共加载了 Y 个文档的目录索引'"
echo ""
echo "======================================"
