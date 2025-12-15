#!/bin/bash
set -e

cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system

echo "=== 1. 检查状态 ==="
git status

echo -e "\n=== 2. 暂存改动 ==="
git add backend/routers/llm.py
git add frontend/src/pages/LLMManagement.tsx
git add frontend/src/types/index.ts

echo -e "\n=== 3. 确认暂存 ==="
git status

echo -e "\n=== 4. 提交改动 ==="
git commit -m "feat(llm): 支持 Ollama 模型管理 + 优化添加模型体验

- 新增内置 Ollama 模型：千问3 8B (qwen3:8b)
- 前端支持 Ollama provider，自动填充 Docker 端点
- API Key 对 Ollama 改为可选
- 添加模型失败时显示后端具体错误 detail
- 修复表单提交无反应问题（显式触发 + 校验失败提示）
- 后端支持自定义模型持久化到 system_config
- chat/test 接口支持按 modelId 路由到自定义/Ollama 模型"

echo -e "\n=== 5. 验证提交 ==="
git log -1 --oneline

echo -e "\n✅ 提交完成"
