# MCP Servers

本目录包含项目的所有 **Model Context Protocol (MCP)** 服务器实现。

## 📁 目录结构

```
mcp-servers/
├── README.md              # 本文件
├── database-query/        # 数据库查询 MCP 服务器 (NEW!)
│   ├── python/            # Python 实现
│   ├── package.json       # MCP 配置
│   └── README.md          # 详细文档
├── document-parser/       # 文档解析 MCP 服务器
│   ├── src/               # TypeScript 源码
│   ├── python/            # Python 后端
│   ├── test/              # 测试套件
│   └── README.md          # 详细文档
├── knowledge-base/        # 知识库 MCP 服务器
│   ├── src/               # TypeScript 源码
│   ├── python/            # Python 后端
│   ├── test/              # 测试套件
│   └── README.md          # 详细文档
├── logic-learning/        # 逻辑学习 MCP 服务器
└── logic-checking/        # 逻辑检查 MCP 服务器
```

## 🚀 可用的 MCP 服务器

### 1. Database Query (NEW! 🎉)

**路径**: `database-query/`  
**功能**: 标准化数据库查询接口，支持路径自动转换  
**工具数量**: 4 个  
**调用方式**: AI 助手直接调用（独立运行）

#### 核心功能
- ✅ `query_file_by_id` - 根据UUID查询文件信息
- ✅ `search_files` - 多条件搜索文件（文件名、分类、类型、日期）
- ✅ `get_file_stats` - 统计信息（总数、大小、分类统计）
- ✅ `list_recent_files` - 最近上传文件列表

#### 特色功能
- 🔄 **路径自动转换**: 容器路径 ↔ 宿主机路径智能转换
- 🐳 **Docker兼容**: 完美支持Docker挂载环境
- 📊 **丰富查询**: 支持日期范围、文件类型、分类过滤

#### 快速启动
```bash
cd database-query
python3 python/test_database_query.py
```

详细文档: [database-query/README.md](./database-query/README.md)

---

```json
{
  "mcpServers": {
    "database-query": {
      "command": "python3",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/database-query/python/database_query.py"
      ],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5433",
        "DB_NAME": "bidding_db",
        "DB_USER": "postgres",
        "DB_PASSWORD": "postgres123"
      }
    },
    "document-parser": {
      "command": "node",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/document-parser/dist/index.js"
      ]
    },
    "knowledge-base": {
      "command": "node",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/knowledge-base/dist/index.js"
      ]
    }
  }
}
```etup.sh

# 启用OCR
python python/document_parser.py parse file.pdf --ocr
```

详细文档: [document-parser/README.md](./document-parser/README.md)

---

### 3. Knowledge Base
### Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "document-parser": {
      "command": "node",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/document-parser/dist/index.js"
      ]
    },
    "knowledge-base": {
      "command": "node",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/knowledge-base/dist/index.js"
      ]
    }
  }
}
```python
from core.mcp_client import get_knowledge_base_client

async def search():
    client = get_knowledge_base_client()
    results = await client.search_knowledge(
        query="投标要求",
        category="tender"
    )
    return results
```

#### HTTP API 端点
```bash
# 搜索知识
curl -X POST http://localhost:18888/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "投标", "category": "tender"}'

# 获取统计
curl http://localhost:18888/api/knowledge/statistics
```

#### 快速启动
```bash
cd knowledge-base
./setup.sh

# 测试集成
chmod +x test/test_integration.sh
./test/test_integration.sh
```

详细文档: [knowledge-base/README.md](./knowledge-base/README.md)

---

## 🔧 通用配置

### Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "document-parser": {
      "command": "node",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/document-parser/dist/index.js"
### VS Code 配置

在项目根目录的 `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "document-parser": {
      "command": "node",
      "args": ["./mcp-servers/document-parser/dist/index.js"]
    },
    "knowledge-base": {
      "command": "node",
      "args": ["./mcp-servers/knowledge-base/dist/index.js"]
    }
  }
}
``` "document-parser": {
      "command": "node",
      "args": ["./mcp-servers/document-parser/dist/index.js"]
    }
  }
}
```

---

## 📚 MCP 协议

所有服务器遵循 [Model Context Protocol](https://modelcontextprotocol.io/) 标准：

- **Transport**: stdio (标准输入/输出)
- **Schema**: JSON Schema 参数验证
- **Tools**: 标准化工具定义
- **Errors**: 统一错误处理

---

## 🛠️ 开发指南

### 添加新 MCP 服务器

1. **创建目录**
   ```bash
   cd mcp-servers
   mkdir my-new-server
   ```

2. **基本结构**
   ```
   my-new-server/
   ├── package.json
   ├── tsconfig.json
   ├── src/
   │   └── index.ts
   ├── python/           # 可选：Python 后端
   │   └── backend.py
   └── README.md
   ```

3. **实现 MCP 协议**
   ```typescript
   import { Server } from '@modelcontextprotocol/sdk/server/index.js';
   import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
   
   const server = new Server({
     name: 'my-server',
     version: '1.0.0'
   }, { capabilities: { tools: {} } });
   
   // 定义工具...
   ```

4. **更新本 README**
   - 添加服务器到列表
   - 更新配置示例

---

## 🧪 测试

### 测试单个服务器
```bash
cd document-parser
python test/test_parser.py
```

### 测试所有服务器
```bash
# 从项目根目录
cd mcp-servers
for dir in */; do
  if [ -d "$dir/test" ]; then
    echo "Testing $dir..."
    cd "$dir" && python test/*.py && cd ..
  fi
done
```

---

## 📖 相关文档

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [主项目 README](../README.md)
- [MCP_PARSER_SETUP.md](../MCP_PARSER_SETUP.md) - Document Parser 设置指南

---

## ⚙️ 技术栈

| 组件 | 技术 |
|------|------|
| **协议** | Model Context Protocol (MCP) |
| **前端** | TypeScript + Node.js |
| **后端** | Python 3.12+ |
| **通信** | stdio / WebSocket |
| **验证** | JSON Schema |

---

## 📋 MCP服务器清单

| 服务器 | 状态 | 工具数 | 语言 | 用途 |
|--------|------|--------|------|------|
| database-query | ✅ 生产 | 4 | Python | 数据库查询 + 路径转换 |
| document-parser | ✅ 生产 | 4 | TS/Python | 文档解析 + OCR |
| knowledge-base | ✅ 生产 | 6 | TS/Python | 知识库管理 |
| logic-learning | ✅ 生产 | 5 | TS/Python | 逻辑学习 |
| logic-checking | ✅ 生产 | 3 | TS/Python | 逻辑检查 |

**总计**: 5个MCP服务器, 22个工具

---

**最后更新**: 2025-12-16  
**维护者**: bidding-intelligence-system 团队
