# 文档和图片存储目录说明

## 存储根目录
```
/Volumes/ssd/bidding-data/
```

## 完整目录结构

### 1. 上传临时目录 (uploads/)
```
/Volumes/ssd/bidding-data/uploads/
├── temp/                    # 临时上传文件（处理后删除）
│   ├── {session_id}/       # 按会话ID分组
│   └── {file_id}.ext       # 原始上传文件
```
**用途:** 文件上传后的临时存储位置  
**生命周期:** 处理完成后自动删除  
**当前状态:** 动态变化

### 2. 解析中间目录 (parsed/)
```
/Volumes/ssd/bidding-data/parsed/
```
**用途:** 存储解析过程中的中间文件（如果需要）  
**当前状态:** 0个文件（未使用）

### 3. 归档目录 (archive/) ⭐ 主文档存储
```
/Volumes/ssd/bidding-data/archive/
├── {year}/                          # 按年份
│   └── {month}/                     # 按月份
│       ├── tender/                  # 招标文件
│       │   ├── 2025-12-14_项目名_招标文件_076251.docx
│       │   └── ...
│       ├── proposal/                # 投标文件
│       │   ├── 2025-12-14_项目名_投标文件_ce298b.docx
│       │   └── ...
│       └── reference/               # 参考资料
└── financial_reports/               # 财务报告（特殊处理）
    ├── 2023/
    ├── 2022/
    └── unknown/
```
**用途:** 永久存储已分类的文档  
**当前状态:** 多个文件

**文件命名规则:**
```
{日期}_{项目名}_{文档类型}_{hash6位}.{扩展名}

例: 2025-12-14_未命名项目_招标文件_076251.docx
    ↑          ↑        ↑         ↑
    日期      项目名   文档类型   MD5哈希(防重名)
```

### 4. 图片提取目录 (images/) ⭐ 新增功能
```
/Volumes/ssd/bidding-data/images/
├── {year}/                          # 按年份组织
│   ├── {file_id}/                   # 每个文件有独立目录
│   │   ├── 001_891553e0.png        # 图片编号_hash8位.格式
│   │   ├── 002_ce298bca.png
│   │   └── 003_cd848b05.png
│   └── {file_id2}/
│       └── ...
├── 2025/
│   └── 2142917b-af60-431f-9bb4-e14b7f9ed2da/
│       ├── 001_891553e0.png (1.7KB)
│       ├── 002_ce298bca.png (2.0KB)
│       └── 003_cd848b05.png (1.8KB)
└── 2024/
    └── ...
```
**用途:** 永久存储从文档中提取的原始图片  
**特点:**
- ✅ 保存原始图片，不进行OCR处理
- ✅ 按年份分目录，避免单目录文件过多
- ✅ 每个文件有独立目录，便于管理和删除
- ✅ MD5哈希用于文件名，防止重复
- ✅ 支持PNG、JPEG、GIF等多种格式

**图片命名规则:**
```
{序号3位}_{page页码}__{hash8位}.{格式}

例: 001_891553e0.png
    ↑   ↑
    序号 MD5哈希

或: 003_page05_cd848b05.png (PDF图片包含页码)
```

**数据库记录:**
- 表名: `extracted_images`
- 字段: id, file_id, image_path, image_number, page_number, format, size, width, height, hash
- API: `/api/images/{file_id}`, `/api/images/year/{year}`, `/api/images/download/{image_id}`

