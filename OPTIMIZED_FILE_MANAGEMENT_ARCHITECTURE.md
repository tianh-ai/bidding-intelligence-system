# 优化的文件管理架构设计

## 当前架构的问题

### ❌ 现有流程缺陷

```
当前流程（有问题）:
用户上传 → 直接保存到 uploads/ → 后台解析 → 数据库
              ↓
         混乱的目录结构
         缺少状态追踪
         无法回滚错误
         没有文档分类
```

**主要问题**：
1. ❌ **目录混乱**：所有文件堆在一个 `uploads/` 目录
2. ❌ **缺少验证**：上传后直接保存，没有解析验证
3. ❌ **状态不明**：无法知道文件处于哪个处理阶段
4. ❌ **无法分类**：手动指定 `doc_type`，不智能
5. ❌ **难以管理**：解析失败的文件混在成功的文件中
6. ❌ **无法恢复**：出错后无法回到上一步

---

## ✅ 优化后的三阶段架构

### 核心理念：临时 → 解析 → 归档

```
┌─────────────────────────────────────────────────────────────┐
│                     文件生命周期管理                           │
└─────────────────────────────────────────────────────────────┘

阶段1: 临时存储（Temporary）
├─ uploads/temp/
│  ├─ {session_id}/{file_id}.ext       # 上传的原始文件
│  └─ 状态: UPLOADED                    # 刚上传，待解析
│
阶段2: 解析处理（Parsed）
├─ uploads/parsed/
│  ├─ {file_id}/
│  │  ├─ original.ext                  # 原始文件副本
│  │  ├─ metadata.json                 # 解析元数据
│  │  ├─ content.txt                   # 提取的文本
│  │  ├─ tables/                       # 提取的表格
│  │  │  ├─ table_1.csv
│  │  │  └─ table_2.csv
│  │  └─ images/                       # 提取的图片（可选）
│  └─ 状态: PARSED → VALIDATED → INDEXED
│
阶段3: 归档存储（Archived）
└─ uploads/archive/
   ├─ {year}/{month}/                  # 按时间归档
   │  └─ {category}/                   # 按类型分类
   │     ├─ tender/                    # 招标文件
   │     ├─ proposal/                  # 投标文件
   │     ├─ reference/                 # 参考资料
   │     └─ other/                     # 其他
   │        └─ {file_id}.ext
   └─ 状态: ARCHIVED

数据流向：
temp/ → parsed/ → archive/ → knowledge_base
  ↓        ↓         ↓            ↓
UPLOADED PARSED  ARCHIVED    INDEXED
```

---

## 文件状态机（State Machine）

### 状态定义

```python
class FileStatus(str, Enum):
    # 阶段1: 临时
    UPLOADED = "uploaded"           # 已上传到temp/
    UPLOAD_FAILED = "upload_failed" # 上传失败
    
    # 阶段2: 解析
    PARSING = "parsing"             # 正在解析
    PARSED = "parsed"               # 解析完成
    PARSE_FAILED = "parse_failed"   # 解析失败
    VALIDATING = "validating"       # 正在验证
    VALIDATED = "validated"         # 验证通过
    VALIDATION_FAILED = "validation_failed"  # 验证失败
    
    # 阶段3: 归档
    ARCHIVING = "archiving"         # 正在归档
    ARCHIVED = "archived"           # 已归档
    ARCHIVE_FAILED = "archive_failed"  # 归档失败
    
    # 阶段4: 索引
    INDEXING = "indexing"           # 正在建立索引
    INDEXED = "indexed"             # 已建立索引（最终状态）
    INDEX_FAILED = "index_failed"   # 索引失败
    
    # 特殊状态
    QUARANTINED = "quarantined"     # 隔离（病毒/损坏）
    DELETED = "deleted"             # 已删除（软删除）
```

### 状态转换图

