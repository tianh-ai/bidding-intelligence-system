# 📚 两个关键脚本深度学习指南

## 脚本1: verify_new_parser.py - 解析器验证脚本

### 📖 脚本目的
验证PDF解析引擎提取的章节结构是否与PDF原始目录一致。这是**验收测试**脚本，用来测量解析准确率。

### 🏗️ 架构设计

```
┌─────────────┐
│   PDF文件   │ (bidding_example.pdf)
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   ParseEngine           │ 调用: pdfplumber + 文本解析
│   - 打开PDF文件         │
│   - 提取所有文本        │
└──────┬──────────────────┘
       │ 返回: raw_text
       ▼
┌──────────────────────────────────┐
│ EnhancedChapterExtractor        │ 调用: 正则表达式 + 章节检测算法
│ - 识别章节标记 (第、章、节等)    │
│ - 构建章节树结构                  │
│ - 返回 ChapterNode 列表          │
└──────┬───────────────────────────┘
       │ 返回: extracted_chapters
       ▼
┌──────────────────────────┐
│  对比验证 (核心逻辑)      │
│  toc_items vs chapters   │
│  - 逐项匹配              │
│  - 计算成功率            │
└──────┬───────────────────┘
       │
       ▼
┌────────────────────────┐
│ 输出结果               │
│ - 匹配成功数 N/16      │
│ - 成功率百分比         │
│ - 结构统计 (章/节数)   │
└────────────────────────┘
```

### 💻 关键代码详解

#### 1️⃣ 参考TOC定义 (lines 1-30)
```python
toc_items = [
    "第一部分  投标邀请",
    "一、投标说明",
    "二、投标人资格要求",
    "三、投标人应具备的条件",
    "四、招标人联系方式",
    # ... 共16项
]
```
**作用**: 定义PDF原始目录，作为验证的基准线

#### 2️⃣ 主验证流程 (lines 32-65)
```python
# Step 1: 初始化解析引擎
parser = ParseEngine()
raw_text = parser.parse(pdf_path)

# Step 2: 提取章节结构
extractor = EnhancedChapterExtractor()
chapters = extractor.extract_chapters(raw_text)

# Step 3: 构建查找字典 (性能优化)
ch_dict = {ch.title: ch for ch in chapters}

# Step 4: 逐项验证 (核心匹配逻辑)
matched = 0
for item in toc_items:
    if match_chapter(item, ch_dict):
        matched += 1
        print(f"✓ {item}")
    else:
        print(f"✗ {item}")

# Step 5: 计算成功率
success_rate = (matched / len(toc_items)) * 100
print(f"成功率: {success_rate:.1f}% ({matched}/{len(toc_items)})")
```

#### 3️⃣ 章节匹配逻辑 (lines 40-52)
```python
def match_chapter(toc_item, ch_dict):
    """
    核心匹配算法:
    1. 检查章节号是否存在 (e.g., "一" in ch_dict)
    2. 检查标题相似度 (使用 difflib.SequenceMatcher)
    3. 相似度阈值 > 0.8 则视为匹配
    """
    # 提取章节号 (e.g., "一" from "一、投标说明")
    chapter_num = extract_chapter_number(toc_item)
    
    if chapter_num not in ch_dict:
        return False
    
    # 计算字符串相似度
    ch_title = ch_dict[chapter_num].title
    ratio = difflib.SequenceMatcher(None, toc_item, ch_title).ratio()
    
    return ratio > 0.8  # 相似度阈值
```

### 🔧 使用方法

```bash
# 方法1: 默认验证 (使用示例PDF)
cd backend
python verify_new_parser.py

# 方法2: 验证特定PDF (修改脚本中的 pdf_path)
# 编辑 verify_new_parser.py 第75行
pdf_path = "/Volumes/ssd/bidding-data/uploads/your_pdf.pdf"
python verify_new_parser.py

# 方法3: 作为模块导入 (在其他脚本中使用)
from verify_new_parser import verify_parser_accuracy
success_rate = verify_parser_accuracy("path/to/pdf.pdf")
```

### 📊 输出示例

```
验证PDF解析器准确率
PDF文件: bidding_example.pdf

TOC 对比结果:
✓ 第一部分  投标邀请
✓ 一、投标说明
✗ 二、投标人资格要求  [缺失]
✓ 三、投标人应具备的条件
...

解析统计:
- 总目录项: 16
- 成功提取: 14
- 成功率: 87.5%

章节结构:
- 总章节数: 15
- 总节数: 42
```

