# 🔍 关系逻辑查询手册

> 展示如何使用SQL查询追踪verify_new_parser.py与init_database.py之间的完整数据流

---

## 📋 目录

- [基础查询](#基础查询)
- [生命周期追踪](#生命周期追踪)
- [验证准确率分析](#验证准确率分析)
- [知识库追踪](#知识库追踪)
- [关系完整性检查](#关系完整性检查)
- [性能分析](#性能分析)

---

## 基础查询

### 查询1: 查看所有表的结构和关系

```sql
-- 查看系统中的所有表
SELECT 
    table_name,
    ARRAY_AGG(column_name) as columns,
    ARRAY_AGG(data_type) as column_types
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;

/* 预期结果:
table_name              | columns                          | column_types
uploaded_files          | {id, file_name, ...}            | {uuid, varchar, ...}
parsing_results         | {id, file_id, result_json, ...} | {uuid, uuid, jsonb, ...}
knowledge_base          | {id, file_id, ...}              | {uuid, uuid, ...}
verification_tracking   | {id, file_id, ...}              | {uuid, uuid, ...}
relationships_documentation | {...}                       | {...}
*/
```

### 查询2: 查看表间的外键关系

```sql
-- 显示所有外键约束
SELECT 
    constraint_name,
    table_name,
    column_name,
    foreign_table_name,
    foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY table_name;

/* 预期结果:
constraint_name                      | table_name      | column_name | foreign_table_name | foreign_column_name
fk_parsing_results_file_id           | parsing_results | file_id     | uploaded_files     | id
fk_knowledge_base_file_id            | knowledge_base  | file_id     | uploaded_files     | id
fk_verification_tracking_file_id     | verification_tracking | file_id | uploaded_files | id
fk_verification_tracking_parsing_result_id | verification_tracking | parsing_result_id | parsing_results | id
*/
```

---

## 生命周期追踪

### 查询3: 单文件完整生命周期 (最重要)

```sql
-- 追踪单个文件从上传到知识库的完整流程
WITH file_lifecycle AS (
    SELECT 
        -- 文件基本信息
        uf.id as file_id,
        uf.file_name,
        uf.file_path,
        uf.upload_status,
        uf.parse_status,
        uf.created_at as upload_time,
        uf.updated_at as last_update_time,
        
        -- 解析结果信息
        pr.id as parsing_result_id,
        pr.chapter_count,
        pr.parsing_time,
        pr.parsing_status,
        pr.accuracy_score,
        pr.matched_toc_items,
        pr.total_toc_items,
        pr.created_at as parsing_time_created,
        
        -- 验证追踪信息
        vt.id as verification_tracking_id,
        vt.verification_status,
        vt.success_rate,
        vt.extracted_chapter_count,
        vt.verification_start_time,
        vt.verification_end_time,
        vt.verification_duration_seconds,
        
        -- 知识库统计
        COUNT(DISTINCT kb.id) as knowledge_items_count
        
    FROM uploaded_files uf
    LEFT JOIN parsing_results pr ON uf.id = pr.file_id
    LEFT JOIN verification_tracking vt ON pr.id = vt.parsing_result_id
    LEFT JOIN knowledge_base kb ON uf.id = kb.file_id
    
    WHERE uf.file_name = '招标.pdf'  -- 替换为实际文件名
    GROUP BY uf.id, pr.id, vt.id
)
SELECT 
    file_id,
    file_name,
    file_path,
    '上传' as step,
    upload_status,
    upload_time,
    NULL::FLOAT as duration_seconds
FROM file_lifecycle

UNION ALL

SELECT 
    file_id,
    file_name,
    file_path,
    '解析' as step,
    parse_status,
    parsing_time_created,
    parsing_time
FROM file_lifecycle

UNION ALL

SELECT 
    file_id,
    file_name,
    file_path,
    '验证' as step,
    verification_status,
    verification_end_time,
    verification_duration_seconds
FROM file_lifecycle

ORDER BY upload_time;

/* 预期结果:
file_id          | file_name  | file_path    | step | status      | time                | duration_seconds
uuid_1           | 招标.pdf    | /path/to/... | 上传 | completed   | 2024-01-15 10:30:00 | NULL
uuid_1           | 招标.pdf    | /path/to/... | 解析 | completed   | 2024-01-15 10:31:00 | 3.45
uuid_1           | 招标.pdf    | /path/to/... | 验证 | completed   | 2024-01-15 10:31:04 | 4.23
*/
```

### 查询4: 详细时间序列 (追踪数据流向)

```sql
-- 显示每个步骤的时间戳，用于追踪数据流向
SELECT 
    uf.file_name,
    uf.created_at as t1_upload_start,
    uf.updated_at as t2_upload_complete,
    EXTRACT(EPOCH FROM (uf.updated_at - uf.created_at)) as upload_duration_sec,
    
    pr.created_at as t3_parsing_result_created,
    pr.parsing_time as t4_parsing_duration_sec,
    
    vt.verification_start_time as t5_verification_start,
    vt.verification_end_time as t6_verification_end,
    vt.verification_duration_seconds as t7_verification_duration_sec,
    
    COUNT(DISTINCT kb.id) as t8_knowledge_items_extracted,
    MAX(kb.created_at) as t9_knowledge_creation_end,
    
    -- 总处理时间
    EXTRACT(EPOCH FROM (MAX(kb.created_at) - uf.created_at)) as total_processing_seconds
    
FROM uploaded_files uf
LEFT JOIN parsing_results pr ON uf.id = pr.file_id
LEFT JOIN verification_tracking vt ON pr.id = vt.parsing_result_id
LEFT JOIN knowledge_base kb ON uf.id = kb.file_id

GROUP BY uf.id, pr.id, vt.id
ORDER BY uf.created_at DESC;

/* 预期结果:
file_name    | t1_upload_start     | t2_upload_complete | t3_parsing_result_created | t4_parsing_duration_sec | t5_verification_start | t6_verification_end | t7_verification_duration_sec | t8_knowledge_items_extracted | total_processing_seconds
招标.pdf     | 10:30:00.000000     | 10:30:01.500000    | 10:31:00.000000           | 3.45                    | 10:31:00.100000       | 10:31:04.333000     | 4.23                         | 42                           | 64.33
*/
```

---

## 验证准确率分析

### 查询5: verify_new_parser准确率统计

```sql
-- 分析所有文件的verify验证准确率分布
SELECT 
    uf.file_name,
    pr.accuracy_score,
    pr.matched_toc_items,
    pr.total_toc_items,
    CASE 
        WHEN pr.accuracy_score >= 90 THEN 'Excellent (>=90%)'
        WHEN pr.accuracy_score >= 80 THEN 'Good (80-90%)'
        WHEN pr.accuracy_score >= 70 THEN 'Fair (70-80%)'
        ELSE 'Poor (<70%)'
    END as accuracy_grade,
    pr.parsing_time,
    COUNT(DISTINCT kb.id) as knowledge_items,
    vt.verification_status,
    pr.created_at
    
FROM uploaded_files uf
JOIN parsing_results pr ON uf.id = pr.file_id
LEFT JOIN verification_tracking vt ON pr.id = vt.parsing_result_id
LEFT JOIN knowledge_base kb ON uf.id = kb.file_id

GROUP BY uf.id, pr.id, vt.id
ORDER BY pr.accuracy_score DESC;

/* 预期结果:
file_name      | accuracy_score | matched_toc_items | total_toc_items | accuracy_grade  | parsing_time | knowledge_items | verification_status | created_at
招标-A.pdf     | 93.8           | 15                | 16              | Excellent       | 2.89         | 56              | completed           | 2024-01-15 10:31:00
招标-B.pdf     | 87.5           | 14                | 16              | Good            | 3.45         | 42              | completed           | 2024-01-15 10:32:00
招标-C.pdf     | 75.0           | 12                | 16              | Fair            | 4.12         | 35              | completed           | 2024-01-15 10:33:00
*/
```

### 查询6: TOC匹配详情 (从result_json提取)

```sql
-- 从result_json提取并显示每项TOC的匹配情况
SELECT 
    uf.file_name,
    jsonb_array_elements(pr.result_json -> 'toc_verification') as toc_verification_item,
    
    -- 从JSON提取字段
    (jsonb_array_elements(pr.result_json -> 'toc_verification')->>'toc_item') as toc_item,
    (jsonb_array_elements(pr.result_json -> 'toc_verification')->>'matched')::BOOLEAN as matched,
    (jsonb_array_elements(pr.result_json -> 'toc_verification')->>'similarity_score')::FLOAT as similarity_score
    
FROM uploaded_files uf
JOIN parsing_results pr ON uf.id = pr.file_id

WHERE uf.file_name = '招标.pdf'
ORDER BY matched DESC, similarity_score DESC;

/* 预期结果:
file_name  | toc_item                    | matched | similarity_score
招标.pdf   | 第一部分  投标邀请           | true    | 0.95
招标.pdf   | 一、投标说明                 | true    | 0.92
招标.pdf   | 二、投标人资格要求           | false   | 0.0
...
*/
```

### 查询7: 准确率对比分析

```sql
-- 对比parsing_time与accuracy_score的关系
SELECT 
    ROUND(pr.parsing_time)::INT as parsing_time_bucket,
    COUNT(*) as file_count,
    ROUND(AVG(pr.accuracy_score), 2) as avg_accuracy,
    MIN(pr.accuracy_score) as min_accuracy,
    MAX(pr.accuracy_score) as max_accuracy,
    STDDEV(pr.accuracy_score)::NUMERIC(5,2) as accuracy_stddev
    
FROM parsing_results pr
GROUP BY parsing_time_bucket
ORDER BY parsing_time_bucket;

/* 预期结果: 
parsing_time_bucket | file_count | avg_accuracy | min_accuracy | max_accuracy | accuracy_stddev
2                   | 5          | 91.25        | 87.5         | 93.8         | 2.34
3                   | 8          | 85.31        | 75.0         | 93.8         | 6.12
4                   | 3          | 79.17        | 75.0         | 87.5         | 5.89
*/
```

---

## 知识库追踪

### 查询8: 从文件到知识条项的追踪

```sql
-- 显示从特定文件提取的所有知识条项，包含来源追踪
SELECT 
    kb.id as knowledge_item_id,
    kb.title,
    kb.chapter_source,
    kb.extraction_confidence,
    kb.category,
    
    -- 来源文件信息
    uf.file_name,
    uf.file_id,
    
    -- 解析来源信息
    pr.accuracy_score as source_parsing_accuracy,
    pr.parsed_chapter_count,
    
    -- 创建时间链
    uf.created_at as file_upload_time,
    pr.created_at as parsing_complete_time,
    kb.created_at as knowledge_extraction_time,
    
    -- 时间差
    EXTRACT(EPOCH FROM (kb.created_at - uf.created_at))::INT as total_processing_seconds
    
FROM knowledge_base kb
JOIN uploaded_files uf ON kb.file_id = uf.id
LEFT JOIN parsing_results pr ON uf.id = pr.file_id

WHERE uf.file_name = '招标.pdf'
ORDER BY kb.chapter_source, kb.extraction_confidence DESC;

/* 预期结果:
knowledge_item_id | title           | chapter_source      | extraction_confidence | category  | source_parsing_accuracy | total_processing_seconds
uuid_k1           | 第一部分内容     | 第一部分  投标邀请   | 0.95                  | 招标条款  | 87.5                    | 64
uuid_k2           | 投标说明内容     | 一、投标说明       | 0.92                  | 招标条款  | 87.5                    | 65
...
*/
```

### 查询9: 知识条项统计 (按来源文件)

```sql
-- 统计每个文件提取了多少知识条项
SELECT 
    uf.file_name,
    COUNT(DISTINCT kb.id) as total_knowledge_items,
    COUNT(DISTINCT kb.category) as category_count,
    ARRAY_AGG(DISTINCT kb.category) as categories,
    ROUND(AVG(kb.extraction_confidence), 3) as avg_extraction_confidence,
    pr.parsing_time,
    pr.accuracy_score
    
FROM uploaded_files uf
LEFT JOIN knowledge_base kb ON uf.id = kb.file_id
LEFT JOIN parsing_results pr ON uf.id = pr.file_id

GROUP BY uf.id, pr.id
ORDER BY total_knowledge_items DESC;

/* 预期结果:
file_name      | total_knowledge_items | category_count | categories           | avg_extraction_confidence | parsing_time | accuracy_score
招标-A.pdf     | 56                    | 3              | {招标条款,技术规格,...} | 0.943                     | 2.89         | 93.8
招标-B.pdf     | 42                    | 2              | {招标条款,资格要求}   | 0.917                     | 3.45         | 87.5
*/
```

---

## 关系完整性检查

### 查询10: 孤立数据检查

```sql
-- 检查是否有孤立的parsing_results (没有对应的uploaded_files)
SELECT 
    pr.id,
    pr.file_id,
    pr.parsing_status,
    'ORPHANED parsing_result' as issue
    
FROM parsing_results pr
LEFT JOIN uploaded_files uf ON pr.file_id = uf.id
WHERE uf.id IS NULL;

-- 检查是否有孤立的knowledge_base
SELECT 
    kb.id,
    kb.file_id,
    'ORPHANED knowledge_item' as issue
    
FROM knowledge_base kb
LEFT JOIN uploaded_files uf ON kb.file_id = uf.id
WHERE uf.id IS NULL;

-- 检查是否有孤立的verification_tracking
SELECT 
    vt.id,
    vt.parsing_result_id,
    'ORPHANED verification_tracking' as issue
    
FROM verification_tracking vt
LEFT JOIN parsing_results pr ON vt.parsing_result_id = pr.id
WHERE pr.id IS NULL;
```

### 查询11: 关系完整性验证

```sql
-- 验证所有parsing_results都有对应的verification_tracking
WITH pr_without_vt AS (
    SELECT pr.id as parsing_result_id
    FROM parsing_results pr
    LEFT JOIN verification_tracking vt ON pr.id = vt.parsing_result_id
    WHERE vt.id IS NULL
)
SELECT 
    COUNT(*) as untracked_parsing_results,
    CASE 
        WHEN COUNT(*) = 0 THEN '✓ 完整 - 所有parsing_results都有tracking记录'
        ELSE '✗ 不完整 - ' || COUNT(*) || ' 个parsing_results缺少tracking'
    END as integrity_status
FROM pr_without_vt;

-- 验证所有knowledge_base都有有效的file_id
SELECT 
    COUNT(*) as orphaned_knowledge_items,
    CASE 
        WHEN COUNT(*) = 0 THEN '✓ 完整 - 所有knowledge_base都关联了文件'
        ELSE '✗ 不完整 - ' || COUNT(*) || ' 个knowledge_items缺少文件关联'
    END as integrity_status
FROM knowledge_base kb
LEFT JOIN uploaded_files uf ON kb.file_id = uf.id
WHERE uf.id IS NULL;
```

---

## 性能分析

### 查询12: 处理性能统计

```sql
-- 分析系统的处理性能
SELECT 
    COUNT(DISTINCT uf.id) as total_files_processed,
    COUNT(DISTINCT pr.id) as total_parsing_results,
    COUNT(DISTINCT kb.id) as total_knowledge_items,
    
    -- 时间统计
    ROUND(AVG(pr.parsing_time), 2) as avg_parsing_time_sec,
    ROUND(MIN(pr.parsing_time), 2) as min_parsing_time_sec,
    ROUND(MAX(pr.parsing_time), 2) as max_parsing_time_sec,
    
    -- 准确率统计
    ROUND(AVG(pr.accuracy_score), 2) as avg_accuracy_score,
    ROUND(MIN(pr.accuracy_score), 2) as min_accuracy_score,
    ROUND(MAX(pr.accuracy_score), 2) as max_accuracy_score,
    
    -- 知识提取统计
    ROUND(AVG(COUNT_KB.kb_count)) as avg_knowledge_items_per_file,
    ROUND(MIN(COUNT_KB.kb_count)) as min_knowledge_items_per_file,
    ROUND(MAX(COUNT_KB.kb_count)) as max_knowledge_items_per_file
    
FROM uploaded_files uf
LEFT JOIN parsing_results pr ON uf.id = pr.file_id
LEFT JOIN (
    SELECT file_id, COUNT(*) as kb_count
    FROM knowledge_base
    GROUP BY file_id
) COUNT_KB ON uf.id = COUNT_KB.file_id;

/* 预期结果:
total_files_processed | total_parsing_results | total_knowledge_items | avg_parsing_time_sec | avg_accuracy_score | avg_knowledge_items_per_file
42                    | 42                    | 1848                  | 3.42                 | 87.67              | 44
*/
```

### 查询13: 处理瓶颈分析

```sql
-- 找出处理最慢的文件
SELECT 
    uf.file_name,
    pr.parsing_time,
    pr.accuracy_score,
    COUNT(DISTINCT kb.id) as knowledge_items,
    ROUND((COUNT(DISTINCT kb.id) / pr.parsing_time), 2) as knowledge_items_per_second,
    pr.created_at
    
FROM uploaded_files uf
JOIN parsing_results pr ON uf.id = pr.file_id
LEFT JOIN knowledge_base kb ON uf.id = kb.file_id

GROUP BY uf.id, pr.id
ORDER BY pr.parsing_time DESC
LIMIT 10;

/* 预期结果:
file_name     | parsing_time | accuracy_score | knowledge_items | knowledge_items_per_second | created_at
大型招标-2024 | 8.92         | 75.0           | 128             | 14.35                     | 2024-01-15 11:00:00
中型招标-2024 | 6.45         | 87.5           | 96              | 14.89                     | 2024-01-15 11:01:00
*/
```

---

## 🎯 常用查询速查表

| 需求 | 查询编号 | 说明 |
|------|---------|------|
| 查看单文件完整流程 | 查询3 | 从上传到知识库提取 |
| 分析验证准确率 | 查询5/6 | verify结果分布 |
| 追踪知识来源 | 查询8 | 知识条项溯源 |
| 数据完整性检查 | 查询10/11 | 检测孤立记录 |
| 性能监控 | 查询12/13 | 识别处理瓶颈 |

---

## 📌 SQL执行建议

```bash
# 在PostgreSQL中执行这些查询
psql -h localhost -U postgres -d bidding_db

# 或使用文件执行
psql -h localhost -U postgres -d bidding_db -f queries.sql

# 使用 \watch 命令定时执行 (每2秒刷新一次)
\watch 2
```