```
UPLOADED ──parse──> PARSING ──success──> PARSED ──validate──> VALIDATING
   │                   │                     │                     │
   │                  fail                   │                   success
   │                   ↓                     │                     ↓
   └──────────> UPLOAD_FAILED         PARSE_FAILED         VALIDATED
                                                                  │
                                                              archive
                                                                  ↓
                                                              ARCHIVING
                                                                  │
                                                         success ↓  fail
                                                              ARCHIVED → ARCHIVE_FAILED
                                                                  │
                                                              index
                                                                  ↓
                                                              INDEXING
                                                                  │
                                                         success ↓  fail
                                                              INDEXED    INDEX_FAILED
                                                           (终态)
```

---

## 优化的处理流程

### 第一阶段：上传与临时存储

```python
# 1. 接收上传
POST /api/files/upload
├─ 创建 session_id
├─ 保存到 uploads/temp/{session_id}/{file_id}.ext
├─ 计算文件哈希（SHA256）
├─ 检查重复（基于哈希）
├─ 创建数据库记录
│  ├─ status: UPLOADED
│  ├─ temp_path: uploads/temp/...
│  └─ created_at: timestamp
└─ 返回 file_id 和 session_id

优点：
✓ 快速响应用户
✓ 不阻塞上传
✓ 支持批量上传（同一session）
✓ 可以在解析前预览文件列表
```

### 第二阶段：解析与验证

```python
# 2. 后台解析任务
@celery_app.task
def parse_uploaded_file(file_id: str):
    """
    解析临时文件并提取结构化信息
    """
    # 2.1 更新状态
    update_status(file_id, FileStatus.PARSING)
    
    # 2.2 加载临时文件
    temp_path = get_temp_path(file_id)
    
    # 2.3 创建解析目录
    parsed_dir = f"uploads/parsed/{file_id}/"
    os.makedirs(parsed_dir, exist_ok=True)
    
    # 2.4 执行解析
    try:
        parser = PreprocessorAgent()
        result = parser.parse(temp_path)
        
        # 2.5 保存解析结果
        save_parsed_results(parsed_dir, result):
            ├─ original.ext         # 复制原始文件
            ├─ metadata.json        # 解析元数据
            ├─ content.txt          # 纯文本内容
            ├─ tables/*.csv         # 表格数据
            └─ structure.json       # 章节结构
        
        # 2.6 更新数据库
        update_file_record(file_id, {
            "status": FileStatus.PARSED,
            "parsed_path": parsed_dir,
            "metadata": result.metadata,
            "parsed_at": datetime.now()
        })
        
        # 2.7 触发验证
        validate_parsed_file.delay(file_id)
        
    except Exception as e:
        update_status(file_id, FileStatus.PARSE_FAILED)
        save_error_log(file_id, str(e))
        # 保留temp文件供人工检查
```

### 第三阶段：智能分类与归档

```python
# 3. 文档分类引擎
class DocumentClassifier:
    """
    根据解析内容自动分类文档
    """
    
    def classify(self, metadata: dict, content: str) -> str:
        """
        分类策略：
        1. 关键词匹配
        2. 文档结构分析
        3. LLM语义理解（可选）
        """
        
        # 3.1 关键词规则
        if any(kw in content for kw in ["招标", "投标须知", "评分标准"]):
            return "tender"
        
        if any(kw in content for kw in ["投标文件", "技术方案", "商务报价"]):
            return "proposal"
        
        # 3.2 结构特征
        if has_bid_form_structure(metadata):
            return "tender"
        
        # 3.3 LLM分类（精确但慢）
        if use_llm_classification:
            return llm_classify(content[:2000])  # 只用前2000字
        
        return "other"
    
    def generate_filename(self, metadata: dict, category: str) -> str:
        """
        根据内容生成语义化文件名
        
        示例:
        - 原始: document_20231201.pdf
        - 生成: 2023年某某项目招标文件_技术部分.pdf
        """
        project_name = extract_project_name(metadata)
        doc_type = extract_doc_type(metadata)
        date = metadata.get("date", "")
        
        return f"{date}_{project_name}_{doc_type}.{metadata['ext']}"

# 4. 归档任务
@celery_app.task
def archive_file(file_id: str):
    update_status(file_id, FileStatus.ARCHIVING)
    
    # 4.1 加载解析结果
    parsed_dir = f"uploads/parsed/{file_id}/"
    metadata = load_json(f"{parsed_dir}/metadata.json")
    content = read_file(f"{parsed_dir}/content.txt")
    
    # 4.2 分类
    classifier = DocumentClassifier()
    category = classifier.classify(metadata, content)
    new_filename = classifier.generate_filename(metadata, category)
    
    # 4.3 生成归档路径
    year = datetime.now().year
    month = datetime.now().month
    archive_path = f"uploads/archive/{year}/{month:02d}/{category}/{new_filename}"
    
    # 4.4 移动文件
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    shutil.copy(f"{parsed_dir}/original.ext", archive_path)
    
    # 4.5 更新数据库
    update_file_record(file_id, {
        "status": FileStatus.ARCHIVED,
        "archive_path": archive_path,
        "category": category,
        "semantic_filename": new_filename,
        "archived_at": datetime.now()
    })
    
    # 4.6 触发知识库索引
    index_to_knowledge_base.delay(file_id)
```

