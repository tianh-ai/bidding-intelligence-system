#!/bin/bash

# 测试文件上传流程
echo "========================================="
echo "测试标书智能系统文件上传流程"
echo "========================================="
echo ""

# 1. 测试健康检查
echo "1. 测试后端健康状态..."
curl -s http://localhost:18888/health | python3 -m json.tool
echo ""

# 2. 登录获取token
echo "2. 登录获取token..."
TOKEN=$(curl -s -X POST http://localhost:18888/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"bidding2024"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

echo "Token获取成功: ${TOKEN:0:30}..."
echo ""

# 3. 上传测试文件
echo "3. 上传测试文档..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:18888/api/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@test_upload_doc.txt" \
  -F "uploader=admin" \
  -F "duplicate_action=skip")

echo "$UPLOAD_RESPONSE" | python3 -m json.tool
echo ""

# 提取文件ID
FILE_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['uploaded'][0]['id'] if data.get('uploaded') else 'NONE')")

if [ "$FILE_ID" != "NONE" ]; then
  echo "文件上传成功! ID: $FILE_ID"
  echo ""
  
  # 4. 等待后台处理
  echo "4. 等待后台处理（10秒）..."
  for i in {10..1}; do
    echo -ne "剩余 $i 秒...\r"
    sleep 1
  done
  echo ""
  echo ""
  
  # 5. 查询文件状态
  echo "5. 查询文件处理状态..."
  curl -s "http://localhost:18888/api/files/list?limit=1" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
  echo ""
  
  # 6. 查询知识库条目
  echo "6. 查询知识库条目..."
  curl -s "http://localhost:18888/api/files/knowledge-base?limit=5" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
  echo ""
  
  # 7. 查询数据库统计
  echo "7. 查询数据库统计..."
  curl -s "http://localhost:18888/api/files/database-details" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
  echo ""
  
else
  echo "❌ 文件上传失败"
fi

echo "========================================="
echo "测试完成"
echo "========================================="
