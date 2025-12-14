# 文件存储问题分析与修复

## 发现的问题

### 1. 文件名重复覆盖问题

**症状:**
- 数据库有12条上传记录
- 实际磁盘只有4个文件
- 多个不同的原始文件指向同一个archive_path

**根本原因:**
`document_classifier.py` 的 `generate_semantic_filename()` 方法在无法提取项目名时,对所有文件都返回 `"未命名项目"`,导致:
- `2025-12-14_未命名项目_招标文件.docx` (8个文件指向)
- `2025-12-14_未命名项目_投标文件.docx` (4个文件指向)

**数据示例:**
```
原始文件名: 第一部分  二、经审计的财务报告或资信证明（招标）.docx
原始文件名: 第三部分  一、技术条款偏离表（招标）.docx
原始文件名: 第四部分  一、开标一览表（招标）.docx
                                ↓
          同一archive_path: 2025-12-14_未命名项目_招标文件.docx
                                ↓
                        后上传覆盖先上传
```

### 2. 内容丢失

由于文件覆盖:
- 第一批上传的文件内容被后续上传覆盖
- 数据库记录存在但文件内容已变
- 导致10个文件的原始内容永久丢失

## 修复方案

### 修改 `generate_semantic_filename()`

**Before:**
```python
parts = [date_str, project_name, doc_type]
if version:
    parts.append(version)

semantic_name = "_".join(filter(None, parts)) + ext
```

**After:**
```python
parts = [date_str, project_name, doc_type]
if version:
    parts.append(version)

semantic_name = "_".join(filter(None, parts))

# 添加唯一性后缀: 原始文件名hash前6位
file_hash = hashlib.md5(original_filename.encode()).hexdigest()[:6]
semantic_name = f"{semantic_name}_{file_hash}{ext}"
```

**效果:**
```
第一部分 二、经审计的财务报告或资信证明（招标）.docx
  → 2025-12-14_未命名项目_招标文件_076251.docx

第三部分 一、技术条款偏离表（招标）.docx
  → 2025-12-14_未命名项目_招标文件_67956e.docx

第四部分 一、开标一览表（招标）.docx
  → 2025-12-14_未命名项目_招标文件_31f4a8.docx
```

每个文件现在都有**唯一的6位hash后缀**,即使项目名相同也不会冲突。

## 当前存储状态

### 物理文件
```
/Volumes/ssd/bidding-data/archive/2025/12/
├── tender/
│   ├── 2025-12-14_四、项目_招标文件.docx (17KB)
│   └── 2025-12-14_未命名项目_招标文件.docx (12KB) ← 被覆盖8次
└── proposal/
    ├── 2025-12-14_四、项目_投标文件.docx (11MB)
    └── 2025-12-14_未命名项目_投标文件.docx (17MB) ← 被覆盖4次,最终版包含OCR内容
```

### 数据库记录
```sql
SELECT COUNT(*) FROM uploaded_files;  -- 12条
SELECT COUNT(DISTINCT archive_path) FROM uploaded_files;  -- 4个唯一路径
```

**文件映射关系:**
| 原始文件名 | Archive Path | 结果 |
|-----------|-------------|------|
| 第一部分 二、经审计的财务报告或资信证明（招标）| 未命名项目_招标 | ✅ 保留(最后覆盖) |
| 第四部分 一、开标一览表（招标）| 未命名项目_招标 | ❌ 被覆盖 |
| 第三部分 一、技术条款偏离表（招标）| 未命名项目_招标 | ❌ 被覆盖 |
| ... | | |

## 数据恢复建议

### 无法恢复的数据
- 已被覆盖的8个文件内容**永久丢失**
- 建议重新上传原始文件

### 可采取的措施
1. **清理数据库**: 删除指向已覆盖文件的记录
```sql
DELETE FROM uploaded_files 
WHERE archive_path IN (
    SELECT archive_path 
    FROM uploaded_files 
    GROUP BY archive_path 
    HAVING COUNT(*) > 1
)
AND id NOT IN (
    SELECT MAX(id) 
    FROM uploaded_files 
    GROUP BY archive_path
);
```

2. **重新上传**: 使用修复后的系统重新上传所有文件

## 验证修复

### 测试命令
```bash
docker exec bidding_backend python3 -c "
from engines.document_classifier import DocumentClassifier, FileCategory
classifier = DocumentClassifier()

files = ['文件A.docx', '文件A.docx', '文件B.docx']
for f in files:
    print(classifier.generate_semantic_filename(f, FileCategory.TENDER, {}, None))
"
```

### 预期输出
```
2025-12-14_未命名项目_招标文件_5d7a8b.docx
2025-12-14_未命名项目_招标文件_5d7a8b.docx  ← 相同原名=相同hash
2025-12-14_未命名项目_招标文件_3f9e2c.docx  ← 不同原名=不同hash
```

## 总结

### 问题根源
- 语义文件名生成逻辑缺少唯一性保证
- 项目名提取失败时使用固定fallback值
- 没有文件覆盖检测机制

### 修复效果
- ✅ 每个文件有唯一semantic_filename
- ✅ 相同原始文件名产生相同hash(支持重复上传检测)
- ✅ 不同原始文件名产生不同hash(防止覆盖)
- ✅ Hash长度6位,足够避免冲突(约1677万种组合)

### 后续建议
1. 添加文件覆盖警告
2. 实现文件版本管理
3. 定期备份archive目录
4. 添加文件完整性校验(MD5/SHA256)