### 🎯 关键学习点

| 概念 | 说明 |
|------|------|
| **ParseEngine** | 负责打开PDF并提取原始文本，支持表格识别 |
| **EnhancedChapterExtractor** | 使用正则表达式检测章节模式 (如"第一"、"一、"等) |
| **SequenceMatcher** | Python标准库算法，计算字符串相似度 (0-1之间) |
| **threshold 0.8** | 相似度阈值，高于此值视为成功匹配 |
| **成功率** | (matched_count / total_toc_items) * 100 |

---

## 脚本2: init_database.py - 数据库初始化脚本

### 📖 脚本目的
初始化投标智能系统的PostgreSQL数据库，创建所有必需的表、索引和约束。

### 🏗️ 数据库架构

```
┌────────────────────────────────────┐
│     PostgreSQL 数据库设计          │
│     bidding_db (on SSD)            │
└────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────────┐┌──────────────┐┌─────────────────────┐
│knowledge_   ││uploaded_     ││parsing_            │
│base         ││files         ││results             │
│(知识库)     ││(上传追踪)    ││(解析结果)          │
└─────────────┘└──────────────┘└─────────────────────┘
    │                 │                    │
    ├─id (UUID)      ├─id (UUID)         ├─id (UUID)
    ├─title          ├─file_name         ├─file_id (FK)
    ├─content        ├─file_path         ├─chapter_count
    ├─category       ├─file_size         ├─parsing_time
    ├─file_id (FK)   ├─upload_status     ├─parsing_status
    ├─file_name      ├─parse_status      ├─error_message
    ├─source         ├─storage_location  ├─result_json
    ├─embedding      └─created_at        └─created_at
    └─timestamps
```

### 💻 核心表结构详解

#### 表1️⃣: knowledge_base (知识库表)
```sql
CREATE TABLE knowledge_base (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 内容字段
    title VARCHAR(255) NOT NULL,           -- 条目标题
    content TEXT NOT NULL,                 -- 完整内容
    category VARCHAR(100),                 -- 分类 (e.g., "资格", "条件", "文件")
    
    -- 溯源字段
    file_id UUID REFERENCES uploaded_files(id),  -- 来源文件
    file_name VARCHAR(255),                      -- 来源文件名
    source VARCHAR(100),                        -- 来源 (e.g., "招标文件", "API")
    
    -- AI增强字段
    embedding vector(1536),                -- OpenAI 嵌入 (用于语义搜索)
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引 (加快查询)
CREATE INDEX idx_knowledge_base_file_id ON knowledge_base(file_id);
CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
```

**用途**: 存储从招标文件中提取的所有知识条目 (资格要求、投标条件、技术规格等)

