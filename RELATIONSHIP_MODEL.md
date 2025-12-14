# 📊 verify_new_parser.py ↔ init_database.py 关系逻辑数据库

## 🎯 核心关系流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                  用户上传PDF文件                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │  File Upload Handler (files.py)│
         │  - 文件保存到SSD               │
         │  - 获得file_path和file_size    │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │   init_database.py作用域       │
         │   INSERT uploaded_files       │
         │   ────────────────────────────│
         │   id: UUID                     │
         │   file_name: "招标.pdf"         │
         │   file_path: SSD路径            │
         │   upload_status: "completed"   │
         │   parse_status: "pending"      │
         │   storage_location: SSD        │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  verify_new_parser.py作用域    │
         │  - ParseEngine.parse()         │
         │  - EnhancedChapterExtractor()  │
         │  - 验证提取的章节              │
         │  - 计算匹配率 (N/16)          │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │   init_database.py作用域       │
         │   UPDATE uploaded_files        │
         │   ────────────────────────────│
         │   parse_status: "completed"   │
         │   parsing_time: 3.45s         │
         │                                │
         │   INSERT parsing_results      │
         │   ────────────────────────────│
         │   file_id: FK -> uploaded_files
         │   chapter_count: 24           │
         │   parsing_status: "completed" │
         │   result_json: {...验证结果...}│
         │   accuracy_score: 87.5%       │
         └────────────┬───────────────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │   init_database.py作用域       │
         │   INSERT knowledge_base        │
         │   ────────────────────────────│
         │   file_id: FK -> uploaded_files
         │   content: 提取的条款内容      │
         │   embedding: OpenAI向量       │
         │   (多条记录)                    │
         └────────────┬───────────────────┘
                      │
                      ▼
                   ✅ 完成
```

---

## 🔗 详细关系矩阵

### **关键的数据流关系**

| 序号 | 来源脚本 | 操作类型 | 目标表 | 依赖关系 | 时间顺序 |
|------|---------|---------|--------|---------|---------|
| 1️⃣ | init_database.py | CREATE TABLE | uploaded_files | 无 | 最早 |
| 2️⃣ | init_database.py | CREATE TABLE | parsing_results | FK → uploaded_files | 1之后 |
| 3️⃣ | init_database.py | CREATE TABLE | knowledge_base | FK → uploaded_files | 1之后 |
| 4️⃣ | files.py (external) | INSERT | uploaded_files | 无 | 用户上传时 |
| 5️⃣ | verify_new_parser.py | VALIDATE | (无直接DB操作) | 依赖: uploaded_files | 上传后 |
| 6️⃣ | tasks.py (external) | UPDATE | uploaded_files | 依赖: uploaded_files ID | 验证后 |
| 7️⃣ | tasks.py (external) | INSERT | parsing_results | FK → uploaded_files | 验证完成后 |
| 8️⃣ | tasks.py (external) | INSERT | knowledge_base | FK → uploaded_files | 最后 |

---

## 📊 关系逻辑数据模型

### **表1: uploaded_files (核心枢纽表)**

```
┌────────────────────────────────────────────────────────────┐
│              uploaded_files (文件追踪表)                     │
│              ▲ 被其他表引用 (FK来源)                        │
├────────────────────────────────────────────────────────────┤
│ 字段                    │ 类型      │ 说明                  │
├────────────────────────────────────────────────────────────┤
│ id (PK)                 │ UUID      │ 主键                  │
│ file_name              │ VARCHAR   │ 原始文件名             │
│ file_path              │ TEXT      │ SSD完整路径            │
│ file_size              │ BIGINT    │ 文件大小(字节)         │
│ upload_status          │ TEXT      │ pending/completed     │
│ parse_status           │ TEXT      │ pending/processing/completed
│ storage_location       │ TEXT      │ 默认=/Volumes/ssd/... │
│ created_at             │ TIMESTAMPTZ │ 上传时间           │
│ updated_at             │ TIMESTAMPTZ │ 最后更新时间       │
└────────────────────────────────────────────────────────────┘