### 第四阶段：知识库索引

```python
# 5. 知识库索引
@celery_app.task
def index_to_knowledge_base(file_id: str):
    update_status(file_id, FileStatus.INDEXING)
    
    # 5.1 加载解析数据
    parsed_dir = f"uploads/parsed/{file_id}/"
    structure = load_json(f"{parsed_dir}/structure.json")
    
    # 5.2 分章节索引
    for chapter in structure["chapters"]:
        # 生成向量嵌入
        embedding = generate_embedding(chapter["content"])
        
        # 存储到知识库
        save_to_knowledge_base({
            "file_id": file_id,
            "chapter_id": chapter["id"],
            "title": chapter["title"],
            "content": chapter["content"],
            "embedding": embedding,
            "metadata": {
                "category": get_file_category(file_id),
                "level": chapter["level"],
                "page": chapter["page"]
            }
        })
    
    # 5.3 完成
    update_status(file_id, FileStatus.INDEXED)
    
    # 5.4 清理临时文件（可选）
    cleanup_temp_files(file_id)
```

---

## 数据库Schema优化

### 新增字段

```sql
ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS
    -- 状态管理
    status VARCHAR(50) DEFAULT 'uploaded',
    status_updated_at TIMESTAMP,
    
    -- 路径管理
    temp_path TEXT,              -- 临时路径
    parsed_path TEXT,            -- 解析路径
    archive_path TEXT,           -- 归档路径
    
    -- 分类信息
    category VARCHAR(50),        -- 自动分类结果
    semantic_filename TEXT,      -- 语义化文件名
    
    -- 元数据
    metadata JSONB,              -- 解析元数据
    
    -- 时间戳
    uploaded_at TIMESTAMP DEFAULT NOW(),
    parsed_at TIMESTAMP,
    validated_at TIMESTAMP,
    archived_at TIMESTAMP,
    indexed_at TIMESTAMP,
    
    -- 错误处理
    error_log TEXT,              -- 错误日志
    retry_count INT DEFAULT 0;   -- 重试次数
```

### 新增索引

```sql
-- 状态查询优化
CREATE INDEX idx_file_status ON uploaded_files(status);
CREATE INDEX idx_file_category ON uploaded_files(category);
CREATE INDEX idx_file_archived_at ON uploaded_files(archived_at);

-- 元数据查询（JSONB GIN索引）
CREATE INDEX idx_file_metadata ON uploaded_files USING GIN(metadata);
```

---

## API 接口设计

### 1. 上传文件

```http
POST /api/files/upload
Content-Type: multipart/form-data

FormData:
  files: File[]
  session_id?: string  # 可选，用于批量上传

Response:
{
  "session_id": "sess_xxx",
  "files": [
    {
      "id": "file_xxx",
      "name": "document.pdf",
      "status": "uploaded",
      "temp_path": "uploads/temp/sess_xxx/file_xxx.pdf",
      "size": 102400,
      "hash": "sha256...",
      "uploaded_at": "2025-12-07T..."
    }
  ],
  "duplicates": [],
  "failed": []
}
```

### 2. 触发解析

