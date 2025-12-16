# 存储路径标准化规范

**版本**: 1.0.0  
**日期**: 2025-12-16  
**状态**: ⚠️ **发现不一致问题，需要修复**

---

## 📋 执行摘要

### 🚨 核心问题

系统存在**双重路径标准**导致的不一致问题：

| 位置 | 使用路径 | 状态 |
|------|---------|------|
| **数据库 (uploaded_files)** | `/Volumes/ssd/bidding-data/archive/...` | ❌ 容器无法直接访问 |
| **Docker容器内部** | `/app/data/archive/...` | ✅ 实际可访问路径 |
| **配置文件 (config.py)** | `/app/data/uploads` | ✅ 正确 |
| **MCP测试** | 使用数据库路径失败 | ❌ FileNotFoundError |

**影响**: 
- MCP document-parser 无法访问数据库中记录的文件路径
- 需要手动转换路径才能访问文件
- 潜在的跨环境兼容性问题

---

## 🏗️ 路径架构总览

### 1. 物理存储层 (宿主机)

**SSD挂载点**: `/Volumes/ssd/bidding-data/`

```
/Volumes/ssd/bidding-data/
├── uploads/          # 上传临时文件
│   └── temp/         # 会话临时目录
├── parsed/           # 解析中间结果
├── archive/          # 归档文件（长期存储）
│   ├── 2025/
│   │   └── 12/
│   │       ├── tender/           # 招标文件
│   │       ├── proposal/         # 投标文件
│   │       ├── reference/        # 参考文件
│   │       └── financial_reports/# 财务报告
├── images/           # 提取的图片
│   └── 2025/
│       └── {file_id}/
├── logs/             # 日志文件
├── db/               # 数据库备份（未使用）
└── .DS_Store
```

### 2. Docker容器层

**挂载配置** (`docker-compose.yml`):
```yaml
volumes:
  - /Volumes/ssd/bidding-data:/app/data
```

**容器内路径**: `/app/data/`

```
/app/data/              # 对应宿主机 /Volumes/ssd/bidding-data/
├── uploads/
├── parsed/
├── archive/            # 归档文件
├── images/             # 图片存储
└── logs/
```

### 3. 应用配置层

**配置文件**: `backend/core/config.py`

```python
# ✅ 正确配置
UPLOAD_DIR: str = "/app/data/uploads"
IMAGE_STORAGE_DIR: str = "/app/data/images"

# ❌ 问题：派生路径计算
ARCHIVE_DIR = os.path.join(os.path.dirname(UPLOAD_DIR), "archive")
# 结果: /app/data/archive  ✅
```

### 4. 数据库存储层

**表**: `uploaded_files`

**路径字段**:
- `file_path`: 文件原始/当前路径
- `archive_path`: 归档后的路径

**当前存储格式** (❌ 错误):
```sql
file_path     = '/Volumes/ssd/bidding-data/archive/2025/12/proposal/...'
archive_path  = '/Volumes/ssd/bidding-data/archive/2025/12/proposal/...'
```

**应该存储的格式** (✅ 正确):
```sql
file_path     = '/app/data/archive/2025/12/proposal/...'
archive_path  = '/app/data/archive/2025/12/proposal/...'
```

---

## ⚙️ 路径映射关系

### 宿主机 ↔ 容器映射

| 宿主机路径 | 容器路径 | 用途 |
|-----------|---------|------|
| `/Volumes/ssd/bidding-data/uploads/` | `/app/data/uploads/` | 文件上传 |
| `/Volumes/ssd/bidding-data/parsed/` | `/app/data/parsed/` | 解析结果 |
| `/Volumes/ssd/bidding-data/archive/` | `/app/data/archive/` | 归档文件 |
| `/Volumes/ssd/bidding-data/images/` | `/app/data/images/` | 图片存储 |
| `/Volumes/ssd/bidding-data/logs/` | `/app/data/logs/` | 日志文件 |

### 数据库路径转换

