#!/bin/bash

echo "=== 1. 查找容器内的文件 ==="
docker exec bidding_backend find /Volumes/ssd/bidding-data -type f -name "*.docx" 2>/dev/null | head -20

echo ""
echo "=== 2. 查找容器内 /app 目录的文件 ==="
docker exec bidding_backend find /app -type f -name "*.docx" 2>/dev/null | head -20

echo ""
echo "=== 3. 查找宿主机 SSD 的文件 ==="
find /Volumes/ssd/bidding-data -type f -name "*.docx" 2>/dev/null | head -20

echo ""
echo "=== 4. 查找项目目录的文件 ==="
find /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend/uploads -type f -name "*.docx" 2>/dev/null | head -20

echo ""
echo "=== 5. 容器内所有 docx 文件 ==="
docker exec bidding_backend find / -type f -name "*.docx" 2>/dev/null | grep -v proc | head -20
