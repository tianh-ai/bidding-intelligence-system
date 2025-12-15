#!/bin/bash
# ⚠️ 本项目强制使用 Docker 运行。
# 为避免误操作（把端口/配置改回旧值），本地启动脚本已禁用。

set -e

echo "❌ 已禁用本地启动（必须使用 Docker）。"
echo "   启动：docker compose up -d"
echo "   访问：前端 http://localhost:13000  后端 http://localhost:18888"
exit 1
