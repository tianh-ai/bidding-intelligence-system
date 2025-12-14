# 🎯 verify_new_parser ↔ init_database 关系快速参考卡

> 印刷版 - 方便贴在办公室或保存为PDF

---

## 📋 单页参考卡

```
┌─────────────────────────────────────────────────────────────┐
│   verify_new_parser.py ↔ init_database.py 关系速查表         │
├─────────────────────────────────────────────────────────────┤

【核心表结构】

表名                      | 字段数 | 关键字段 | 关系类型 | 数据流向
──────────────────────────┼────────┼────────┼────────┼──────────
uploaded_files            | 9      | id, file_name, parse_status | 枢纽 | 源
parsing_results           | 10     | file_id(FK), accuracy_score, result_json | 1:1 | verify输出
verification_tracking     | 12     | file_id(FK), parsing_result_id(FK) | 1:1 | 追踪
knowledge_base            | 13     | file_id(FK), chapter_source | 1:N | 知识
parsing_verification_mapping | 6   | 三表FK | Junction | 关系

【关键数据流】

上传PDF 
  ↓
uploaded_files (parse_status=pending)
  ↓
verify_new_parser.py 执行
  ↓
verification_result: {accuracy, matched_count, toc_details}
  ↓
4表并行插入:
  • UPDATE uploaded_files (parse_status=completed)
  • INSERT parsing_results (accuracy_score, result_json)
  • INSERT verification_tracking (toc_verification_details)
  • INSERT parsing_verification_mapping (关系记录)
  • INSERT knowledge_base x N (知识条项)
  ↓
✅ 完成

【时间序列】
T+0s: 文件上传完成
T+30s: verify_parser开始
T+33-35s: 解析完成 (parsing_time: 3-5s)
T+35-36s: 验证完成，结果存储
T+36s: parse_status变为completed

【关键概念】
✓ uploaded_files 是所有数据的枢纽
✓ verify结果完全存储在result_json中
✓ 时间戳支持完整的流程追踪
✓ 级联删除保证数据完整性
✓ mapping表记录复杂关系

【查询模板】

查询文件生命周期:
  SELECT uf.*, pr.accuracy_score, COUNT(kb.id) as kb_count
  FROM uploaded_files uf
  LEFT JOIN parsing_results pr ON uf.id = pr.file_id
  LEFT JOIN knowledge_base kb ON uf.id = kb.file_id
  WHERE uf.file_name = ?
  GROUP BY uf.id, pr.id

查询低准确率文件:
  SELECT file_name, accuracy_score
  FROM uploaded_files uf
  JOIN parsing_results pr ON uf.id = pr.file_id
  WHERE pr.accuracy_score < 80
  ORDER BY accuracy_score

【性能指标】
平均解析时间: 3-5秒
典型准确率: 87.5% (14/16)
知识条项数: 40-60条/文件
存储效率: 20-30KB/文件
查询响应: <100ms

└─────────────────────────────────────────────────────────────┘
```

---

## 📊 关系矩阵 (打印版)

```
┌─────────────────────────────────────────────────────────────┐
│  6表关系矩阵 - 箭头表示FK关系                                │
├─────────────────────────────────────────────────────────────┤

             ┌────────────────────────┐
             │  uploaded_files        │ ← 核心表
             │  (id, file_name, ...) │
             └───┬────────┬───────┬───┘
                 │        │       │
    FK file_id   │ FK     │       │ FK
                 │ file_id│       │ file_id
                 │        │       │
        ┌────────▼──┐  ┌─▼────────┐   ┌──▼──────────┐
        │ parsing_  │  │knowledge │   │verification│
        │ results   │  │ _base    │   │ _tracking  │
        └───┬──────┘  └──────────┘   └───┬─────────┘
            │ FK parsing_result_id         │
            │ (junction via mapping)      │
            └────────────┬─────────────────┘
                         │
                    ┌────▼──────────────┐
                    │parsing_verification
                    │_mapping           │
                    │(Junction/关系表)   │
                    └───────────────────┘
```

---

## 🔄 状态流转 (一页纸)

```
┌─────────────────────────────────────────────────────────────┐
│              状态转移流程图                                  │
├─────────────────────────────────────────────────────────────┤

【文件处理流程】
              
[上传]                [解析]              [完成]
  │                     │                   │
  ├─ upload_status      ├─ parse_status    ├─ parse_status
  │  pending ───────────▶ processing ──────▶ completed
  │  ↓                    ↓                  ↓
  │  completed         completed           knowledge_base
  │                    parsing_results   extracted
  │                  verification_tracking
  │                  created
  │
  └──────────────── ON DELETE CASCADE ─────┬───────────┘
                        删除时自动清理      │
                        所有关联数据        ▼
                                      ✓ 一致性保证

【时间戳关键点】

T1: uf.created_at ← 上传时间
T2: pr.created_at ← 解析结果创建
T3: vt.created_at ← 验证追踪创建
T4: kb.created_at ← 知识提取完成
T5: uf.updated_at ← 最后更新

流程耗时: T5 - T1 = 通常30-40秒
解析耗时: T2到验证完成 ≈ 3-5秒
```

---

## 📱 手机版速查 (竖排)