生命周期状态转移:
┌─────────┐     ┌───────────┐     ┌─────────────┐
│pending  │ ──> │processing │ ──> │completed    │
│(上传)   │     │(解析中)   │     │(完成)       │
└─────────┘     └───────────┘     └─────────────┘
```

### **表2: parsing_results (解析结果表)**

```
┌────────────────────────────────────────────────────────────┐
│           parsing_results (解析验证结果表)                   │
│           ← FK: file_id REFERENCES uploaded_files(id)      │
├────────────────────────────────────────────────────────────┤
│ 字段                    │ 类型      │ 说明                  │
├────────────────────────────────────────────────────────────┤
│ id (PK)                 │ UUID      │ 主键                  │
│ file_id (FK)            │ UUID      │ 关联文件ID            │
│ chapter_count           │ INTEGER   │ 提取的章节数(24)      │
│ parsing_time            │ FLOAT     │ 解析耗时(秒)          │
│ parsing_status          │ TEXT      │ completed/failed      │
│ error_message           │ TEXT      │ 失败时错误信息        │
│ result_json             │ JSONB     │ 解析结果详情          │
│   ├─ chapters[]         │           │ 章节数组              │
│   ├─ accuracy_score     │ FLOAT     │ verify结果(87.5%)     │
│   ├─ matched_chapters   │ INTEGER   │ 匹配数(14/16)        │
│   ├─ extraction_quality │ TEXT      │ good/fair/poor        │
│   └─ verification_details
│                         │ JSONB     │ 每项TOC的匹配详情     │
│ storage_location        │ TEXT      │ 解析文件保存路径       │
│ created_at              │ TIMESTAMPTZ │ 结果生成时间       │
└────────────────────────────────────────────────────────────┘

重要: result_json 字段存储 verify_new_parser.py 的全部验证结果
```

### **表3: knowledge_base (知识库表)**

```
┌────────────────────────────────────────────────────────────┐
│             knowledge_base (知识库表)                        │
│             ← FK: file_id REFERENCES uploaded_files(id)    │
├────────────────────────────────────────────────────────────┤
│ 字段                    │ 类型      │ 说明                  │
├────────────────────────────────────────────────────────────┤
│ id (PK)                 │ UUID      │ 主键                  │
│ file_id (FK)            │ UUID      │ 来源文件ID            │
│ title                   │ VARCHAR   │ 条款标题              │
│ content                 │ TEXT      │ 完整内容              │
│ category                │ VARCHAR   │ 分类(资格/条件/技术..) │
│ file_name               │ VARCHAR   │ 来源文件名            │
│ source                  │ VARCHAR   │ 来源标记              │
│ embedding               │ vector(1536) │ OpenAI语义向量    │
│ chapter_source          │ VARCHAR   │ 来自哪个章节(第一部分) │
│ extraction_confidence   │ FLOAT     │ 提取置信度(0-1)      │
│ created_at              │ TIMESTAMPTZ │ 创建时间           │
│ updated_at              │ TIMESTAMPTZ │ 更新时间           │
└────────────────────────────────────────────────────────────┘

说明: 多条记录关联同一个file_id (1:N关系)
      每条记录代表从PDF提取的一个知识条项
```

---

## 🔄 数据流关键转换点

### **关键点1: verify_new_parser.py 的验证结果**

```python
# verify_new_parser.py 的输出数据结构
verification_result = {
    "file_path": "/Volumes/ssd/bidding-data/uploads/招标.pdf",
    "file_id": "uuid-of-uploaded-file",
    
    # verify_new_parser.py 计算的核心结果
    "total_toc_items": 16,
    "matched_count": 14,
    "success_rate": 87.5,  # (14/16)*100
    
    # 详细匹配结果
    "toc_verification": [
        {
            "toc_item": "第一部分  投标邀请",
            "matched": True,
            "extracted_chapter": "第一部分",
            "similarity_score": 0.95
        },
        {
            "toc_item": "一、投标说明",
            "matched": True,
            "extracted_chapter": "一",
            "similarity_score": 0.92
        },
        {
            "toc_item": "二、投标人资格要求",
            "matched": False,
            "extracted_chapter": None,
            "similarity_score": 0.0
        },
        # ... 13项其他结果
    ],
    
    # 章节提取统计
    "chapter_extraction_stats": {
        "total_chapters_extracted": 24,
        "chapter_levels": {
            "level_1": 6,  # 第一、第二等
            "level_2": 18  # 一、二、三等
        }
    }
}
```

### **关键点2: 数据流转换**

```
verify_new_parser.py 输出
         ↓
    verification_result
         ↓
  转换为SQL操作:
    ├─ UPDATE uploaded_files
    │  SET parse_status = "completed"
    │  WHERE id = file_id
    │
    ├─ INSERT INTO parsing_results
    │  VALUES (
    │    file_id,
    │    chapter_count = 24,
    │    parsing_status = "completed",
    │    result_json = verification_result (完整JSON),
    │    accuracy_score = 87.5,
    │    ...
    │  )
    │
    └─ INSERT INTO knowledge_base (多条)
       FOR EACH extracted_chapter:
         INSERT INTO knowledge_base (
           file_id,
           chapter_source = extracted_chapter.title,
           extraction_confidence = similarity_score,
           ...
         )