```http
POST /api/files/parse
Content-Type: application/json

{
  "file_ids": ["file_1", "file_2"],
  "auto_archive": true,      # 解析后自动归档
  "auto_index": true         # 归档后自动索引
}

Response:
{
  "tasks": [
    {
      "file_id": "file_1",
      "task_id": "celery_task_id",
      "status": "parsing"
    }
  ]
}
```

### 3. 查询文件状态

```http
GET /api/files/{file_id}/status

Response:
{
  "id": "file_xxx",
  "name": "document.pdf",
  "status": "parsed",
  "stage": "parsed",         # temp/parsed/archived
  "progress": {
    "uploaded": true,
    "parsed": true,
    "validated": true,
    "archived": false,
    "indexed": false
  },
  "paths": {
    "temp": "uploads/temp/...",
    "parsed": "uploads/parsed/...",
    "archive": null
  },
  "metadata": { ... },
  "timestamps": {
    "uploaded_at": "...",
    "parsed_at": "...",
    "archived_at": null
  },
  "error": null
}
```

### 4. 浏览归档文件

```http
GET /api/files/archive?category=tender&year=2025&month=12

Response:
{
  "files": [
    {
      "id": "file_xxx",
      "original_name": "document.pdf",
      "semantic_name": "2025年XX项目招标文件_技术部分.pdf",
      "category": "tender",
      "archive_path": "uploads/archive/2025/12/tender/...",
      "archived_at": "..."
    }
  ],
  "total": 25,
  "categories": {
    "tender": 10,
    "proposal": 8,
    "reference": 5,
    "other": 2
  }
}
```

### 5. 重新处理失败文件

```http
POST /api/files/{file_id}/retry

Response:
{
  "id": "file_xxx",
  "status": "parsing",
  "retry_count": 2,
  "task_id": "celery_task_id"
}
```

---

## 前端交互流程

### 用户体验优化

```typescript
// 1. 上传阶段
const handleUpload = async (files: File[]) => {
  // 创建session
  const sessionId = generateSessionId()
  
  // 批量上传
  const response = await uploadFiles(files, sessionId)
  
  // 显示上传结果
  showUploadedFiles(response.files)
  
  // 询问用户：是否立即解析？
  const shouldParse = await confirm('是否立即解析文件？')
  
  if (shouldParse) {
    startParsing(response.files.map(f => f.id))
  }
}

// 2. 实时状态监控
const monitorFileStatus = (fileId: string) => {
  const eventSource = new EventSource(`/api/files/${fileId}/status/stream`)
  
  eventSource.onmessage = (event) => {
    const status = JSON.parse(event.data)
    
    // 更新进度条
    updateProgressBar(fileId, status.progress)
    
    // 更新状态标签
    updateStatusBadge(fileId, status.status)
    
    if (status.status === 'indexed') {
      eventSource.close()
      showSuccess('文件处理完成！')
    }
    
    if (status.error) {
      eventSource.close()
      showError(status.error)
    }
  }
}

// 3. 分阶段展示
<Tabs>
  <Tab label="临时区">
    {/* 显示 status=uploaded 的文件 */}
    {tempFiles.map(file => (
      <FileCard 
        file={file}
        actions={['解析', '删除']}
      />
    ))}
  </Tab>
  
  <Tab label="解析区">
    {/* 显示 status=parsed|validated 的文件 */}
    {parsedFiles.map(file => (
      <FileCard 
        file={file}
        actions={['查看元数据', '归档', '删除']}
        metadata={file.metadata}
      />
    ))}
  </Tab>
  
  <Tab label="归档区">
    {/* 按分类显示 status=archived|indexed 的文件 */}
    <Tree>
      {categories.map(cat => (
        <TreeNode label={cat.name}>
          {cat.files.map(file => (
            <FileCard 
              file={file}
              showSemanticName={true}
            />
          ))}
        </TreeNode>
      ))}
    </Tree>
  </Tab>
</Tabs>
```

---

## 错误处理与恢复

### 失败重试策略

