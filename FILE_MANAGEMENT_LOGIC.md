# 文件管理系统完整逻辑

## 目录
1. [架构概览](#架构概览)
2. [上传流程](#上传流程)
3. [解析流程](#解析流程)
4. [知识库生成](#知识库生成)
5. [文件检索](#文件检索)
6. [数据库设计](#数据库设计)
7. [API接口](#api接口)
8. [错误处理](#错误处理)

---

## 架构概览

```
┌─────────────┐
│   前端UI    │ FileUpload.tsx (Split 60/40布局)
└──────┬──────┘
       │ FormData (multipart/form-data)
       ↓
┌─────────────┐
│  API路由    │ routers/files.py
└──────┬──────┘
       │
       ├─→ uploaded_files表 (基础信息)
       │
       ├─→ Celery后台任务 (parse_and_store)
       │   └─→ PreprocessorAgent (文档解析)
       │       ├─→ files表 (完整内容)
       │       └─→ chapters表 (章节结构)
       │
       └─→ processFiles API调用
           └─→ 知识库生成引擎
               └─→ knowledge_base表 (向量+元数据)
```

---

## 上传流程

### 前端逻辑 (`FileUpload.tsx`)

```typescript
// 1. 用户选择文件
<Upload
  fileList={fileList}
  beforeUpload={(file) => {
    setFileList([...fileList, file])
    return false // 阻止自动上传
  }}
/>

// 2. 构造FormData
const formData = new FormData()
fileList.forEach(file => {
  formData.append('files', file.originFileObj, file.name) // 关键：添加filename
})
formData.append('doc_type', 'other')

// 3. 发送请求
const response = await fileAPI.uploadFiles(formData)

// 4. 处理响应
if (response.files?.length > 0) {
  const fileIds = response.files.map(f => f.id)
  await fileAPI.processFiles(fileIds) // 生成知识库
  fetchData() // 刷新页面数据
}
```

### 后端逻辑 (`routers/files.py`)

```python
@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    doc_type: str = Form(default="other"),  # 关键：default参数
    background_tasks: BackgroundTasks = None
):
    # 1. 验证文件类型
    for file in files:
        if not validate_file_type(file.filename):
            failed.append({"name": file.filename, "error": "不支持的文件格式"})
            continue
        
        # 2. 检查重复
        existing = db.query(UploadedFile).filter_by(filename=file.filename).first()
        if existing:
            failed.append({"name": file.filename, "error": "文件已存在"})
            continue
        
        # 3. 保存文件
        file_id = str(uuid.uuid4())
        save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 4. 创建数据库记录
        new_file = UploadedFile(
            id=file_id,
            filename=file.filename,
            file_path=save_path,
            file_size=os.path.getsize(save_path),
            file_type=doc_type
        )
        db.add(new_file)
        db.commit()
        
        # 5. 添加后台解析任务
        background_tasks.add_task(
            parse_and_store,
            file_id,
            save_path,
            file.filename,
            doc_type
        )
        
        parsed_files.append({
            "id": file_id,
            "name": file.filename,
            "size": os.path.getsize(save_path),
            "type": doc_type,
            "uploadedAt": datetime.now().isoformat()
        })
    
    return {
        "status": "success",
        "files": parsed_files,
        "failed": failed
    }
```

---

## 解析流程

### Celery后台任务 (`tasks.py`)

```python
@celery_app.task
def parse_and_store(file_id: str, file_path: str, filename: str, doc_type: str):
    """后台解析文件并存储到数据库"""
    
    # 1. 延迟导入避免循环依赖
    from backend.agents.preprocessor import PreprocessorAgent
    
    # 2. 初始化解析器
    parser = PreprocessorAgent()
    
    # 3. 解析文档结构
    doc_structure = parser.parse_document(file_path)
    # 返回: DocumentStructure {
    #   text_blocks: List[TextBlock]  # 文本块
    #   table_blocks: List[TableBlock]  # 表格
    #   chapter_nodes: List[ChapterNode]  # 章节树
    # }
    
    # 4. 存储到files表
    file_record = File(
        id=file_id,
        filename=filename,
        full_content=doc_structure.full_text,
        file_type=doc_type,
        created_at=datetime.now()
    )
    db.add(file_record)
    
    # 5. 存储章节结构
    for chapter in doc_structure.chapter_nodes:
        chapter_record = Chapter(
            id=str(uuid.uuid4()),
            file_id=file_id,
            title=chapter.title,
            level=chapter.level,
            content=chapter.content,
            parent_id=chapter.parent_id
        )
        db.add(chapter_record)
    
    db.commit()
    logger.info(f"✅ 文件解析完成: {filename}")
```

### 预处理代理 (`agents/preprocessor.py`)

```python
class PreprocessorAgent:
    def parse_document(self, file_path: str) -> DocumentStructure:
        """解析文档为结构化数据"""
        
        if file_path.endswith('.pdf'):
            return self._parse_pdf(file_path)
        elif file_path.endswith(('.docx', '.doc')):
            return self._parse_word(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            return self._parse_excel(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_path}")
    
    def _parse_pdf(self, file_path: str) -> DocumentStructure:
        """PDF解析（使用pdfplumber提取表格）"""
        
        text_blocks = []
        table_blocks = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本
                text = page.extract_text()
                if text:
                    text_blocks.append(TextBlock(
                        content=text,
                        page_number=page_num,
                        block_type="paragraph"
                    ))
                
                # 提取表格（准确率90% vs PyPDF 30%）
                tables = page.extract_tables()
                for table in tables:
                    table_blocks.append(TableBlock(
                        data=table,
                        page_number=page_num,
                        rows=len(table),
                        cols=len(table[0]) if table else 0
                    ))
        
        # 生成章节树
        chapter_nodes = self._build_chapter_tree(text_blocks)
        
        return DocumentStructure(
            text_blocks=text_blocks,
            table_blocks=table_blocks,
            chapter_nodes=chapter_nodes
        )
```

---

## 知识库生成

### 触发流程

```typescript
// 前端调用
const fileIds = uploadedFiles.map(f => f.id)
await fileAPI.processFiles(fileIds)
```

```python
# 后端处理 (routers/files.py)
@router.post("/process")
async def process_files(request: ProcessRequest):
    """生成知识库条目"""
    
    for file_id in request.fileIds:
        # 1. 获取文件内容
        file_record = db.query(File).filter_by(id=file_id).first()
        if not file_record:
            continue
        
        # 2. 获取章节
        chapters = db.query(Chapter).filter_by(file_id=file_id).all()
        
        # 3. 生成向量嵌入
        from backend.engines.embedding_engine import EmbeddingEngine
        embedding_engine = EmbeddingEngine()
        
        for chapter in chapters:
            # 生成向量
            embedding = await embedding_engine.generate_embedding(chapter.content)
            
            # 存储到knowledge_base表
            kb_entry = KnowledgeBase(
                id=str(uuid.uuid4()),
                file_id=file_id,
                chapter_id=chapter.id,
                content=chapter.content,
                embedding=embedding,  # pgvector类型
                metadata={
                    "title": chapter.title,
                    "level": chapter.level,
                    "source": file_record.filename
                }
            )
            db.add(kb_entry)
        
        db.commit()
    
    return {"status": "success", "processed": len(request.fileIds)}
```

### 向量检索

```python
# 使用pgvector进行相似度搜索
@router.get("/search")
async def search_knowledge(query: str, top_k: int = 5):
    """语义搜索知识库"""
    
    # 1. 生成查询向量
    query_embedding = await embedding_engine.generate_embedding(query)
    
    # 2. pgvector相似度搜索
    results = db.execute(text("""
        SELECT 
            kb.content,
            kb.metadata,
            1 - (kb.embedding <=> :query_embedding) AS similarity
        FROM knowledge_base kb
        ORDER BY kb.embedding <=> :query_embedding
        LIMIT :top_k
    """), {
        "query_embedding": query_embedding,
        "top_k": top_k
    })
    
    return [
        {
            "content": row.content,
            "metadata": row.metadata,
            "score": row.similarity
        }
        for row in results
    ]
```

---

## 文件检索

### 按文件名搜索

```python
@router.get("/files")
async def get_files(search: str = None):
    """获取文件列表（支持搜索）"""
    
    query = db.query(UploadedFile)
    
    if search:
        query = query.filter(
            UploadedFile.filename.ilike(f"%{search}%")
        )
    
    files = query.order_by(UploadedFile.created_at.desc()).all()
    
    return {
        "status": "success",
        "files": [
            {
                "id": f.id,
                "name": f.filename,
                "type": f.file_type,
                "size": f.file_size,
                "uploadedAt": f.created_at.isoformat()
            }
            for f in files
        ],
        "total": len(files)
    }
```

### 获取文件详情

```python
@router.get("/files/{file_id}/detail")
async def get_file_detail(file_id: str):
    """获取文件详细信息"""
    
    # 基础信息
    uploaded_file = db.query(UploadedFile).filter_by(id=file_id).first()
    
    # 解析内容
    file_record = db.query(File).filter_by(id=file_id).first()
    
    # 章节结构
    chapters = db.query(Chapter).filter_by(file_id=file_id).all()
    
    # 知识库条目
    kb_entries = db.query(KnowledgeBase).filter_by(file_id=file_id).all()
    
    return {
        "file": {
            "id": uploaded_file.id,
            "name": uploaded_file.filename,
            "path": uploaded_file.file_path,
            "size": uploaded_file.file_size,
            "type": uploaded_file.file_type
        },
        "content": file_record.full_content if file_record else None,
        "chapters": [
            {
                "id": c.id,
                "title": c.title,
                "level": c.level,
                "content": c.content[:200] + "..."  # 预览
            }
            for c in chapters
        ],
        "knowledge_entries": len(kb_entries)
    }
```

---

## 数据库设计

### 核心表结构

```sql
-- 1. 上传文件表（基础信息）
CREATE TABLE uploaded_files (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 文件内容表（解析后的完整内容）
CREATE TABLE files (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    full_content TEXT,  -- 完整文本
    file_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id) REFERENCES uploaded_files(id) ON DELETE CASCADE
);

-- 3. 章节表（文档结构）
CREATE TABLE chapters (
    id VARCHAR(36) PRIMARY KEY,
    file_id VARCHAR(36) NOT NULL,
    title VARCHAR(500),
    level INTEGER,  -- 1=一级标题, 2=二级...
    content TEXT,
    parent_id VARCHAR(36),  -- 父章节ID（树形结构）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES chapters(id) ON DELETE SET NULL
);

-- 4. 知识库表（向量存储）
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_base (
    id VARCHAR(36) PRIMARY KEY,
    file_id VARCHAR(36) NOT NULL,
    chapter_id VARCHAR(36),
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embedding维度
    metadata JSONB,  -- {"title": "...", "source": "...", "level": 1}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE SET NULL
);

-- 向量索引（加速相似度搜索）
CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 关系图

```
uploaded_files (1) ←─────→ (1) files
                              ↓
                           (1:N)
                              ↓
                          chapters (树形结构)
                              ↓
                           (1:N)
                              ↓
                        knowledge_base
```

---

## API接口

### 文件上传

```http
POST /api/files/upload
Content-Type: multipart/form-data

FormData:
  files: File[]
  doc_type: string = "other"
  overwrite: boolean = false

Response:
{
  "status": "success",
  "totalFiles": 2,
  "files": [
    {
      "id": "uuid",
      "name": "document.pdf",
      "size": 102400,
      "type": "other",
      "uploadedAt": "2024-01-01T00:00:00"
    }
  ],
  "failed": []
}
```

### 文件列表

```http
GET /api/files?search=project

Response:
{
  "status": "success",
  "files": [...],
  "total": 19
}
```

### 处理文件

```http
POST /api/files/process
Content-Type: application/json

{
  "fileIds": ["uuid1", "uuid2"]
}

Response:
{
  "status": "success",
  "processed": 2
}
```

### 文档索引

```http
GET /api/files/document-indexes?fileId=uuid

Response:
{
  "indexes": [
    {
      "id": "uuid",
      "fileName": "document.pdf",
      "chapterTitle": "第一章",
      "level": 1,
      "preview": "内容预览...",
      "createdAt": "2024-01-01T00:00:00"
    }
  ]
}
```

### 知识库搜索

```http
GET /api/files/search?query=项目经理资质&top_k=5

Response:
{
  "results": [
    {
      "content": "项目经理应具有...",
      "metadata": {
        "title": "人员要求",
        "source": "tender.pdf",
        "level": 2
      },
      "score": 0.92
    }
  ]
}
```

### 文件下载

```http
GET /api/files/uploaded/{file_id}/download

Response:
File stream (application/octet-stream)
```

### 文件删除

```http
DELETE /api/files/uploaded/{file_id}

Response:
{
  "status": "success",
  "message": "文件已删除"
}
```

---

## 错误处理

### 前端错误处理

```typescript
try {
  const response = await fileAPI.uploadFiles(formData)
  
  if (response.files?.length > 0) {
    message.success(`成功上传 ${response.files.length} 个文件`)
  }
  
  if (response.failed?.length > 0) {
    response.failed.forEach(fail => {
      message.warning(`${fail.name}: ${fail.error}`)
    })
  }
  
} catch (error) {
  console.error('上传失败:', error)
  
  if (error.response?.status === 422) {
    message.error('请求参数错误，请检查文件格式')
  } else if (error.response?.status === 500) {
    message.error('服务器错误，请稍后重试')
  } else {
    message.error('上传失败: ' + (error.message || '未知错误'))
  }
}
```

### 后端错误处理

```python
@router.post("/upload")
async def upload_files(...):
    try:
        # 处理逻辑...
        
    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"上传失败: {str(e)}"
        )

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None
        }
    )
```

### 常见错误码

| 错误码 | 含义 | 处理方式 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查FormData格式 |
| 422 | 验证失败 | 检查文件类型、Form参数 |
| 413 | 文件太大 | 调整上传大小限制 |
| 500 | 服务器错误 | 查看后端日志 |
| 503 | 服务不可用 | 检查Docker服务状态 |

---

## 性能优化

### 1. 后台任务处理

```python
# ✅ 正确：使用Celery异步处理
background_tasks.add_task(parse_and_store, file_id, ...)

# ❌ 错误：同步处理阻塞请求
parse_and_store(file_id, ...)
```

### 2. 批量操作

```python
# ✅ 正确：批量commit
for chapter in chapters:
    db.add(chapter)
db.commit()

# ❌ 错误：每次循环commit
for chapter in chapters:
    db.add(chapter)
    db.commit()  # 性能差
```

### 3. 向量索引

```sql
-- 创建IVFFlat索引加速搜索（100倍速度提升）
CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

### 4. Redis缓存

```python
from core.cache import cache_result

@cache_result(expire=3600)  # 缓存1小时
async def get_file_statistics():
    return db.query(...).all()
```

---

## 监控与日志

### 日志配置 (`core/logger.py`)

```python
from loguru import logger

logger.add(
    "logs/file_upload_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天轮换
    retention="30 days",  # 保留30天
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    enqueue=True  # 异步写入
)
```

### 关键日志点

```python
# 上传开始
logger.info(f"开始上传文件: {filename}, 大小: {file_size}")

# 解析完成
logger.info(f"✅ 文件解析完成: {filename}, 章节数: {len(chapters)}")

# 知识库生成
logger.info(f"生成知识库条目: file_id={file_id}, 条目数: {count}")

# 错误记录
logger.error(f"上传失败: {filename}, 原因: {str(e)}", exc_info=True)
```

### 查看日志

```bash
# 后端日志
./docker-manager.sh logs backend

# 实时监控
tail -f backend/logs/file_upload_$(date +%Y-%m-%d).log

# 过滤错误
docker logs bidding_backend 2>&1 | grep ERROR
```

---

## 测试清单

### 功能测试

- [ ] 上传单个文件（PDF/Word/Excel）
- [ ] 批量上传多个文件
- [ ] 重复文件检测
- [ ] 不支持的文件格式拒绝
- [ ] 文件列表显示
- [ ] 文件搜索
- [ ] 文件下载
- [ ] 文件删除
- [ ] 章节解析准确性
- [ ] 表格提取完整性
- [ ] 知识库生成
- [ ] 向量搜索准确性

### 性能测试

- [ ] 大文件上传（>10MB）
- [ ] 并发上传（10个文件）
- [ ] 向量搜索响应时间（<100ms）
- [ ] 数据库查询优化

### 错误处理测试

- [ ] 无效文件类型
- [ ] 文件已存在
- [ ] 磁盘空间不足
- [ ] 数据库连接失败
- [ ] 网络中断

---

## 故障排查

### 问题1：上传后无反应

**症状**：进度条到100%后消失，无文件显示

**排查步骤**：
```bash
# 1. 检查后端日志
docker logs bidding_backend --tail 50

# 2. 检查数据库
docker exec -it bidding_postgres psql -U postgres -d bidding_db -c \
  "SELECT COUNT(*) FROM uploaded_files;"

# 3. 手动测试API
curl -X POST http://localhost:8000/api/files/upload \
  -F "files=@test.txt" \
  -F "doc_type=other"
```

**常见原因**：
- FormData缺少filename参数
- 后端Form参数类型错误
- 数据库连接失败

### 问题2：422错误

**症状**：所有上传请求返回422

**原因**：
- `doc_type: str = Form("other")` 缺少 `default=`
- FormData字段名不匹配

**解决**：
```python
# ✅ 正确
doc_type: str = Form(default="other")

# ❌ 错误
doc_type: str = Form("other")
```

### 问题3：知识库未生成

**排查**：
```bash
# 检查Celery worker
docker logs bidding_celery_worker --tail 50

# 检查knowledge_base表
docker exec -it bidding_postgres psql -U postgres -d bidding_db -c \
  "SELECT COUNT(*) FROM knowledge_base;"
```

---

## 总结

### 核心流程

1. **上传** → 2. **保存** → 3. **解析** → 4. **知识库** → 5. **检索**

### 关键技术

- **pdfplumber**: 表格提取（90%准确率）
- **pgvector**: 向量存储和检索
- **Celery**: 异步任务处理
- **Pydantic**: 数据验证
- **React Split**: 可调整布局

### 最佳实践

- ✅ 使用FormData明确指定filename
- ✅ 后台任务处理耗时操作
- ✅ 批量commit减少数据库压力
- ✅ 向量索引加速搜索
- ✅ 完善的错误处理和日志

---

**文档版本**: 1.0  
**最后更新**: 2024-01-XX  
**维护者**: 标书智能系统团队