```

---

## 📈 完整的时间序列关系

```
时间轴:

T0: 系统初始化
    ├─ init_database.py 运行
    └─ 3个表被创建 (空表状态)

T1: 用户上传PDF (t1_timestamp)
    ├─ files.py 处理上传
    ├─ 文件保存到 /Volumes/ssd/bidding-data/uploads/
    └─ INSERT uploaded_files
       id = uuid_1
       file_name = "招标.pdf"
       upload_status = "completed"
       parse_status = "pending"  ← 关键状态
       created_at = t1_timestamp

T2: 解析引擎启动 (t2_timestamp)
    ├─ 触发 verify_new_parser.py
    ├─ 从 uploaded_files 读取: id = uuid_1, file_path
    ├─ ParseEngine.parse(file_path)
    ├─ EnhancedChapterExtractor.extract_chapters()
    └─ 生成 verification_result

T3: 验证完成 (t3_timestamp, 通常 t3 = t2 + 3~5秒)
    ├─ UPDATE uploaded_files
    │  SET parse_status = "completed",
    │      updated_at = t3_timestamp
    │  WHERE id = uuid_1
    │
    ├─ INSERT parsing_results
    │  id = uuid_2
    │  file_id = uuid_1  ← 外键关联
    │  chapter_count = 24
    │  parsing_time = (t3 - t2)
    │  result_json = verification_result
    │  created_at = t3_timestamp
    │
    └─ 生成N条 INSERT knowledge_base
       FOR EACH chapter IN extracted_chapters:
         INSERT INTO knowledge_base
           file_id = uuid_1  ← 外键关联
           chapter_source = chapter.title
           extraction_confidence = similarity_score
           created_at = t3_timestamp
```

---

## 🔍 关系查询示例

### **查询1: 追踪单个文件的完整生命周期**

```sql
-- 查询文件 uuid_1 的完整处理流程
SELECT 
    uf.id as file_id,
    uf.file_name,
    uf.upload_status,
    uf.parse_status,
    uf.created_at as upload_time,
    uf.updated_at as last_updated,
    
    -- 关联的解析结果
    pr.id as result_id,
    pr.chapter_count,
    pr.parsing_time,
    pr.parsing_status,
    pr.result_json->>'accuracy_score' as accuracy_score,
    pr.created_at as parse_complete_time,
    
    -- 关联的知识库条目数
    COUNT(DISTINCT kb.id) as knowledge_items_count
    
FROM uploaded_files uf
LEFT JOIN parsing_results pr ON uf.id = pr.file_id
LEFT JOIN knowledge_base kb ON uf.id = kb.file_id

WHERE uf.id = 'uuid_1'
GROUP BY uf.id, pr.id;

/* 预期输出:
file_id          | file_name      | upload_status | parse_status | ...
uuid_1           | 招标.pdf        | completed     | completed    | ...
result_id        | chapter_count  | parsing_time  | accuracy_score
uuid_2           | 24             | 3.45          | 87.5         | ...
knowledge_items_count
42                (从PDF提取的42个知识条项)
*/
```

### **查询2: verify_new_parser 准确率分析**

```sql
-- 分析所有文件的解析准确率分布
SELECT 
    uf.file_name,
    pr.result_json->>'success_rate' as verify_success_rate,
    pr.result_json->>'total_toc_items' as total_toc_items,
    pr.result_json->>'matched_count' as matched_toc_items,
    pr.parsing_time,
    COUNT(kb.id) as extracted_knowledge_count,
    pr.created_at
    
FROM parsing_results pr
JOIN uploaded_files uf ON pr.file_id = uf.id
LEFT JOIN knowledge_base kb ON pr.file_id = kb.file_id

GROUP BY pr.id, uf.id
ORDER BY pr.created_at DESC;