**当前需要手动转换**:
```python
# 数据库路径
db_path = "/Volumes/ssd/bidding-data/archive/2025/12/proposal/file.docx"

# 转换为容器路径
container_path = db_path.replace("/Volumes/ssd/bidding-data", "/app/data")
# => "/app/data/archive/2025/12/proposal/file.docx"
```

---

## 📝 标准化规范

### 规范1: 数据库存储路径必须使用容器路径

**强制要求**:
- ✅ 所有写入数据库的路径必须使用 `/app/data/` 前缀
- ❌ 禁止使用 `/Volumes/ssd/bidding-data/` 前缀

**理由**:
1. 容器内应用只能访问 `/app/data/`
2. 跨环境兼容性（本地/生产/测试环境）
3. Docker是唯一运行环境

### 规范2: 配置文件路径标准

**backend/core/config.py**:
```python
# ✅ 正确：使用容器内绝对路径
UPLOAD_DIR: str = "/app/data/uploads"
IMAGE_STORAGE_DIR: str = "/app/data/images"

# ❌ 错误：使用宿主机路径
UPLOAD_DIR: str = "/Volumes/ssd/bidding-data/uploads"  # 不要这样！
```

### 规范3: 路径构建标准

**推荐模式**:
```python
from pathlib import Path
from core.config import get_settings

settings = get_settings()
base_data_dir = Path("/app/data")

# ✅ 方法1: 直接使用配置
upload_dir = Path(settings.UPLOAD_DIR)

# ✅ 方法2: 基于基准路径构建
archive_dir = base_data_dir / "archive"
image_dir = base_data_dir / "images"

# ❌ 错误：硬编码宿主机路径
archive_dir = Path("/Volumes/ssd/bidding-data/archive")
```

### 规范4: 归档路径结构

**标准格式**:
```
/app/data/archive/{YYYY}/{MM}/{category}/{semantic_filename}

示例:
/app/data/archive/2025/12/proposal/2025-12-14_项目名称_投标文件_abc123.docx
/app/data/archive/2025/12/tender/2025-12-14_项目名称_招标文件_def456.pdf
```

**分类目录** (`category`):
- `tender` - 招标文件
- `proposal` - 投标文件
- `reference` - 参考文件
- `financial_reports` - 财务报告
- `certificate` - 证件资质
- `other` - 其他文件

### 规范5: 图片存储路径

**标准格式**:
```
/app/data/images/{YYYY}/{file_id}/image_{index}.{ext}

示例:
/app/data/images/2025/6e8908c6-88fe-4bbc-8513-4f47c93c9fe7/image_001.jpg
/app/data/images/2025/6e8908c6-88fe-4bbc-8513-4f47c93c9fe7/image_002.png
```

---

## 🔧 代码实现标准

### 文件上传路由 (`backend/routers/files.py`)

```python
from core.config import get_settings

settings = get_settings()

# ✅ 正确：使用配置的路径
UPLOAD_DIR = settings.upload_path  # /app/data/uploads
TEMP_DIR = os.path.join(UPLOAD_DIR, "temp")
PARSED_DIR = os.path.join(os.path.dirname(UPLOAD_DIR), "parsed")
ARCHIVE_DIR = os.path.join(os.path.dirname(UPLOAD_DIR), "archive")

# 归档文件
archive_path = os.path.join(
    ARCHIVE_DIR,
    str(year),
    f"{month:02d}",
    category,
    semantic_filename
)
# 结果: /app/data/archive/2025/12/proposal/file.docx ✅

# ✅ 存入数据库时使用容器路径
db.execute(
    "UPDATE uploaded_files SET archive_path = %s WHERE id = %s",
    (archive_path, file_id)  # archive_path 已是 /app/data/... 格式
)
```

### 图片提取 (`skills/image_processor.py`)

