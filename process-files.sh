#!/bin/bash

# 自动处理已上传文件的脚本

API_URL="http://localhost:18888"

echo "========== 获取待处理文件 =========="
PENDING=$(curl -s "$API_URL/api/pending-files" | jq '.files')
echo "$PENDING" | jq '.'

if [ "$(echo "$PENDING" | jq 'length')" -eq 0 ]; then
  echo "✅ 没有待处理文件"
  exit 0
fi

echo ""
echo "========== 获取文件ID =========="
FILE_IDS=$(echo "$PENDING" | jq -r '.[].id' | jq -R -s -c 'split("\n")[:-1] | map({file_id: .})')
echo "处理中的文件IDs: $FILE_IDS"

echo ""
echo "========== 触发文件处理 =========="
RESULT=$(curl -X POST \
  -H "Content-Type: application/json" \
  -d "{\"file_ids\": $(echo "$PENDING" | jq '[.[].id]')}" \
  "$API_URL/api/process-files")

echo "$RESULT" | jq '.'

echo ""
echo "========== 验证结果 =========="

# 获取统计信息
echo "文件统计信息:"
curl -s "$API_URL/api/files/stats" | jq '{total_files, total_size, by_status}'

echo ""
echo "知识库条目数:"
curl -s "$API_URL/api/files/knowledge-base-entries" | jq 'length'

echo ""
echo "文档索引数:"
curl -s "$API_URL/api/files/document-indexes" | jq 'length'

echo ""
echo "✅ 处理完成！请访问 http://localhost:13000 查看结果"
