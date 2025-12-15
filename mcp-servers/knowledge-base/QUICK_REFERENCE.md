# Knowledge Base MCP 快速参考

## 🎯 核心特性

**主程序可调用的 MCP 服务器** - 与 document-parser 的关键区别

## 📦 安装

```bash
cd mcp-servers/knowledge-base
./setup.sh
```

## ✅ 验证

```bash
# 快速验证（推荐）
./quick_verify.sh

# 完整集成测试
./test/test_integration.sh
```

## 🔌 使用方式

### 方式 1: Python 代码调用（主程序）

```python
from core.mcp_client import get_knowledge_base_client

async def search():
    client = get_knowledge_base_client()
    results = await client.search_knowledge(
        query="投标要求",
        category="tender",
        limit=10
    )
    return results
```

### 方式 2: HTTP API 调用

```bash
# 搜索
curl -X POST http://localhost:18888/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "投标", "category": "tender"}'

# 统计
curl http://localhost:18888/api/knowledge/statistics

# 健康检查
curl http://localhost:18888/api/knowledge/health
```

### 方式 3: CLI 测试

```bash
cd mcp-servers/knowledge-base

# 搜索
python python/knowledge_base.py search --query "投标" --category tender

# 统计
python python/knowledge_base.py stats

# 添加
python python/knowledge_base.py add \
  --file-id 1 \
  --category tender \
  --title "测试" \
  --content "内容"
```

## 🛠️ 6 个核心工具

| 工具 | 功能 |
|------|------|
| `search_knowledge` | 搜索知识 |
| `add_knowledge_entry` | 添加条目 |
| `get_knowledge_entry` | 获取详情 |
| `list_knowledge_entries` | 条目列表 |
| `delete_knowledge_entry` | 删除条目 |
| `get_knowledge_statistics` | 统计信息 |

## 🌐 7 个 HTTP 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge/search` | 搜索 |
| POST | `/api/knowledge/entries` | 添加 |
| GET | `/api/knowledge/entries/{id}` | 获取 |
| POST | `/api/knowledge/entries/list` | 列表 |
| DELETE | `/api/knowledge/entries/{id}` | 删除 |
| GET | `/api/knowledge/statistics` | 统计 |
| GET | `/api/knowledge/health` | 健康检查 |

## 🏗️ 架构

```
FastAPI → MCP Client → MCP Server → Python Backend → Database
```

## 📁 核心文件

- `python/knowledge_base.py` - Python 后端
- `src/index.ts` - MCP 服务器
- `backend/core/mcp_client.py` - **MCP 客户端（关键桥接层）**
- `backend/routers/knowledge.py` - HTTP API

## 🔍 故障排查

```bash
# 1. 检查构建
ls dist/index.js

# 2. 测试 Python 后端
python python/knowledge_base.py stats

# 3. 检查后端服务
curl http://localhost:18888/health

# 4. 查看日志
tail -f ../../backend/logs/app.log
```

## 📚 文档

- `README.md` - 完整文档
- `KNOWLEDGE_BASE_MCP_COMPLETE.md` - 实现报告
- `mcp-servers/README.md` - MCP 服务器索引

## 🚀 下一步

1. 运行 `./setup.sh` 构建
2. 运行 `./quick_verify.sh` 验证
3. 启动 Docker 服务测试 API（`docker compose up -d`）
4. Git 提交

---

**需要帮助？** 查看 `README.md` 或运行测试脚本