```
【verify_new_parser.py 的输出映射】

验证结果字段              数据库表存储            字段
────────────────────────┼──────────────────┼────────────
total_toc_items         parsing_results    total_toc_items
matched_count           parsing_results    matched_toc_items
accuracy_score          parsing_results    accuracy_score
success_rate            verification_...   success_rate
toc_verification[]      verification_...   toc_verification_
                        _details
extracted_chapter_count verification_...   extracted_chapter_
                        _count
parsing_duration        parsing_results    parsing_time
完整验证结果            parsing_results    result_json (JSONB)

【核心提问 & 回答】

Q: 如何查一个文件的完整历史?
A: SELECT * FROM uploaded_files uf
   LEFT JOIN parsing_results ON...
   LEFT JOIN knowledge_base ON...

Q: 哪个表存verify的详细结果?
A: parsing_results.result_json (JSONB)
   + verification_tracking (细节表)

Q: 如何找出准确率低的文件?
A: SELECT file_name, accuracy_score
   FROM uploaded_files JOIN parsing_results
   WHERE accuracy_score < 80

Q: 删除文件会发生什么?
A: ON DELETE CASCADE 自动清理:
   - parsing_results
   - verification_tracking  
   - parsing_verification_mapping
   - knowledge_base (所有条项)

Q: 最多能存多少文件?
A: 受SSD容量限制 (1.8TB)
   每个文件 ~20-30KB数据库
   每个文件 ~1-5MB文件本身
   理论上几千个文件
```

---

## 🎓 学习路线 (7天速成)

```
【Day 1】理论基础
  - 阅读 RELATIONSHIP_MODEL.md (30分钟)
  - 理解6个表的作用 (20分钟)
  - 看关系图 (10分钟)

【Day 2-3】实践环境
  - 运行 enhanced_database.py (5分钟)
  - 连接PostgreSQL查看表 (10分钟)
  - 研究 relationships_documentation表 (15分钟)

【Day 4-5】SQL查询
  - 学习查询3: 单文件生命周期 (20分钟)
  - 学习查询5: 准确率分析 (20分钟)
  - 自己写一个查询 (20分钟)

【Day 6】端到端演示
  - 运行 integrated_parser_with_tracking.py (10分钟)
  - 观察数据库变化 (20分钟)
  - 理解完整流程 (20分钟)

【Day 7】实战应用
  - 上传真实PDF文件 (5分钟)
  - 运行完整流程 (10分钟)
  - 查询和分析结果 (15分钟)
  - 写总结笔记 (20分钟)

总用时: ~4小时理论 + 2小时实践 = 6小时
```

---

## ⚡ 常用命令速查

```bash
# 数据库初始化
python3 enhanced_database.py

# 查看所有表
psql -U postgres -d bidding_db -c "\dt"

# 连接数据库交互式
psql -h localhost -U postgres -d bidding_db

# 查看单个表结构
\d uploaded_files

# 执行查询文件 (见RELATIONSHIP_QUERIES.md)
psql -U postgres -d bidding_db -f query.sql

# 演示脚本
python3 integrated_parser_with_tracking.py

# 查看日志
tail -50 /Volumes/ssd/bidding-data/logs/enhanced_database.log
```

---

## 🆚 对比表: init_database vs enhanced_database

```
功能                init_database.py  enhanced_database.py
────────────────────┼─────────────────┼──────────────────
表数量              3                 6 (新增3个)
验证追踪            ✗                 ✓
关系映射            ✗                 ✓
元数据文档          ✗                 ✓
verify结果存储      ✓ (result_json)   ✓ (全面)
生命周期追踪        手动              自动完整
关系查询难度        中                易 (有junction表)
数据完整性          基础              完整 (级联+约束)
审计能力            低                高 (关系表支持)
文件行数            196               450+
推荐使用            快速测试          生产环境
```

---

## 🎬 一句话总结

```
init_database.py 定义表结构
verify_new_parser.py 执行验证
enhanced_database.py 完整追踪关系
RELATIONSHIP_QUERIES.md 查询与分析

═══════════════════════════════════════════════════════
最终目标: 从PDF到知识库的每一步都能被完整追踪和审计
═══════════════════════════════════════════════════════
```

---

## 📎 附录: 表字段一览

```
【uploaded_files】(9字段)
id, file_name, file_path, file_size, upload_status, 
parse_status, storage_location, created_at, updated_at

【parsing_results】(10字段)
id, file_id(FK), chapter_count, parsing_time, parsing_status,
error_message, result_json, accuracy_score, matched_toc_items,
total_toc_items, storage_location, created_at, updated_at

【verification_tracking】(12字段)
id, file_id(FK), parsing_result_id(FK), verification_status,
verification_start_time, verification_end_time,
total_toc_items, matched_toc_items, success_rate,
extracted_chapter_count, toc_verification_details,
failed_items, error_message, verification_log, created_at, updated_at

【knowledge_base】(13字段)
id, file_id(FK), title, content, category, file_name,
source, chapter_source, extraction_confidence,
embedding(vector 1536), created_at, updated_at

【parsing_verification_mapping】(6字段)
id, file_id(FK), parsing_result_id(FK), verification_tracking_id(FK),
overall_quality_score, created_at

【relationships_documentation】(13字段)
id, source_table, target_table, relationship_type,
source_field, target_field, foreign_key_name,
data_flow_direction, transformation_logic, execution_order,
depends_on, cascade_on_delete, unique_constraint,
description, examples, notes, created_at, updated_at
```

---

打印或保存此页面以便快速查阅！