**当前状态:** 3张图片 (5.7KB)  
**测试文件:** test_with_images_20251214_063148.docx
示例: 2025-12-14_未命名项目_招标文件_076251.docx
```

### 4. 日志目录 (logs/)
```
/Volumes/ssd/bidding-data/logs/
├── bidding_system_YYYY-MM-DD_HH-MM-SS_{pid}.log  # 系统日志
└── errors_YYYY-MM-DD_HH-MM-SS_{pid}.log          # 错误日志
```
**当前状态:** 54个日志文件

## 图片处理说明

### 当前实现
**图片不单独存储**，而是采用以下处理方式:

1. **嵌入图片OCR识别** (parse_engine.py Line 180-220)
   - DOCX文件中的嵌入图片会被提取到内存
   - 使用 Tesseract OCR 识别图片中的文字
   - 识别结果直接追加到文本内容中
   - 格式: `[图片内容-1]\n{OCR文字}`

2. **存储位置**
   - ❌ 图片本身**不保存**到磁盘
   - ✅ OCR识别的文字保存到数据库 `files.content` 字段
   - ✅ 原始文档(包含图片)保存在 `archive/` 目录

### 示例
```
原始文件: 财务报告2023.docx (17MB，包含84张图片)
                    ↓
            OCR提取图片文字
                    ↓
存储结果:
1. archive/proposal/2025-12-14_未命名项目_投标文件.docx (17MB原文件)
2. files.content = "二、经审计的财务报告...[图片内容-1]\n资产负债表..." (122KB文字)
```

## 数据库存储

### uploaded_files 表
```sql
- id: 文件唯一ID
- filename: 原始文件名
- archive_path: 归档路径 (/Volumes/ssd/bidding-data/archive/...)
- status: 状态 (uploaded → parsing → archived → indexed)
- created_at: 上传时间
```

### files 表
```sql
- id: 关联uploaded_files.id
- filename: 语义文件名
- content: 提取的文本内容(包含OCR识别的图片文字) ← 图片文字在这里
- doc_type: 文档类型 (tender/proposal/reference)
```

### chapters 表
```sql
- file_id: 关联files.id
- chapter_number: 章节编号
- chapter_title: 章节标题
- content: 章节内容
```

## 如何查找文件

### 1. 通过API查询
```bash
# 获取文件列表
curl http://localhost:18888/api/files/list

# 获取文件详情
curl http://localhost:18888/api/files/{file_id}
```

### 2. 直接访问磁盘
```bash
# 查看所有归档文件
ls -lh /Volumes/ssd/bidding-data/archive/2025/12/*/

# 查找特定文件
find /Volumes/ssd/bidding-data/archive -name "*项目*.docx"
```

### 3. 数据库查询
```sql
-- 查看文件存储位置
SELECT filename, archive_path, LENGTH(content) as content_size
FROM uploaded_files uf
JOIN files f ON uf.id = f.id
ORDER BY uf.created_at DESC;
```

## 存储配置

### 代码配置 (backend/routers/files.py)
```python
UPLOAD_DIR = "/Volumes/ssd/bidding-data/uploads"
TEMP_DIR = "/Volumes/ssd/bidding-data/uploads/temp"
PARSED_DIR = "/Volumes/ssd/bidding-data/parsed"
ARCHIVE_DIR = "/Volumes/ssd/bidding-data/archive"
```

### 环境变量 (.env)
```bash
STORAGE_BASE=/Volumes/ssd/bidding-data  # 可选，当前硬编码
```

## 磁盘使用情况

```
目录                    文件数    总大小
uploads/temp             0        0
parsed/                  0        0
archive/                 4        28MB
├── tender/             2        29KB
└── proposal/           2        28MB
logs/                   54       未统计
```

## 注意事项

1. **图片不独立存储**: 只保存OCR文字，不保存图片文件本身
2. **临时文件自动清理**: temp目录中的文件处理后会删除
3. **归档文件永久保留**: archive目录的文件不会自动删除
4. **文件覆盖问题已修复**: 现在每个文件都有唯一的hash后缀
5. **财务报告特殊处理**: 按年份分离存储在 `financial_reports/` 目录

## 如需单独保存图片

如果需要保存原始图片文件，可以修改 `parse_engine.py`:

```python
# 创建图片目录
IMAGE_DIR = "/Volumes/ssd/bidding-data/images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# 保存图片
for image in doc.part.rels.values():
    if "image" in image.target_ref:
        image_data = image.target_part.blob
        image_path = f"{IMAGE_DIR}/{file_id}_{image_count}.png"
        with open(image_path, 'wb') as f:
            f.write(image_data)
```
