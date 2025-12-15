# 前端知识库和文档索引显示 - 修复总结

## 已完成的修复

### 1. 后端修复 (backend/routers/files.py)
- ✅ 重复文件返回完整信息
  - `existing_size`: 文件大小
  - `existing_uploaded_at`: 上传时间
  - 两处duplicate_files.append都已修复

### 2. 前端修复 (frontend/src/pages/FileUpload.tsx)
- ✅ 导入 knowledgeAPI
- ✅ 使用 MCP API (`knowledgeAPI.listEntries`)
- ✅ 重复文件显示逻辑
  - 添加 size 和 uploadedAt 字段
  - 标记 isDuplicate: true
  - 显示"重复文件"标签
- ✅ loadKnowledgeEntriesForFiles 函数
  - 遍历每个文件ID
  - 调用 MCP API 获取知识条目
  - 合并所有结果
- ✅ loadSpecificDocumentIndexes 函数
  - 正确设置 documentIndexes 状态
  - 默认折叠所有文档
- ✅ 删除旧的 loadKnowledgeEntries 函数
- ✅ 删除重复的 console.log

### 3. API 定义 (frontend/src/services/api.ts)
- ✅ 新增 knowledgeAPI 对象
  - listEntries: 列出知识条目
  - search: 搜索知识
  - semanticSearch: 语义搜索
  - getStatistics: 获取统计信息

## 前端界面结构

```
FileUpload 页面
├── 左侧 (70%)
│   ├── 上传区域
│   │   ├── 拖拽上传框
│   │   ├── 开始上传按钮
│   │   └── 清空列表按钮
│   └── 已上传文件列表 (表格)
│       ├── 文件名 (带状态标签)
│       ├── 大小
│       ├── 上传时间
│       └── 操作 (下载/删除)
│
└── 右侧 (30%) - 可调整宽度
    ├── 存档统计卡片
    │   ├── 文件总数
    │   ├── 存储占用
    │   ├── 知识条目
    │   └── 最后更新
    │
    └── Tab 标签页
        ├── 文档目录索引 (indexes)
        │   └── 文档列表 (可折叠的树形结构)
        │       ├── 展开/折叠按钮
        │       ├── 全部展开/折叠
        │       ├── 查看按钮
        │       └── 删除按钮
        │
        └── 知识库条目 (knowledge)
            └── 条目列表
                ├── 标题
                ├── 类别标签
                ├── 来源文件
                ├── 创建时间
                └── 查看按钮
```

## 数据流程

### 上传流程
```
用户上传文件
  ↓
handleUpload()
  ↓
fileAPI.uploadFiles(formData)
  ↓
后端处理 (返回 uploaded + duplicates)
  ↓
前端处理结果
  ├── 新上传文件 → displayFiles
  └── 重复文件 → displayFiles (标记 isDuplicate)
  ↓
setUploadedFilesList(displayFiles)
  ↓
加载数据
  ├── loadDatabaseStats()
  ├── loadSpecificDocumentIndexes(allFileIds)
  └── loadKnowledgeEntriesForFiles(allFileIds)
  ↓
启动自动刷新 (setAutoRefresh(true))
```

### MCP 调用流程
```
loadKnowledgeEntriesForFiles(fileIds)
  ↓
遍历每个 fileId
  ↓
knowledgeAPI.listEntries({ file_id, limit: 100 })
  ↓
POST /api/knowledge/entries/list
  ↓
MCP Client (backend/core/mcp_client.py)
  ↓
MCP Server (mcp-servers/knowledge-base)
  ↓
Python Backend (knowledge_base.py)
  ↓
PostgreSQL (knowledge_entries 表)
  ↓
返回条目数组
  ↓
setKnowledgeEntries(allEntries)
```

## 测试步骤

### 1. 启动服务
```bash
# 后端
cd backend && python main.py

# 前端
cd frontend && npm run dev
```

### 2. 浏览器测试
1. 访问 http://localhost:5173
2. 登录系统
3. 进入"文件上传"页面

### 3. 测试新上传
1. 选择一个文件（如 proposal.docx）
2. 点击"开始上传"
3. 观察：
   - 左侧表格出现文件，状态从"解析中"→"已完成"
   - 右侧"存档统计"更新数字
   - 右侧"文档目录索引"显示章节树
   - 右侧"知识库条目"显示条目列表

### 4. 测试重复上传
1. 再次上传相同文件
2. 观察：
   - 弹出警告："文件已存在，已跳过"
   - 左侧表格出现该文件，带"重复文件"橙色标签
   - 文件大小和上传时间正确显示
   - 右侧数据正常显示（知识库条目和文档索引）

### 5. 检查控制台
应该看到以下日志：
```
✓ 通过 MCP 加载了 X 条知识条目
✓ 总共加载了 Y 个文档的目录索引
```

## 常见问题排查

### 问题1: 右侧不显示知识库条目
**可能原因:**
- 文件还没生成知识条目
- MCP 服务未启动
- 数据库中没有 knowledge_entries

**解决方案:**
```bash
# 触发知识提取
curl -X POST http://localhost:8000/api/files/{file_id}/extract-knowledge

# 或重建索引
curl -X POST http://localhost:8000/api/knowledge/reindex
```

### 问题2: 重复文件不显示
**检查清单:**
- ✓ 后端返回 existing_size 和 existing_uploaded_at
- ✓ 前端正确解析 duplicates 数组
- ✓ uploadedFilesList 包含重复文件

**调试:**
打开浏览器控制台，查看网络请求的响应数据

### 问题3: 文档目录为空
**可能原因:**
- documentIndexes 状态未设置
- loadSpecificDocumentIndexes 未调用
- 后端未返回章节数据

**调试:**
```javascript
// 浏览器控制台
console.log(documentIndexes)
```

## 物理存储位置

- **上传文件**: `data/uploads/`
- **归档文件**: `data/parsed/`
- **提取图片**: `data/images/`
- **知识条目**: PostgreSQL `knowledge_entries` 表
- **文档索引**: PostgreSQL `chapters` 表
- **向量数据**: PostgreSQL (pgvector 扩展)

## 验证 MCP 调用

### 方法1: 浏览器控制台
查找日志：`✓ 通过 MCP 加载了`

### 方法2: 后端日志
```bash
cd backend
tail -f logs/app.log | grep MCP
```

### 方法3: 直接测试 API
```bash
curl -X POST http://localhost:8000/api/knowledge/entries/list \
  -H 'Content-Type: application/json' \
  -d '{"file_id": "your-file-id", "limit": 10}'
```

## 完成状态

✅ 所有修复已完成
✅ 代码无语法错误
✅ 逻辑流程正确
✅ MCP 集成完整

请刷新浏览器测试！
