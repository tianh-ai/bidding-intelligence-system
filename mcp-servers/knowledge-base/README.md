# Knowledge Base MCP 服务器

## 概述

知识库 MCP 服务器提供智能知识管理功能，支持**主程序调用**和 **AI 助手直接调用**两种模式。

### 架构设计

```
主程序调用链：
FastAPI (knowledge.py)
    ↓ HTTP API
MCP Client (mcp_client.py)
    ↓ JSON-RPC over stdio
MCP Server (TypeScript)
    ↓ exec() Python
Python Backend (knowledge_base.py)
    ↓ import
PostgreSQL Database
```

## 功能特性

### 6 大核心工具

1. **search_knowledge** - 知识库搜索
   - 支持模糊查询
   - 分类筛选
   - 重要性评分排序

2. **add_knowledge_entry** - 添加知识条目
   - 自动关键词提取
   - 重要性评分
   - 元数据支持

3. **get_knowledge_entry** - 获取条目详情
   - 关联文件信息
   - 完整元数据

4. **list_knowledge_entries** - 条目列表
   - 分页支持
   - 分类筛选
   - 文件筛选

5. **delete_knowledge_entry** - 删除条目
   - 安全删除
   - 审计日志

6. **get_knowledge_statistics** - 统计信息
   - 总数统计
   - 分类分布
   - 最近条目

## 安装配置

### 1. 安装依赖

```bash
cd mcp-servers/knowledge-base
./setup.sh
```

或手动安装：
```bash
npm install
npm run build
```

### 2. 数据库配置

确保主程序数据库已初始化（包含 `knowledge_base` 表）：

```sql
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    file_id INT REFERENCES uploaded_files(id),
    category VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    keywords TEXT[],
    importance_score FLOAT DEFAULT 0.0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_knowledge_base_file_id ON knowledge_base(file_id);
CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
```

## 使用方式

### 方式 1: 主程序调用（推荐）

通过 FastAPI HTTP API：

```bash
# 搜索知识
curl -X POST http://localhost:18888/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "投标要求",
    "category": "tender",
    "limit": 10,
    "min_score": 0.5
  }'

# 添加知识条目
curl -X POST http://localhost:18888/api/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 1,
    "category": "tender",
    "title": "投标保证金要求",
    "content": "投标保证金为项目总价的2%",
    "keywords": ["保证金", "投标"],
    "importance_score": 0.85
  }'

# 获取统计信息
curl http://localhost:18888/api/knowledge/statistics
```

### 方式 2: Python 代码调用

```python
from core.mcp_client import get_knowledge_base_client

async def my_function():
    client = get_knowledge_base_client()
    
    # 搜索知识
    results = await client.search_knowledge(
        query="投标要求",
        category="tender",
        limit=10
    )
    
    # 添加条目
    entry = await client.add_knowledge_entry(
        file_id=1,
        category="tender",
        title="项目要求",
        content="详细内容...",
        keywords=["投标", "要求"]
    )
    
    return results
```

### 方式 3: Claude Desktop 调用

配置 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "knowledge-base": {
      "command": "node",
      "args": ["/path/to/mcp-servers/knowledge-base/dist/index.js"]
    }
  }
}
```

在 Claude Desktop 中：
```
请搜索知识库中关于"投标资质"的内容
```

### 方式 4: Python CLI 测试

```bash
# 获取统计信息
python python/knowledge_base.py stats

# 搜索知识
python python/knowledge_base.py search --query "投标" --category tender

# 添加条目
python python/knowledge_base.py add \
  --file-id 1 \
  --category tender \
  --title "测试条目" \
  --content "测试内容" \
  --keywords "测试,知识库"

# 列出条目
python python/knowledge_base.py list --category tender --limit 5

# 获取详情
python python/knowledge_base.py get --id 1

# 删除条目
python python/knowledge_base.py delete --id 1
```

## API 端点

### HTTP API (主程序)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/knowledge/search` | 搜索知识 |
| POST | `/api/knowledge/entries` | 添加条目 |
| GET | `/api/knowledge/entries/{id}` | 获取详情 |
| POST | `/api/knowledge/entries/list` | 条目列表 |
| DELETE | `/api/knowledge/entries/{id}` | 删除条目 |
| GET | `/api/knowledge/statistics` | 统计信息 |
| GET | `/api/knowledge/health` | 健康检查 |

### MCP 工具 (AI 助手)

| 工具名称 | 输入参数 | 返回值 |
|---------|---------|--------|
| search_knowledge | query, category?, limit?, min_score? | List[Dict] |
| add_knowledge_entry | file_id, category, title, content, ... | Dict |
| get_knowledge_entry | entry_id | Dict |
| list_knowledge_entries | file_id?, category?, limit?, offset? | Dict |
| delete_knowledge_entry | entry_id | Dict |
| get_knowledge_statistics | - | Dict |

## 测试验证

### 1. 健康检查

```bash
curl http://localhost:18888/api/knowledge/health
```

预期响应：
```json
{
  "status": "healthy",
  "mcp_server": "knowledge-base",
  "timestamp": "2024-01-20T10:30:00"
}
```

### 2. Python 后端测试

```bash
cd mcp-servers/knowledge-base
python python/knowledge_base.py stats
```

### 3. MCP 客户端测试

```python
# 创建测试脚本
python backend/core/mcp_client.py
```

### 4. 集成测试

```bash
# 启动后端服务（Docker）
docker compose up -d backend

# 另一个终端测试 API
curl -X POST http://localhost:18888/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}'
```

## 目录结构

```
knowledge-base/
├── src/
│   └── index.ts          # MCP 服务器 (TypeScript)
├── python/
│   └── knowledge_base.py # Python 后端
├── test/
│   └── (测试文件)
├── dist/
│   └── index.js          # 编译后的 JS
├── package.json
├── tsconfig.json
├── setup.sh
└── README.md
```

## 技术栈

- **MCP 协议**: JSON-RPC 2.0 over stdio
- **TypeScript**: @modelcontextprotocol/sdk v1.0.0
- **Python**: asyncio + subprocess
- **数据库**: PostgreSQL
- **通信**: Node.js ↔ Python 子进程

## 常见问题

### Q: MCP 服务器启动失败
A: 确保已运行 `npm run build` 且 `dist/index.js` 存在

### Q: 数据库连接错误
A: 检查主程序的数据库配置和 `knowledge_base` 表是否存在

### Q: HTTP API 返回 500 错误
A: 查看日志 `backend/logs/`，检查 MCP 服务器是否正常运行

### Q: 性能优化建议
A: 
1. 使用 Redis 缓存热门查询
2. 为 `content` 字段创建全文索引
3. 实现向量搜索（embedding）

## 下一步优化

- [ ] 向量搜索（使用 OpenAI embeddings）
- [ ] 知识条目关联图谱
- [ ] 版本控制和历史记录
- [ ] 批量导入功能
- [ ] 智能标签推荐
- [ ] 知识评分系统

## 许可证

MIT License - 参见项目根目录 LICENSE 文件