```python
from core.config import get_settings

settings = get_settings()

# ✅ 正确：使用配置的图片路径
image_base = Path(settings.image_storage_path)  # /app/data/images
file_image_dir = image_base / str(year) / str(file_id)
file_image_dir.mkdir(parents=True, exist_ok=True)

# 保存图片
image_path = file_image_dir / f"image_{index:03d}.{ext}"
# 结果: /app/data/images/2025/{file_id}/image_001.jpg ✅
```

### MCP文档解析 (`mcp-servers/document-parser`)

```python
# ✅ 正确：从数据库获取路径后直接使用
file_path = db.query("SELECT archive_path FROM uploaded_files WHERE id = %s", file_id)
# file_path 应该是: /app/data/archive/...

# ❌ 当前问题：数据库返回的是 /Volumes/ssd/...
# 需要修复数据库数据或添加路径转换层
```

---

## 🐛 已知问题与修复

### 问题1: 数据库存储了宿主机路径

**问题描述**:
```sql
SELECT file_path FROM uploaded_files LIMIT 1;
-- 结果: /Volumes/ssd/bidding-data/archive/2025/12/proposal/file.docx
-- 容器内无法访问此路径
```

**影响范围**:
- `uploaded_files` 表的 `file_path` 和 `archive_path` 字段
- 所有历史数据（约 XX 条记录）

**修复方案1: 数据库批量更新** (推荐)
```sql
-- 更新所有宿主机路径为容器路径
UPDATE uploaded_files 
SET file_path = REPLACE(file_path, '/Volumes/ssd/bidding-data', '/app/data')
WHERE file_path LIKE '/Volumes/ssd/bidding-data/%';

UPDATE uploaded_files 
SET archive_path = REPLACE(archive_path, '/Volumes/ssd/bidding-data', '/app/data')
WHERE archive_path LIKE '/Volumes/ssd/bidding-data/%';
```

**修复方案2: 添加路径转换中间层**
```python
# backend/utils/path_mapper.py
def normalize_db_path(db_path: str) -> str:
    """将数据库路径标准化为容器路径"""
    if db_path.startswith("/Volumes/ssd/bidding-data"):
        return db_path.replace("/Volumes/ssd/bidding-data", "/app/data")
    return db_path

# 使用
file_path = normalize_db_path(db.query(...))
```

**修复方案3: 修复上传路由的路径存储逻辑**
```python
# backend/routers/files.py - 归档函数修改

# 当前代码（推测问题所在）
archive_path = os.path.join(ARCHIVE_DIR, ...)  # 已经是 /app/data/archive/...

# ❌ 如果有这样的代码就是问题源头
# archive_path = str(Path(archive_path).resolve())  # 会转为宿主机路径！

# ✅ 正确：直接使用计算的路径
db.execute("UPDATE ... SET archive_path = %s", (archive_path,))
```

### 问题2: init_database.py 硬编码了宿主机路径

**文件**: `backend/init_database.py`

**问题代码**:
```python
# Line 93, 126, 145-148
storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data'
```

**修复**:
```python
# ✅ 应改为容器路径
storage_location TEXT DEFAULT '/app/data'
```

---

## ✅ 检查清单

### 配置文件检查
- [x] `docker-compose.yml` volume挂载正确
- [x] `backend/core/config.py` 使用 `/app/data/` 路径
- [ ] `backend/init_database.py` 移除硬编码的 `/Volumes/ssd/` 路径

### 代码检查
- [x] `backend/routers/files.py` 使用配置的路径
- [x] `skills/image_processor.py` 使用配置的图片路径
- [ ] 所有路由均从配置获取路径，无硬编码

### 数据库检查
- [ ] `uploaded_files.file_path` 全部使用 `/app/data/` 前缀
- [ ] `uploaded_files.archive_path` 全部使用 `/app/data/` 前缀
- [ ] 其他表的路径字段符合标准

### 运行时检查
- [ ] MCP可以访问数据库中的文件路径
- [ ] 日志中无宿主机路径 `/Volumes/ssd/`
- [ ] 文件上传后路径正确存储

---

## 📊 路径使用统计

