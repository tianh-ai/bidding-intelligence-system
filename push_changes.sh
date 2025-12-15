#!/bin/bash
set -e

cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system

echo "=== 1. 检查状态 ==="
git status

echo -e "\n=== 2. 暂存所有改动 ==="
git add -A

echo -e "\n=== 3. 提交改动 ==="
git commit -m "chore: 更新配置文档和 Ollama 集成相关文件"

echo -e "\n=== 4. 推送到远程仓库 ==="
git push origin main

echo -e "\n✅ 推送完成"
git log -1 --oneline
