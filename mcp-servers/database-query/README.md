# Database Query MCP Server

**用途**: 为外部程序提供标准化的数据库访问接口

## 为什么需要数据库MCP

### ✅ 优势

1. **统一接口**: 其他程序不需要知道数据库连接细节
2. **权限控制**: 可以限制访问范围，只暴露必要的查询
3. **路径自动转换**: 可以处理容器路径与宿主机路径的转换
4. **类型安全**: 返回标准化的JSON数据，避免SQL注入
5. **解耦设计**: 数据库结构变化时，MCP接口保持稳定

### 🎯 适用场景

**推荐使用MCP**:
- ✅ 外部AI Agent查询文件信息
- ✅ 第三方应用集成
- ✅ 跨语言程序访问（Python/Node.js/其他）
- ✅ Claude Desktop等AI工具调用
- ✅ 需要路径转换的场景

**直接连接数据库**:
- 后端API内部查询（已在Docker网络内）
- 数据库管理工具（pgAdmin, DBeaver等）
- 数据分析脚本（需要复杂SQL）

## 核心功能设计

### 工具1: 查询文件信息
```json
{
  "name": "query_file_by_id",
  "description": "根据文件ID查询文件信息，自动转换路径",
  "inputSchema": {
    "file_id": "uuid",
    "return_host_path": "boolean"  // 是否返回宿主机路径
  }
}
```

### 工具2: 搜索文件
```json
{
  "name": "search_files",
  "description": "根据条件搜索文件",
  "inputSchema": {
    "filename": "string",
    "category": "string",
    "date_from": "date",
    "date_to": "date",
    "limit": "number"
  }
}
```

### 工具3: 获取文件统计
```json
{
  "name": "get_file_stats",
  "description": "获取文件统计信息"
}
```

## 路径转换策略

### 自动路径映射

```python
class PathMapper:
    CONTAINER_PREFIX = "/app/data"
    HOST_PREFIX = "/Volumes/ssd/bidding-data"
    
    @staticmethod
    def to_host_path(container_path: str) -> str:
        """容器路径 → 宿主机路径（用于外部程序访问）"""
        return container_path.replace(
            PathMapper.CONTAINER_PREFIX, 
            PathMapper.HOST_PREFIX
        )
    
    @staticmethod
    def to_container_path(host_path: str) -> str:
        """宿主机路径 → 容器路径（用于存储）"""
        return host_path.replace(
            PathMapper.HOST_PREFIX,
            PathMapper.CONTAINER_PREFIX
        )
```

### 使用示例

**场景1: 外部程序需要读取文件**
```python
# MCP调用
result = mcp.query_file_by_id(
    file_id="c230a55a-1180-4175-9b1b-46b622123090",
    return_host_path=True  # 返回宿主机路径
)

# 返回
{
    "id": "c230a55a-1180-4175-9b1b-46b622123090",
    "filename": "投标文件.docx",
    "archive_path": "/Volumes/ssd/bidding-data/archive/2025/12/proposal/...",
    "size_mb": 0.02,
    "created_at": "2025-12-14T12:37:00Z"
}

# 外部程序直接访问
with open(result["archive_path"], 'rb') as f:
    content = f.read()
```

**场景2: 搜索最近上传的文件**
```python
files = mcp.search_files(
    category="proposal",
    date_from="2025-12-01",
    limit=10,
    return_host_path=True
)

for file in files:
    process_file(file["archive_path"])
```

## 实现优先级

### 阶段1: 基础查询 (立即实现)
- [x] 数据库路径标准化完成
- [ ] 创建MCP服务器框架
- [ ] 实现 `query_file_by_id`
- [ ] 实现路径自动转换

### 阶段2: 高级功能 (按需实现)
- [ ] `search_files` 多条件搜索
- [ ] `get_file_stats` 统计信息
- [ ] 文件元数据提取
- [ ] 知识库查询集成

### 阶段3: 安全增强 (生产环境)
- [ ] API密钥认证
- [ ] 查询速率限制
- [ ] SQL注入防护
- [ ] 审计日志

## 配置示例

**MCP服务器配置** (`mcp-servers/database-query/config.json`):
```json
{
  "server_name": "bidding-database",
  "database": {
    "host": "localhost",
    "port": 5433,
    "database": "bidding_db",
    "user": "postgres",
    "password": "${DB_PASSWORD}"
  },
  "path_mapping": {
    "container_prefix": "/app/data",
    "host_prefix": "/Volumes/ssd/bidding-data"
  },
  "security": {
    "read_only": true,
    "allowed_tables": ["uploaded_files", "knowledge_base"],
    "max_results": 100
  }
}
```

## 与现有MCP的协作

```
数据库MCP          document-parser MCP
    ↓                      ↓
1. 查询文件信息     →  2. 获取文件路径
3. 返回路径         →  4. 解析文档内容
                        5. 返回解析结果
```

**示例流程**:
```python
# 步骤1: 通过数据库MCP查询文件
file_info = database_mcp.query_file_by_id(file_id)

# 步骤2: 使用document-parser MCP解析
parsed = document_parser_mcp.parse(
    file_path=file_info["archive_path"]
)

# 步骤3: 处理结果
print(f"文件: {file_info['filename']}")
print(f"段落数: {len(parsed['paragraphs'])}")
```

## 决策建议

### 立即创建数据库MCP的理由

1. **标准化访问**: 统一的接口比直接SQL更可维护
2. **路径透明**: 自动处理容器/宿主机路径转换
3. **未来扩展**: 为多个外部程序提供服务
4. **安全性**: 限制访问范围，只读操作
5. **AI友好**: Claude Desktop可直接调用

### 实施时间

- **现在**: 创建基础框架和核心查询
- **下周**: 根据实际使用情况添加功能
- **持续**: 优化性能和安全性

---

**下一步**: 是否立即创建数据库MCP服务器？