```python
@celery_app.task(bind=True, max_retries=3)
def parse_uploaded_file(self, file_id: str):
    try:
        # 解析逻辑...
        pass
    except RecoverableError as e:
        # 可恢复错误：重试
        raise self.retry(exc=e, countdown=60)  # 1分钟后重试
    except UnrecoverableError as e:
        # 不可恢复错误：标记失败
        update_status(file_id, FileStatus.PARSE_FAILED)
        save_error_log(file_id, str(e))
```

### 隔离区管理

```python
def quarantine_file(file_id: str, reason: str):
    """
    将有问题的文件移到隔离区
    """
    quarantine_path = f"uploads/quarantine/{file_id}/"
    os.makedirs(quarantine_path, exist_ok=True)
    
    # 移动所有相关文件
    shutil.move(get_temp_path(file_id), quarantine_path)
    
    # 更新状态
    update_file_record(file_id, {
        "status": FileStatus.QUARANTINED,
        "quarantine_reason": reason,
        "quarantined_at": datetime.now()
    })
```

---

## 性能优化

### 1. 并行处理

```python
# 批量解析（并行）
@celery_app.task
def parse_batch(file_ids: List[str]):
    from celery import group
    
    # 创建并行任务组
    job = group(parse_uploaded_file.s(fid) for fid in file_ids)
    result = job.apply_async()
    
    return result.id
```

### 2. 增量索引

```python
# 只索引新增章节
def incremental_index(file_id: str):
    existing_chapters = get_indexed_chapters(file_id)
    new_chapters = get_parsed_chapters(file_id)
    
    to_index = [c for c in new_chapters if c.id not in existing_chapters]
    
    for chapter in to_index:
        index_chapter(chapter)
```

### 3. 缓存策略

```python
from core.cache import cache_result

@cache_result(expire=3600)
def get_file_metadata(file_id: str):
    """缓存元数据查询"""
    return load_metadata(file_id)
```

---

## 监控与统计

### Dashboard 数据

```sql
-- 实时处理统计
SELECT 
    status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (NOW() - uploaded_at))) as avg_time_seconds
FROM uploaded_files
WHERE uploaded_at > NOW() - INTERVAL '24 hours'
GROUP BY status;

-- 分类统计
SELECT 
    category,
    COUNT(*) as count,
    SUM(file_size) as total_size
FROM uploaded_files
WHERE status = 'indexed'
GROUP BY category;

-- 错误率
SELECT 
    DATE(uploaded_at) as date,
    COUNT(*) FILTER (WHERE status LIKE '%_failed') as failed,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status LIKE '%_failed') / COUNT(*), 2) as error_rate
FROM uploaded_files
WHERE uploaded_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(uploaded_at);
```

---

## 总结：优势对比

| 维度 | 旧架构 | 新架构 | 改进 |
|------|--------|--------|------|
| **目录管理** | 单一uploads/ | temp/parsed/archive/ | ✅ 清晰分离 |
| **状态追踪** | 无 | 9种状态+状态机 | ✅ 可追溯 |
| **错误恢复** | 无法回滚 | 重试+隔离机制 | ✅ 可恢复 |
| **文档分类** | 手动指定 | 自动分类+语义命名 | ✅ 智能化 |
| **知识库** | 直接生成 | 解析→验证→索引 | ✅ 数据质量 |
| **用户体验** | 黑盒处理 | 分阶段可见 | ✅ 透明度 |
| **性能** | 阻塞 | 异步+并行 | ✅ 高吞吐 |

---

## 实施计划

### Phase 1: 基础架构 (Week 1)
- [ ] 创建三级目录结构
- [ ] 数据库schema迁移
- [ ] 状态机实现

### Phase 2: 核心流程 (Week 2)
- [ ] 重构上传API
- [ ] 实现解析任务
- [ ] 实现归档逻辑

### Phase 3: 智能分类 (Week 3)
- [ ] 文档分类引擎
- [ ] 语义命名生成
- [ ] 知识库索引

### Phase 4: 前端适配 (Week 4)
- [ ] 分阶段UI
- [ ] 实时状态监控
- [ ] 错误处理界面

---

**这个架构是否满足你的需求？有什么需要调整的地方吗？**
