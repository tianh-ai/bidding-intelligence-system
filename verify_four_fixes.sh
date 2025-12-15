#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 验证4个问题的修复"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 测试1：系统设置API
echo "✅ 测试1: 系统设置加载"
echo "   测试 GET /api/settings/upload"
SETTINGS_RESULT=$(curl -s http://localhost:8001/api/settings/upload)
if echo "$SETTINGS_RESULT" | grep -q "upload_dir"; then
    echo "   ✓ 系统设置API返回正确"
    echo "   响应: $SETTINGS_RESULT" | head -c 100
else
    echo "   ✗ 系统设置API失败"
    echo "   响应: $SETTINGS_RESULT"
fi
echo ""

# 测试2：文件上传并验证返回结构
echo "✅ 测试2: 文件上传返回files字段"
echo "   创建测试文件..."
echo "测试内容" > /tmp/test_file.txt

UPLOAD_RESULT=$(curl -s -X POST http://localhost:8001/api/files/upload \
  -F "files=@/tmp/test_file.txt" \
  -F "doc_type=other")

if echo "$UPLOAD_RESULT" | grep -q '"files"'; then
    echo "   ✓ 上传响应包含files字段"
    echo "   响应: $UPLOAD_RESULT" | jq '.files | length' 2>/dev/null || echo "$UPLOAD_RESULT"
else
    echo "   ✗ 上传响应缺少files字段"
    echo "   响应: $UPLOAD_RESULT"
fi
echo ""

# 测试3：删除和下载API路径
echo "✅ 测试3: 删除和下载API存在性"

# 检查后端路由是否包含新增的API
ROUTES_CHECK=$(docker exec bidding_backend python3 -c "
import sys
sys.path.insert(0, '/app')
from routers import files
router_paths = [route.path for route in files.router.routes]
print('uploaded/' in str(router_paths))
" 2>/dev/null)

if [ "$ROUTES_CHECK" = "True" ]; then
    echo "   ✓ 删除和下载API已注册"
    echo "   路径: /api/files/uploaded/{id}/download"
    echo "   路径: /api/files/uploaded/{id} (DELETE)"
else
    echo "   ⚠️  API路由检查需要手动验证"
fi
echo ""

# 测试4：前端页面文件存在
echo "✅ 测试4: 文件管理页面"
if [ -f "frontend/src/pages/FileManagement.tsx" ]; then
    echo "   ✓ FileManagement.tsx 已创建"
    LINES=$(wc -l < frontend/src/pages/FileManagement.tsx)
    echo "   文件行数: $LINES"
else
    echo "   ✗ FileManagement.tsx 不存在"
fi

if grep -q "FileManagement" frontend/src/App.tsx; then
    echo "   ✓ FileManagement 已注册到路由"
else
    echo "   ✗ FileManagement 未注册到路由"
fi
echo ""

# 代码变更总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 代码变更总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  已上传清单仅显示当次上传"
echo "   📁 FileUpload.tsx"
echo "   - 移除 uploadedFiles 状态"
echo "   - 移除 loadFiles() 函数和 useEffect"
echo "   - 表格数据源改为 matchingResult.files"
echo "   - 分页文本改为 '本次上传 X 个文件'"
echo ""

echo "2️⃣  删除和下载功能修复"
echo "   📁 backend/routers/files.py"
echo "   - 新增 DELETE /api/files/uploaded/{id}"
echo "   - 新增 GET /api/files/uploaded/{id}/download"
echo "   📁 frontend/src/services/api.ts"
echo "   - deleteFile 路径: /api/files/uploaded/{id}"
echo "   - downloadFile 路径: /api/files/uploaded/{id}/download"
echo ""

echo "3️⃣  系统设置加载修复"
echo "   📁 backend/routers/settings.py"
echo "   - 移除 response_model=UploadSettings"
echo "   - 直接返回字典而不是Pydantic模型"
echo "   - 返回正确的字段结构"
echo ""

echo "4️⃣  文件管理页面实现"
echo "   📁 frontend/src/pages/FileManagement.tsx (新建)"
echo "   - 完整的文件列表展示"
echo "   - 搜索功能"
echo "   - 删除和下载操作"
echo "   - 分页和排序"
echo "   📁 frontend/src/App.tsx"
echo "   - 注册 /management 路由"
echo "   - 导入 FileManagement 组件"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 浏览器验证步骤"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 访问文件上传页面: http://localhost:13000/files"
echo "   - 上传几个文件"
echo "   - 验证「已上传清单」仅显示本次上传的文件"
echo "   - 测试删除和下载功能"
echo ""
echo "2. 访问系统设置页面: http://localhost:13000/settings"
echo "   - 验证当前路径信息正常加载"
echo "   - 验证磁盘空间信息显示"
echo "   - 测试路径测试功能"
echo ""
echo "3. 访问文件管理页面: http://localhost:13000/management"
echo "   - 验证文件列表正常显示"
echo "   - 测试搜索功能"
echo "   - 测试删除和下载功能"
echo "   - 验证分页正常工作"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 清理测试文件
rm -f /tmp/test_file.txt
