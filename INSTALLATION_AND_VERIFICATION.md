# 🚀 完整安装与验证步骤

> **说明**: 在执行以下步骤前，已经分析了数据存储架构。参考: `DATA_STORAGE_ARCHITECTURE.md`

---

## 📋 安装前检查

### 步骤 1: 审计数据存储架构
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system
python3 audit_storage.py
```

**预期输出**:
```
✅ 配置检查
✅ 文件系统检查
✅ 数据库检查 (如果有缺失表，会提示)
✅ 数据一致性检查
```

---

## 🔧 安装步骤 (给予全部权限)

### 步骤 2: 创建文件系统结构
```bash
# 确保有全部权限
chmod -R 777 /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system

# 创建所有必需的目录
python3 << 'EOF'
import os
from pathlib import Path

base = Path('/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system')
dirs = [
    base / 'uploads',
    base / 'uploads' / 'temp',
    base / 'uploads' / 'parsed',
    base / 'uploads' / 'archive',
    base / 'backend' / 'logs',
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)
    print(f"✅ {d}")
EOF
```

### 步骤 3: 初始化数据库 (如果数据库不存在)
```bash
# 方式 A: 使用 SQL 脚本 (推荐)
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system
psql -h localhost -U postgres -d postgres -c "CREATE DATABASE bidding_db;"
psql -h localhost -U postgres -d bidding_db -f backend/init_database.sql

# 方式 B: 使用 Python (自动化)
cd backend
python3 << 'EOF'
from database import db
from core.logger import logger

try:
    # 运行初始化脚本
    with open('init_database.sql', 'r') as f:
        sql = f.read()
    
    for statement in sql.split(';'):
        if statement.strip():
            db.execute(statement)
    
    logger.info("✅ 数据库初始化成功")
except Exception as e:
    logger.error(f"❌ 数据库初始化失败: {e}")
EOF
```

### 步骤 4: 安装 Python 依赖
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend

# 安装所有依赖 (包括新增的文档处理模块)
pip install -r requirements.txt

# 验证关键依赖
python3 << 'EOF'
packages = [
    'fastapi', 'pydantic', 'sqlalchemy', 'psycopg2',
    'paddlepaddle', 'paddleocr', 'pillow',
    'openai', 'instructor', 'loguru'
]

for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg} (缺失)")
EOF
```

### 步骤 5: 创建必需的索引和优化
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend

python3 << 'EOF'
from database import db
from core.logger import logger

# 创建关键索引以提高性能
indices = [
    "CREATE INDEX IF NOT EXISTS idx_files_doc_type ON files(doc_type);",
    "CREATE INDEX IF NOT EXISTS idx_chapters_file_id ON chapters(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_vectors_file_id ON vectors(file_id);",
    "CREATE INDEX IF NOT EXISTS idx_uploaded_files_status ON uploaded_files(status);",
]

for idx_sql in indices:
    try:
        db.execute(idx_sql)
        logger.info(f"✅ {idx_sql[:50]}...")
    except Exception as e:
        logger.warning(f"索引创建失败: {e}")

logger.info("✅ 索引创建完成")
EOF
```

---

## ✅ 深度验证

### 步骤 6: 验证文件系统
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system

python3 << 'EOF'
import os
from pathlib import Path

base = Path('.')
required = {
    '上传目录': 'uploads',
    '临时目录': 'uploads/temp',
    '解析目录': 'uploads/parsed',
    '归档目录': 'uploads/archive',
    '日志目录': 'backend/logs',
}

print("📁 文件系统验证:")
for name, path in required.items():
    full_path = base / path
    if full_path.exists():
        print(f"  ✅ {name}: {path}")
    else:
        print(f"  ❌ {name}: {path}")

print("\n📊 目录权限:")
for name, path in required.items():
    full_path = base / path
    if os.access(full_path, os.W_OK):
        print(f"  ✅ {path}: 可写")
    else:
        print(f"  ⚠️  {path}: 权限不足")
EOF
```

### 步骤 7: 验证数据库连接和表结构
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend

python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from core.config import get_settings
from database import db
from core.logger import logger

