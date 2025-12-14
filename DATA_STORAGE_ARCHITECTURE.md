# 📊 数据存储架构与位置逻辑分析

## 🎯 当前系统架构

### 1. 文件存储位置 (File System)

```
项目根目录/
├── uploads/                          # 配置: UPLOAD_DIR (config.py)
│   ├── temp/                         # 临时文件夹 (阶段1)
│   │   └── *.pdf, *.docx            # 上传的原始文件
│   ├── parsed/                       # 解析后的文件 (阶段2)
│   │   └── {uuid}/
│   │       ├── extracted.json        # 提取的结构化数据
│   │       ├── metadata.json         # 文件元数据
│   │       └── chapters.json         # 章节信息
│   └── archive/                      # 存档文件 (阶段3)
│       └── {year}/{month}/
│           └── {filename}            # 最终存档位置
```

**配置源**: `backend/core/config.py`
```python
UPLOAD_DIR: str = "./uploads"  # 相对或绝对路径
# 自动创建: upload_path 属性会在 backend/ 父目录创建
```

### 2. 数据库存储位置 (PostgreSQL)

```
Database: bidding_db (config.py: DB_NAME)
Host: localhost (config.py: DB_HOST)
Port: 5432 (config.py: DB_PORT)
User: postgres (config.py: DB_USER)

核心表结构:
├── uploaded_files              # 上传文件元数据
│   ├── id (uuid)
│   ├── filename
│   ├── file_path              # 在 uploads/ 中的位置
│   ├── file_size
│   ├── sha256                 # 文件哈希，用于去重
│   ├── status                 # uploaded/parsing/parsed/archived
│   └── created_at
│
├── files                       # 解析后的文件
│   ├── id (uuid)
│   ├── filename
│   ├── filepath               # 完整文件路径
│   ├── content                # 文本内容
│   ├── metadata (jsonb)       # 元数据
│   └── created_at
│
├── chapters                    # 文件章节
│   ├── id (uuid)
│   ├── file_id (fk)           # 关联到 files
│   ├── chapter_title
│   ├── chapter_level          # 1,2,3...
│   ├── content
│   ├── position_order         # 章节顺序
│   └── structure_data (jsonb)
│
├── vectors                     # 向量知识库 (用于语义搜索)
│   ├── id (uuid)
│   ├── file_id (fk)
│   ├── chapter_id (fk)
│   ├── chunk_text
│   ├── embedding (vector)     # OpenAI embedding
│   └── metadata (jsonb)
│
└── chapter_*_rules            # 各类规则表
    ├── chapter_structure_rules
    ├── chapter_content_rules
    ├── chapter_custom_rules
    ├── chapter_boq_rules
    ├── chapter_mandatory_rules
    └── chapter_scoring_rules
```

### 3. 知识库存储位置 (Knowledge Base)

知识库分为两种：

**A. 文件级知识库** (Files Table + Vectors)
```
files 表存储：
- 原始文本内容
- 文件级元数据
- 关联的章节列表

vectors 表存储：
- 文本的向量化表示 (embedding)
- 用于语义搜索和相似度计算
- 支持向量距离查询
```

**B. 章节级知识库** (Chapters + Chapter_*_Rules)
```
chapters 表存储：
- 章节标题、内容、等级
- 章节顺序和结构

chapter_*_rules 表存储：
- 结构规则 (chapter_structure_rules)
- 内容规则 (chapter_content_rules)
- 自定义规则 (chapter_custom_rules)
- BOM 规则 (chapter_boq_rules)
- 强制要求 (chapter_mandatory_rules)
- 评分规则 (chapter_scoring_rules)
```

---

## 🔄 数据流向与存储顺序

### 阶段1: 上传 (Upload Phase)
```
客户端上传文件
    ↓
保存到: uploads/temp/{filename}
    ↓
创建记录: uploaded_files 表
    ├── file_path = "uploads/temp/{filename}"
    ├── status = "uploaded"
    ├── sha256 = 计算文件哈希
    └── created_at = 当前时间
```