/* 预期输出:
file_name     | verify_success_rate | total_toc_items | matched_toc_items | parsing_time | extracted_knowledge_count
招标.pdf      | 87.5                | 16              | 14                | 3.45         | 42
2024-招标.pdf | 93.8                | 16              | 15                | 2.89         | 56
...
*/
```

### **查询3: 追踪验证失败的文件**

```sql
-- 找出解析失败或准确率低的文件
SELECT 
    uf.file_name,
    uf.upload_status,
    pr.parsing_status,
    COALESCE(pr.error_message, 
             'Success rate < 80%: ' || pr.result_json->>'success_rate' || '%'
    ) as issue_details,
    pr.result_json->>'matched_count' || '/' || pr.result_json->>'total_toc_items' as match_result,
    uf.updated_at
    
FROM uploaded_files uf
LEFT JOIN parsing_results pr ON uf.id = pr.file_id

WHERE pr.parsing_status != 'completed'
   OR (pr.result_json->>'success_rate')::FLOAT < 80

ORDER BY uf.updated_at DESC;
```

### **查询4: 知识库与源文件关联**

```sql
-- 查看从特定文件提取的所有知识条项
SELECT 
    kb.id,
    kb.title,
    kb.content,
    kb.category,
    kb.chapter_source,
    kb.extraction_confidence,
    uf.file_name,
    pr.result_json->>'success_rate' as source_accuracy
    
FROM knowledge_base kb
JOIN uploaded_files uf ON kb.file_id = uf.id
LEFT JOIN parsing_results pr ON kb.file_id = pr.file_id

WHERE uf.file_name = '招标.pdf'
ORDER BY kb.chapter_source, kb.extraction_confidence DESC;
```

---

## 🔐 关系完整性约束

### **外键约束**

```sql
-- parsing_results 表
ALTER TABLE parsing_results 
ADD CONSTRAINT fk_parsing_results_file_id 
FOREIGN KEY (file_id) 
REFERENCES uploaded_files(id) 
ON DELETE CASCADE;  -- 删除文件时自动删除解析结果

-- knowledge_base 表
ALTER TABLE knowledge_base 
ADD CONSTRAINT fk_knowledge_base_file_id 
FOREIGN KEY (file_id) 
REFERENCES uploaded_files(id) 
ON DELETE CASCADE;  -- 删除文件时自动删除知识条项
```

### **删除级联关系图**

```
删除 uploaded_files (id = uuid_1)
    ├─ 自动删除 parsing_results (所有 file_id = uuid_1 的记录)
    ├─ 自动删除 knowledge_base (所有 file_id = uuid_1 的记录)
    └─ 物理删除 SSD 上的文件 (/Volumes/ssd/bidding-data/uploads/...)
```

---

## 📋 关系总结表

| 关系类型 | 来源 | 目标 | 关联字段 | 数据流向 | 转换逻辑 |
|---------|------|------|---------|---------|---------|
| **1:N (一对多)** | uploaded_files | parsing_results | file_id | 单向 | 一个文件 → 一条解析记录 |
| **1:N (一对多)** | uploaded_files | knowledge_base | file_id | 单向 | 一个文件 → 多条知识条项 |
| **1:1 (一对一)** | uploaded_files | file_path(SSD) | storage_location | 双向 | 文件ID ↔ 文件路径 |
| **N:1 (多对一)** | parsing_results | uploaded_files | file_id(FK) | 单向 | 多个结果 ← 单个文件 |
| **验证数据流** | verify_new_parser | parsing_results | result_json | 单向 | 验证结果 → JSON存储 |
| **知识提取流** | parsing_results | knowledge_base | file_id + chapter | 单向 | 解析结果 → 知识条项 |

---

## 🎯 核心设计原则

1. **uploaded_files 是枢纽表**
   - 所有数据都通过 file_id 关联回源文件
   - 支持完整的数据溯源

2. **verify_new_parser 结果完全存储**
   - result_json 字段存储完整的验证详情
   - 支持后续审计和重新分析

3. **时间序列可追踪**
   - 每个表都有 created_at/updated_at
   - 支持分析处理时间和流程

4. **级联删除保证一致性**
   - 删除文件自动清理所有关联数据
   - 防止孤立记录

5. **灵活的 JSONB 存储**
   - 不需要频繁修改schema
   - 支持存储验证细节和错误信息