settings = get_settings()
logger.info(f"📍 数据库: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

# 检查所有表
tables_to_check = [
    'uploaded_files', 'files', 'chapters', 'vectors',
    'chapter_structure_rules', 'chapter_content_rules',
    'chapter_custom_rules', 'chapter_boq_rules',
    'chapter_mandatory_rules', 'chapter_scoring_rules'
]

print("\n📊 数据库表验证:")
missing = []
for table in tables_to_check:
    result = db.execute(f"""
        SELECT EXISTS(
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = '{table}'
        )
    """).fetchone()
    
    if result[0]:
        print(f"  ✅ {table}")
    else:
        print(f"  ❌ {table} (缺失)")
        missing.append(table)

if missing:
    logger.error(f"⚠️  缺失表: {', '.join(missing)}")
    logger.error("请运行: psql -h localhost -U postgres -d bidding_db -f backend/init_database.sql")
else:
    logger.info("✅ 所有表都存在")
EOF
```

### 步骤 8: 验证数据一致性
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend

python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from database import db
from core.logger import logger

print("🔗 数据一致性验证:")

# 检查孤立的章节
result = db.execute("""
    SELECT COUNT(*) FROM chapters c
    WHERE NOT EXISTS(SELECT 1 FROM files f WHERE f.id = c.file_id)
""").fetchone()
orphaned_chapters = result[0]
print(f"  {'✅' if orphaned_chapters == 0 else '⚠️'} 孤立章节: {orphaned_chapters}")

# 检查孤立的向量
result = db.execute("""
    SELECT COUNT(*) FROM vectors v
    WHERE NOT EXISTS(SELECT 1 FROM files f WHERE f.id = v.file_id)
""").fetchone()
orphaned_vectors = result[0]
print(f"  {'✅' if orphaned_vectors == 0 else '⚠️'} 孤立向量: {orphaned_vectors}")

# 统计数据量
result = db.execute("SELECT COUNT(*) FROM files").fetchone()
files_count = result[0]
print(f"\n📈 数据统计:")
print(f"  📄 文件数: {files_count}")

if files_count > 0:
    result = db.execute("SELECT COUNT(*) FROM chapters").fetchone()
    print(f"  📑 章节数: {result[0]}")
    
    result = db.execute("SELECT COUNT(*) FROM vectors").fetchone()
    print(f"  🔍 向量数: {result[0]}")
else:
    logger.info("  (数据库为空，这是正常的)")
EOF
```

---

## 📚 使用真实文件进行验证

### 步骤 9: 上传测试文件
```bash
# 准备一个真实的 PDF 或 DOCX 文件
# 放到: /tmp/test_document.pdf

curl -X POST http://localhost:8000/api/files/upload \
  -F "files=@/tmp/test_document.pdf" \
  -F "uploader=admin"

# 预期响应: 200 OK with file_id
```

### 步骤 10: 验证文件处理流程
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend

python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from database import db
from core.logger import logger

# 查看最新上传的文件
result = db.execute("""
    SELECT id, filename, status, created_at
    FROM uploaded_files
    ORDER BY created_at DESC
    LIMIT 5
""").fetchall()

print("📄 最近上传的文件:")
for row in result:
    print(f"  {row[0][:8]}... | {row[1][:30]:<30} | {row[2]:<10} | {row[3]}")

# 查看处理后的文件数据
result = db.execute("""
    SELECT id, filename, doc_type
    FROM files
    ORDER BY created_at DESC
    LIMIT 5
""").fetchall()

print("\n✅ 已处理的文件:")
for row in result:
    print(f"  {row[0][:8]}... | {row[1][:30]:<30} | {row[2]}")

# 验证章节结构
result = db.execute("""
    SELECT f.filename, COUNT(c.id) as chapter_count
    FROM files f
    LEFT JOIN chapters c ON f.id = c.file_id
    GROUP BY f.id, f.filename
    ORDER BY chapter_count DESC
    LIMIT 5
""").fetchall()

print("\n📑 文件章节统计:")
for filename, count in result:
    print(f"  {filename}: {count} 个章节")
EOF
```

---

## 🧹 清理无用逻辑

### 步骤 11: 删除重复的目录创建代码

在 `backend/routers/files.py` 中清理重复的目录初始化：

```python
# ❌ 删除这些重复的代码
# for directory in [UPLOAD_DIR, TEMP_DIR, PARSED_DIR, ARCHIVE_DIR]:
#     os.makedirs(directory, exist_ok=True)

# ✅ 改为：使用 config 中的 upload_path 属性
upload_path = settings.upload_path  # 这已经自动创建所有目录
```

### 步骤 12: 删除过时的状态字段

检查是否有冗余的状态追踪：
```python
# ❌ 删除冗余字段
# status_created_at  # 重复
# status_updated_at  # 重复

# ✅ 统一使用：
# - created_at
# - updated_at
# - status (single source of truth)
```

---

## ✨ 最终检查

### 步骤 13: 完整系统检查
```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system

# 1. 审计存储架构
python3 audit_storage.py

# 2. 启动后端
cd backend
python3 main.py &

# 3. 测试 API
sleep 3
curl http://localhost:8000/api/health

# 4. 查看日志
tail -f logs/app.log
```

---

## 📋 检查清单

安装完成后的验证清单：

- [ ] ✅ 文件系统目录已创建 (temp, parsed, archive)
- [ ] ✅ 所有 10+ 个数据库表已创建
- [ ] ✅ 数据库索引已创建
- [ ] ✅ Python 依赖已安装
- [ ] ✅ 配置正确 (.env 文件)
- [ ] ✅ 无孤立的数据库记录
- [ ] ✅ 文件路径一致性验证通过
- [ ] ✅ 真实文件上传测试通过
- [ ] ✅ 文档处理模块可正常导入
- [ ] ✅ 无重复的目录创建代码
- [ ] ✅ 状态字段没有冗余定义

---

**所有步骤完成后，系统即可投入使用！** 🚀