### 阶段2: 解析 (Parse Phase)
```
读取: uploads/temp/{filename}
    ↓
使用 ParseEngine 解析
    ├── 提取: 章节结构、内容
    ├── 生成: 向量 embeddings
    └── 保存: uploads/parsed/{uuid}/ 中的 JSON 文件
    ↓
创建数据库记录:
├── files 表
│   ├── filepath = "uploads/parsed/{uuid}/extracted.json"
│   ├── content = 完整文本
│   └── metadata = 提取的元数据
├── chapters 表 (针对每一章)
├── vectors 表 (针对每个 chunk)
└── chapter_*_rules 表 (规则初始化)
    ↓
更新: uploaded_files 表
└── status = "parsed"
```

### 阶段3: 归档 (Archive Phase)
```
读取: uploads/parsed/{uuid}/
    ↓
移动到: uploads/archive/{year}/{month}/{filename}
    ↓
更新数据库:
├── uploaded_files
│   ├── file_path = "uploads/archive/{year}/{month}/{filename}"
│   └── status = "archived"
└── files
    └── filepath = "uploads/archive/{year}/{month}/{filename}"
```

---

## ✅ 数据一致性保证

### 1. 文件路径同步
```python
# uploaded_files.file_path 应与实际文件位置一致
# 规则:
# - temp 阶段: uploads/temp/
# - parsed 阶段: uploads/parsed/{uuid}/
# - archive 阶段: uploads/archive/{year}/{month}/
```

### 2. 数据库记录完整性
```python
# 每个上传文件应有:
✓ uploaded_files 记录 (元数据和状态)
✓ files 记录 (完整文本和结构)
✓ chapters 记录 (所有章节)
✓ vectors 记录 (向量表示)
✓ chapter_*_rules 记录 (初始化规则)
```

### 3. 引用完整性
```python
# 数据库关联关系:
chapters.file_id → files.id
vectors.file_id → files.id
vectors.chapter_id → chapters.id
chapter_*_rules.chapter_id → chapters.id
```

---

## 🔧 实现要点

### 当前代码位置
```
配置: backend/core/config.py
- UPLOAD_DIR: 上传目录基路径
- upload_path: 属性方法，返回绝对路径

初始化: backend/routers/files.py
- UPLOAD_DIR: 获取配置
- TEMP_DIR: uploads/temp
- PARSED_DIR: uploads/parsed
- ARCHIVE_DIR: uploads/archive

数据库: backend/init_database.sql
- 24 个核心表
- uploaded_files: 文件元数据
- files: 解析后的文件
- chapters: 章节
- vectors: 向量知识库
- chapter_*_rules: 规则库
```

### 关键文件
```
backend/routers/files.py (1456行)
- upload_files() 处理上传
- process_uploaded_file() 处理解析
- archive_file() 处理归档

backend/engines/parse_engine.py
- 文本提取和章节解析

backend/database/__init__.py
- 数据库连接和查询
```

---

## 📋 数据验证检查清单

在执行安装前，需要验证：

### ✅ 文件系统
- [ ] `uploads/` 目录存在或可创建
- [ ] `uploads/temp/` 有写权限
- [ ] `uploads/parsed/` 有写权限
- [ ] `uploads/archive/` 有写权限

### ✅ 数据库
- [ ] PostgreSQL 运行中 (localhost:5432)
- [ ] `bidding_db` 数据库存在
- [ ] 所有 24 个表已创建
- [ ] 表结构与代码匹配

### ✅ 数据同步
- [ ] `uploaded_files.file_path` 与实际文件位置一致
- [ ] `files.filepath` 与 `uploaded_files.file_path` 对应
- [ ] 所有外键引用完整
- [ ] 没有孤立的数据库记录

---

## 🚨 无用逻辑清理清单

需要删除的无用逻辑：
- [ ] 硬编码的目录创建语句 (应使用 config)
- [ ] 重复的目录初始化代码
- [ ] 过时的文件移动逻辑
- [ ] 不使用的临时表或视图
- [ ] 冗余的状态字段

需要保留的逻辑：
- ✓ 三阶段架构 (temp → parsed → archive)
- ✓ 文件去重机制 (sha256 哈希)
- ✓ 状态追踪 (uploaded/parsing/parsed/archived)
- ✓ 向量知识库 (embeddings)
- ✓ 规则库 (各类 *_rules 表)

---

**现在已分析完成，可以开始执行安装步骤！**