**示例数据**:
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "项目经理资质要求",
  "content": "项目经理应具备: 1) 5年以上相关工作经验 2) PMP认证或同等资质 3)...",
  "category": "资格条件",
  "file_id": "a1b2c3d4-e5f6-...",
  "file_name": "招标文件.pdf",
  "source": "招标文件",
  "embedding": [0.001, 0.042, -0.023, ... (1536个维度)]
}
```

#### 表2️⃣: uploaded_files (上传文件追踪表)
```sql
CREATE TABLE uploaded_files (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 文件信息
    file_name VARCHAR(255) NOT NULL,           -- 原始文件名
    file_path TEXT NOT NULL,                   -- 完整文件路径
    file_size BIGINT,                          -- 文件大小 (字节)
    
    -- 处理状态 (工作流)
    upload_status TEXT DEFAULT 'pending',      -- pending|completed|failed
    parse_status TEXT DEFAULT 'pending',       -- pending|processing|completed|failed
    
    -- 存储位置 (关键: 指向SSD)
    storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data/uploads',
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引 (加快状态查询)
CREATE INDEX idx_uploaded_files_name 
    ON uploaded_files(file_name);
CREATE INDEX idx_uploaded_files_status 
    ON uploaded_files(upload_status, parse_status);
```

**用途**: 跟踪用户上传的文件生命周期

**状态流转**:
```
上传文件
   │
   ├─ upload_status: pending → completed
   └─ parse_status: pending → processing → completed/failed
```

**示例数据**:
```json
{
  "id": "b2c3d4e5-f6a7-...",
  "file_name": "招标文件_2024.pdf",
  "file_path": "/Volumes/ssd/bidding-data/uploads/招标文件_2024.pdf",
  "file_size": 2048576,  // 2MB
  "upload_status": "completed",
  "parse_status": "completed",
  "storage_location": "/Volumes/ssd/bidding-data/uploads",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### 表3️⃣: parsing_results (解析结果表)
```sql
CREATE TABLE parsing_results (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 外键关系
    file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
    
    -- 解析结果
    chapter_count INTEGER,                     -- 提取的章节数
    parsing_time FLOAT,                        -- 解析耗时 (秒)
    parsing_status TEXT DEFAULT 'pending',     -- pending|completed|failed
    error_message TEXT,                        -- 失败时的错误信息
    
    -- 结果数据 (JSON格式灵活存储)
    result_json JSONB,                         -- 完整解析结果
    
    -- 存储位置 (指向SSD解析结果目录)
    storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data/parsed',
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引 (按文件查询)
CREATE INDEX idx_parsing_results_file_id 
    ON parsing_results(file_id);
```

**用途**: 存储PDF解析的结果和元数据

**示例数据**:
```json
{
  "id": "c3d4e5f6-a7b8-...",
  "file_id": "b2c3d4e5-f6a7-...",
  "chapter_count": 24,
  "parsing_time": 3.45,  // 秒
  "parsing_status": "completed",
  "error_message": null,
  "result_json": {
    "chapters": [
      {"num": "第一部分", "title": "投标邀请", "content": "..."},
      {"num": "一", "title": "投标说明", "content": "..."}
    ],
    "total_pages": 156,
    "extraction_accuracy": 0.92
  },
  "storage_location": "/Volumes/ssd/bidding-data/parsed",
  "created_at": "2024-01-15T10:31:00Z"
}
```

### 💻 代码执行流程

#### Step 1: 初始化数据库连接 (lines 1-25)
```python
import asyncio
import asyncpg
from loguru import logger

# 配置数据库连接参数
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "bidding_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# 连接字符串
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def get_db_connection():
    """获取异步数据库连接"""
    return await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
```

#### Step 2: 主初始化函数 (lines 26-50)
```python
async def init_database():
    """主初始化函数 - 协调所有表的创建"""
    try:
        db = await get_db_connection()
        logger.info("✓ 数据库连接成功")
        
        # 按依赖顺序创建表
        # 1. 先创建独立表 (没有外键依赖)
        await create_uploaded_files_table(db)
        
        # 2. 再创建有外键的表 (依赖 uploaded_files)
        await create_knowledge_base_table(db)
        await create_parsing_results_table(db)
        
        await db.close()
        logger.info("✓ 所有表创建完成")
        return True
        
    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {e}")
        return False
```

#### Step 3: 创建uploaded_files表 (lines 51-75)
```python
async def create_uploaded_files_table(db):
    """创建上传文件追踪表"""
    try:
        query = """
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            file_size BIGINT,
            upload_status TEXT DEFAULT 'pending',
            parse_status TEXT DEFAULT 'pending',
            storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data/uploads',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await db.execute(query)
        logger.info("✓ uploaded_files 表已创建")
        
        # 创建索引 (加速查询)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_uploaded_files_name 
            ON uploaded_files(file_name)
        """)
        
    except Exception as e:
        logger.warning(f"表可能已存在: {e}")
```

#### Step 4: 创建knowledge_base表 (类似结构)

#### Step 5: 创建parsing_results表 (类似结构)

#### Step 6: 验证存储路径 (lines 140-155)
```python
async def verify_storage_paths():
    """确保所有SSD存储目录存在"""
    paths = [
        "/Volumes/ssd/bidding-data/uploads",
        "/Volumes/ssd/bidding-data/parsed",
        "/Volumes/ssd/bidding-data/archive",
        "/Volumes/ssd/bidding-data/logs"
    ]
    
    for path in paths:
        if os.path.exists(path):
            logger.info(f"✓ {path}")
        else:
            logger.warning(f"⚠️ {path} 不存在，正在创建...")
            os.makedirs(path, exist_ok=True)
```

#### Step 7: 主函数入口 (lines 156-195)
```python
async def main():
    """脚本主入口"""
    print("=" * 60)
    print("🚀 数据库初始化")
    print("=" * 60)
    
    # 1. 验证SSD存储路径
    await verify_storage_paths()
    
    # 2. 初始化数据库
    success = await init_database()
    
    # 3. 输出结果
    if success:
        print("✅ 数据库初始化完成！")
        print("\n存储配置:")
        print("  - 文件上传: /Volumes/ssd/bidding-data/uploads")
        print("  - 解析结果: /Volumes/ssd/bidding-data/parsed")
        print("  - 归档文件: /Volumes/ssd/bidding-data/archive")
        print("  - 日志文件: /Volumes/ssd/bidding-data/logs")
    else:
        print("❌ 数据库初始化失败")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

### 🔧 使用方法

```bash
# 1. 确保PostgreSQL运行中
psql -U postgres  # 验证连接

# 2. 创建数据库 (如果不存在)
createdb bidding_db

# 3. 运行初始化脚本
cd backend
python3 init_database.py

# 输出应该类似于:
# ============================================================
# 🚀 数据库初始化
# ============================================================
# 
# 验证存储路径:
#   ✓ /Volumes/ssd/bidding-data/uploads
#   ✓ /Volumes/ssd/bidding-data/parsed
#   ✓ /Volumes/ssd/bidding-data/archive
#   ✓ /Volumes/ssd/bidding-data/logs
# 
# ✓ 数据库连接成功
# ✓ uploaded_files 表已创建
# ✓ knowledge_base 表已创建
# ✓ parsing_results 表已创建
# 
# ============================================================
# ✅ 数据库初始化完成！
# ...
```

### 📊 执行后的验证

```bash
# 进入PostgreSQL
psql -U postgres -d bidding_db

# 查看创建的表
\dt

# 预期输出:
#           List of relations
#  Schema |        Name         | Type  | Owner
# ────────┼─────────────────────┼───────┼──────
#  public | knowledge_base      | table | postgres
#  public | parsing_results     | table | postgres
#  public | uploaded_files      | table | postgres

# 查看表结构
\d knowledge_base
\d uploaded_files
\d parsing_results

# 查看索引
\di

# 插入测试数据
INSERT INTO uploaded_files (file_name, file_path, file_size) 
VALUES ('test.pdf', '/path/to/test.pdf', 1024);

# 查询数据
SELECT * FROM uploaded_files;
```

### 🎯 关键学习点

| 概念 | 说明 |
|------|------|
| **UUID主键** | 分布式系统友好的唯一标识符 (优于自增ID) |
| **Foreign Key** | `file_id REFERENCES uploaded_files(id)` 维护关系完整性 |
| **ON DELETE CASCADE** | 删除父记录时自动删除相关子记录 |
| **JSONB** | PostgreSQL灵活的JSON数据类型 |
| **Vector(1536)** | OpenAI嵌入向量 (用于语义相似度搜索) |
| **异步执行** | `asyncio + asyncpg` 提高并发性能 |
| **索引策略** | 在经常查询的列上创建索引 (file_id, status等) |
| **IF NOT EXISTS** | 幂等操作 (多次运行不会报错) |

---

## 🔗 两个脚本的关系

```
文件上传流程:

1️⃣ 用户上传PDF
   ↓
2️⃣ inserted INTO uploaded_files (file_name, file_path, ...)
   ↓
3️⃣ verify_new_parser.py 验证 (测试环节)
   ├─ ParseEngine 提取文本
   ├─ EnhancedChapterExtractor 提取章节
   └─ 与参考TOC对比 → 得出准确率
   ↓
4️⃣ INSERT INTO parsing_results (file_id, chapter_count, result_json, ...)
   ↓
5️⃣ INSERT INTO knowledge_base (file_id, title, content, category, embedding, ...)
   ↓
✅ 系统准备好进行智能推理
```

---

## ⏭️ 下一步行动

### 立即执行清单:

- [ ] **运行init_database.py** 初始化数据库
  ```bash
  cd backend && python3 init_database.py
  ```

- [ ] **验证数据库表** 通过psql确认表已创建
  ```bash
  psql -U postgres -d bidding_db -c "\dt"
  ```

- [ ] **准备测试PDF** 放入 `/Volumes/ssd/bidding-data/uploads/`

- [ ] **运行verify_new_parser.py** 测试解析准确率
  ```bash
  cd backend && python3 verify_new_parser.py
  ```

- [ ] **检查SSD存储** 验证所有文件已写入
  ```bash
  du -sh /Volumes/ssd/bidding-data/*
  ```

---

**准备执行这些步骤吗?** 我可以逐步指导您运行这些脚本。