### 配置层
```python
# backend/core/config.py
UPLOAD_DIR = "/app/data/uploads"         ✅
IMAGE_STORAGE_DIR = "/app/data/images"   ✅
```

### 应用层
```python
# backend/routers/files.py
ARCHIVE_DIR = "/app/data/archive"        ✅ (通过计算得出)
PARSED_DIR = "/app/data/parsed"          ✅ (通过计算得出)
```

### 数据库层
```sql
-- uploaded_files 表
file_path: '/Volumes/ssd/bidding-data/...'     ❌ 需修复
archive_path: '/Volumes/ssd/bidding-data/...'  ❌ 需修复
```

### 物理层
```bash
# 宿主机
/Volumes/ssd/bidding-data/                     ✅ (Docker挂载源)

# 容器内
/app/data/                                     ✅ (应用访问路径)
```

---

## 🎯 强制执行机制

### 1. 代码层面

**路径验证装饰器**:
```python
# backend/utils/path_validator.py
def validate_container_path(path: str) -> bool:
    """验证路径是否为容器内路径"""
    return path.startswith("/app/data/")

def enforce_container_path(func):
    """强制使用容器路径的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str) and not validate_container_path(result):
            raise ValueError(f"Invalid path format: {result}. Must use /app/data/ prefix")
        return result
    return wrapper
```

### 2. 数据库层面

**触发器检查** (可选):
```sql
CREATE OR REPLACE FUNCTION validate_file_path()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.file_path NOT LIKE '/app/data/%' THEN
        RAISE EXCEPTION 'file_path must start with /app/data/, got: %', NEW.file_path;
    END IF;
    IF NEW.archive_path IS NOT NULL AND NEW.archive_path NOT LIKE '/app/data/%' THEN
        RAISE EXCEPTION 'archive_path must start with /app/data/, got: %', NEW.archive_path;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_file_paths
BEFORE INSERT OR UPDATE ON uploaded_files
FOR EACH ROW
EXECUTE FUNCTION validate_file_path();
```

### 3. CI/CD检查

**pre-commit hook**:
```bash
#!/bin/bash
# .git/hooks/pre-commit

# 检查是否有硬编码的宿主机路径
if git diff --cached | grep -q '/Volumes/ssd/bidding-data'; then
    echo "❌ Error: Found hardcoded host path '/Volumes/ssd/bidding-data'"
    echo "   Please use '/app/data/' instead"
    exit 1
fi
```

---

## 📚 相关文档

- `docker-compose.yml` - Docker挂载配置
- `backend/core/config.py` - 路径配置中心
- `backend/routers/files.py` - 文件上传归档逻辑
- `DOCKER_PRINCIPLES.md` - Docker使用原则
- `CODE_PROTECTION.md` - 代码保护规范

---

## 🔄 迁移计划

### 阶段1: 修复数据库历史数据 (优先级: 🔴 高)
```sql
-- 执行路径标准化
UPDATE uploaded_files 
SET 
    file_path = REPLACE(file_path, '/Volumes/ssd/bidding-data', '/app/data'),
    archive_path = REPLACE(archive_path, '/Volumes/ssd/bidding-data', '/app/data')
WHERE file_path LIKE '/Volumes/ssd/bidding-data/%' 
   OR archive_path LIKE '/Volumes/ssd/bidding-data/%';
```

### 阶段2: 修复配置和初始化脚本 (优先级: 🟡 中)
- 更新 `backend/init_database.py` 移除宿主机路径
- 添加路径验证工具函数

### 阶段3: 添加强制检查机制 (优先级: 🟢 低)
- 添加路径验证装饰器
- 可选：添加数据库触发器
- 添加 pre-commit hook

### 阶段4: 测试验证 (优先级: 🔴 高)
- MCP document-parser 使用数据库路径测试
- 文件上传-归档-访问完整流程测试
- 跨环境兼容性测试

---

**最后更新**: 2025-12-16  
**审核状态**: 待审核  
**下一步行动**: 执行数据库路径修复 SQL
