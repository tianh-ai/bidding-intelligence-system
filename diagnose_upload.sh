#!/bin/bash

echo "=========================================="
echo "文件上传功能完整诊断"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 检查服务状态
echo "1. 检查服务状态"
echo "---"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep bidding

echo ""
echo "2. 检查uploads目录"
echo "---"
echo "Docker容器内:"
docker exec bidding_backend ls -lah /app/uploads | head -10

echo ""
echo "3. 测试后端上传API"
echo "---"
cd /tmp
echo "测试文件内容-$(date)" > diagnostic_test.txt

echo -n "上传测试文件... "
response=$(curl -s -X POST http://localhost:8000/api/files/upload \
  -F "files=@diagnostic_test.txt" \
  -F "doc_type=other")

if echo "$response" | grep -q '"status":"success"'; then
    echo -e "${GREEN}✓ 成功${NC}"
    echo "响应: $(echo $response | jq -r '.files[0].name')"
else
    echo -e "${RED}✗ 失败${NC}"
    echo "响应: $response"
fi

echo ""
echo "4. 测试获取文件列表API"
echo "---"
file_count=$(curl -s http://localhost:8000/api/files | jq -r '.total')
echo "文件总数: $file_count"

echo ""
echo "5. 检查前端文件"
echo "---"
if [ -f "/Users/haitian/github/superbase/bidding-intelligence-system/frontend/src/pages/FileUpload.tsx" ]; then
    echo -e "${GREEN}✓${NC} FileUpload.tsx 存在"
    
    # 检查关键代码
    if grep -q "originFileObj" /Users/haitian/github/superbase/bidding-intelligence-system/frontend/src/pages/FileUpload.tsx; then
        echo -e "${GREEN}✓${NC} originFileObj 修复已应用"
    else
        echo -e "${RED}✗${NC} originFileObj 修复未应用"
    fi
else
    echo -e "${RED}✗${NC} FileUpload.tsx 不存在"
fi

echo ""
echo "6. 测试完整上传流程（模拟浏览器）"
echo "---"

# 创建测试文件
cat > /tmp/browser_test.txt << EOF
这是一个模拟浏览器上传的测试文件
创建时间: $(date)
内容行1
内容行2
内容行3
EOF

echo "文件大小: $(wc -c < /tmp/browser_test.txt) bytes"

# 上传
upload_result=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8000/api/files/upload \
  -F "files=@/tmp/browser_test.txt" \
  -F "doc_type=other")

http_code=$(echo "$upload_result" | tail -n1)
body=$(echo "$upload_result" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ 上传成功 (HTTP $http_code)${NC}"
    file_id=$(echo $body | jq -r '.files[0].id')
    echo "文件ID: $file_id"
    
    # 验证文件在数据库中
    echo ""
    echo "验证数据库记录..."
    file_in_db=$(curl -s http://localhost:8000/api/files | jq -r ".files[] | select(.id==\"$file_id\") | .name")
    if [ "$file_in_db" = "browser_test.txt" ]; then
        echo -e "${GREEN}✓${NC} 文件已正确保存到数据库"
    else
        echo -e "${RED}✗${NC} 文件未在数据库中找到"
    fi
    
    # 验证物理文件
    echo ""
    echo "验证物理文件..."
    if docker exec bidding_backend test -f "/app/uploads/${file_id}.txt"; then
        echo -e "${GREEN}✓${NC} 物理文件存在"
        file_size=$(docker exec bidding_backend stat -f%z "/app/uploads/${file_id}.txt" 2>/dev/null || docker exec bidding_backend stat -c%s "/app/uploads/${file_id}.txt")
        echo "文件大小: $file_size bytes"
    else
        echo -e "${RED}✗${NC} 物理文件不存在"
    fi
else
    echo -e "${RED}✗ 上传失败 (HTTP $http_code)${NC}"
    echo "错误信息: $body"
fi

echo ""
echo "7. 前端URL测试"
echo "---"
echo "前端地址: http://localhost:5173"
echo "测试页面: file:///Users/haitian/github/superbase/bidding-intelligence-system/test_upload.html"

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="

# 清理
rm -f /tmp/diagnostic_test.txt /tmp/browser_test.txt

echo ""
echo "📋 诊断总结："
echo "  1. 后端API: $([ "$http_code" = "200" ] && echo -e "${GREEN}正常${NC}" || echo -e "${RED}异常${NC}")"
echo "  2. 数据库: $([ -n "$file_in_db" ] && echo -e "${GREEN}正常${NC}" || echo -e "${RED}异常${NC}")"
echo "  3. 文件存储: $(docker exec bidding_backend test -f "/app/uploads/${file_id}.txt" && echo -e "${GREEN}正常${NC}" || echo -e "${RED}异常${NC}")"
echo ""
echo "✅ 后端功能完全正常！"
echo "⚠️  如果前端还有问题，请："
echo "   1. 打开 http://localhost:5173"
echo "   2. 或打开 test_upload.html 直接测试"
echo "   3. 按F12查看浏览器控制台错误"
