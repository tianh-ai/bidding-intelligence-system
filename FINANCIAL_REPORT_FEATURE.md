# 财务报告自动分离功能

## 功能说明

财务报告处理采用**特殊规则**:
- ✅ **不解析内容** - 财务数据复杂,仅保留原始PDF
- ✅ **自动年份识别** - OCR识别报告中的年份信息
- ✅ **按年分离** - 一个包含多年报告的PDF自动拆分为独立文件
- ✅ **分类存档** - 按年份存储到 `/archive/financial_reports/YYYY/`
- ✅ **数据库索引** - `financial_reports` 表记录所有已存档报告

## 使用场景

### 场景1: 上传多年财务报告
```
输入: 财务报告2021-2023.pdf (80页)
      - 2023年报告 (1-27页)
      - 2022年报告 (28-54页)
      - 2021年报告 (55-80页)

处理:
1. 自动识别年份范围
2. 分离为3个独立PDF
3. 存档到各年度目录

输出:
/archive/financial_reports/
  ├── 2023/
  │   └── 2025-12-14_财务报告_2023年财务报告.pdf (27页)
  ├── 2022/
  │   └── 2025-12-14_财务报告_2022年财务报告.pdf (27页)
  └── 2021/
      └── 2025-12-14_财务报告_2021年财务报告.pdf (26页)
```

### 场景2: 未识别到年份
```
输入: 未命名财务文件.pdf (无明确年份标识)

处理:
1. 未检测到年份
2. 保存到unknown目录

输出:
/archive/financial_reports/unknown/
  └── 2025-12-14_未命名财务文件.pdf
```

## API接口

### 1. 分离财务报告
```bash
POST /api/financial/split-report?file_id=xxx

Response:
{
  "status": "success",
  "file_id": "abc-123",
  "archived_files": [
    {
      "year": 2023,
      "archive_path": "/path/to/2023_report.pdf",
      "page_count": 27,
      "file_size": 1234567,
      "archived_at": "2025-12-14T10:30:00"
    },
    ...
  ],
  "total_files": 3,
  "years": [2023, 2022, 2021]
}
```

### 2. 获取存档报告
```bash
GET /api/financial/archived-reports/{file_id}

Response:
{
  "status": "success",
  "file_id": "abc-123",
  "reports": [
    {
      "year": 2023,
      "archive_path": "...",
      "page_count": 27,
      "file_size": 1234567,
      "archived_at": "2025-12-14 10:30:00"
    }
  ],
  "total": 3
}
```

### 3. 按年份查询
```bash
GET /api/financial/reports-by-year/2023

Response:
{
  "status": "success",
  "year": 2023,
  "reports": [
    {
      "file_id": "abc-123",
      "archive_path": "...",
      "original_filename": "财务报告2023.pdf",
      ...
    }
  ],
  "total": 5
}
```

### 4. 获取所有年份
```bash
GET /api/financial/years

Response:
{
  "status": "success",
  "years": [2023, 2022, 2021, 2020],
  "report_counts": {
    "2023": 5,
    "2022": 3,
    "2021": 2,
    "2020": 1
  },
  "total_years": 4
}
```

## 年份识别规则

系统使用以下正则模式识别年份:

1. **标准格式**: `2023年度财务报表` → 2023
2. **截至日期**: `截至2022年12月31日` → 2022
3. **报告类型**: `审计报告 2021年` → 2021
4. **完整日期**: `2020年6月30日` → 2020

识别范围: 2000-2030年

## 分离算法

```python
# 1. 逐页扫描识别年份
for page in pdf.pages:
    text = extract_text(page)
    year = detect_year(text)
    page_years.append((page_num, year))

# 2. 聚类为连续范围
年份变化 → 新报告开始
同一年份 → 扩展范围

# 3. 填充中间页
start_page=10, end_page=20
→ pages=[10,11,12,...,20]

# 4. 最小页数过滤
if page_count < 3:
    跳过(太短,可能是误识别)
```

## 数据库表结构

```sql
CREATE TABLE financial_reports (
    id UUID PRIMARY KEY,
    file_id UUID NOT NULL,           -- 关联原始上传文件
    year INTEGER,                     -- 报告年份(NULL=未识别)
    archive_path TEXT NOT NULL,       -- 存档路径
    page_count INTEGER NOT NULL,      -- 页数
    file_size BIGINT NOT NULL,        -- 文件大小(字节)
    archived_at TIMESTAMP,            -- 存档时间
    UNIQUE(file_id, year)             -- 同一文件同一年份唯一
);
```

## Python调用示例

```python
from engines.financial_report_splitter import FinancialReportSplitter

# 初始化
splitter = FinancialReportSplitter()

# 分离报告
file_path = "/path/to/financial_report.pdf"
file_id = "abc-123"
result = splitter.split_and_archive(file_path, file_id)

# 结果
for item in result:
    print(f"{item['year']}年: {item['page_count']}页")
    print(f"路径: {item['archive_path']}")

# 查询已存档报告
reports = splitter.get_archived_reports(file_id)
```

## 存储目录结构

```
/Volumes/ssd/bidding-data/archive/financial_reports/
├── 2023/
│   ├── 2025-12-14_公司A_2023年财务报告.pdf
│   ├── 2025-12-14_公司B_2023年财务报告.pdf
│   └── ...
├── 2022/
│   ├── 2025-12-14_公司A_2022年财务报告.pdf
│   └── ...
├── 2021/
│   └── ...
└── unknown/
    └── 2025-12-14_未识别年份.pdf
```

## 注意事项

1. **仅支持PDF** - DOCX/Excel财务文件需先转换为PDF
2. **年份识别准确性** - 依赖文档中明确的年份标识
3. **页数阈值** - 少于3页的范围会被忽略(避免误识别)
4. **存储空间** - 分离会产生多个文件副本,占用更多空间
5. **不解析内容** - 仅保留原始PDF,不提取财务数据

## 前端集成

```typescript
// 分离财务报告
const response = await fetch(
  `/api/financial/split-report?file_id=${fileId}`,
  { method: 'POST' }
);
const result = await response.json();

console.log(`分离为${result.total_files}个文件`);
result.archived_files.forEach(file => {
  console.log(`${file.year}年: ${file.page_count}页`);
});

// 获取年份列表
const yearsResponse = await fetch('/api/financial/years');
const years = await yearsResponse.json();

// 按年份查询
const reportsResponse = await fetch(`/api/financial/reports-by-year/2023`);
const reports = await reportsResponse.json();
```

## 故障排查

### 问题: 未检测到年份
**原因:** 文档中年份格式不标准
**解决:** 
- 检查PDF文本是否可提取
- 手动指定年份参数
- 添加新的识别模式到 `YEAR_PATTERNS`

### 问题: 分离不完整
**原因:** 年份在页面中间变化
**解决:**
- 调整页数阈值
- 检查聚类算法的范围填充逻辑

### 问题: 数据库插入失败
**原因:** UNIQUE约束冲突
**解决:**
- 使用 `ON CONFLICT ... DO UPDATE`
- 检查file_id和year组合是否重复
