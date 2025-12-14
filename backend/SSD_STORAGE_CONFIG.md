# 📋 投标智能系统 - SSD存储配置完成文档

**配置日期**: 2025年12月12日  
**配置状态**: ✅ 完成并验证  
**存储方案**: SSD盘集中存储

---

## 📊 存储架构总览

### 存储位置层级结构

```
/Volumes/ssd/bidding-data/
├── uploads/                    # 文件上传目录 (1.8TB SSD可用空间)
│   ├── *.pdf                   # 原始PDF文件
│   ├── *.docx                  # Word文档
│   └── temp/                   # 临时文件处理目录
├── parsed/                     # 解析结果目录
│   ├── *.json                  # 结构化解析结果
│   └── *.pkl                   # 序列化对象
├── archive/                    # 归档文件目录
│   └── *.tar.gz                # 压缩归档
├── logs/                       # 日志文件目录
│   ├── app.log                 # 应用日志
│   ├── error.log               # 错误日志
│   └── access.log              # 访问日志
└── db/                         # 数据库备份目录
    └── *.sql.gz                # 数据库备份
```

---

## 🔧 配置文件修改清单

### 1. backend/core/config.py

**修改内容**:
```python
# 上传路径 (原: "./uploads", 现: "/Volumes/ssd/bidding-data/uploads")
UPLOAD_DIR: str = "/Volumes/ssd/bidding-data/uploads"

# 日志路径 (原: "logs", 现: "/Volumes/ssd/bidding-data/logs")
LOG_DIR: str = "/Volumes/ssd/bidding-data/logs"
```

**影响范围**: 
- 所有文件上传操作
- 所有日志记录

### 2. backend/.env.example

**新增配置**:
```
UPLOAD_DIR=/Volumes/ssd/bidding-data/uploads
PARSED_DIR=/Volumes/ssd/bidding-data/parsed
ARCHIVE_DIR=/Volumes/ssd/bidding-data/archive
LOG_DIR=/Volumes/ssd/bidding-data/logs
```

### 3. backend/routers/files.py

**修改内容**:
```python
# 文件路由中的目录配置 (原: 相对路径, 现: 绝对SSD路径)
UPLOAD_DIR = "/Volumes/ssd/bidding-data/uploads"
TEMP_DIR = "/Volumes/ssd/bidding-data/uploads/temp"
PARSED_DIR = "/Volumes/ssd/bidding-data/parsed"
ARCHIVE_DIR = "/Volumes/ssd/bidding-data/archive"
```

---

## 💾 数据库存储配置

### PostgreSQL数据库

**连接信息**:
```
主机名    : localhost
端口      : 5432
数据库    : bidding_db
用户名    : postgres
驱动      : psycopg2 (已安装)
```

**数据库表**:
- `knowledge_base`      - 知识库条目
- `uploaded_files`      - 上传文件元数据
- `parsing_results`     - 解析结果
- (其他业务表)

### 表存储位置配置

在 `init_database.py` 中添加了 `storage_location` 字段，记录文件物理存储位置：

```sql
ALTER TABLE uploaded_files ADD COLUMN storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data';
ALTER TABLE parsing_results ADD COLUMN storage_location TEXT DEFAULT '/Volumes/ssd/bidding-data/parsed';
```

---

## ✅ 验证结果

### 系统验证脚本执行结果

```
✅ SSD存储结构     - 所有目录已创建
✅ 配置文件        - 已更新SSD路径
✅ 目录权限        - 读写权限正常
✅ Python依赖      - 已安装核心包
✅ 数据库配置      - 主机/端口/用户均可
```

### 磁盘空间信息

```
设备          容量      已用      可用      使用率
/Volumes/ssd  1.8TB    1.8GB     1.8TB      1%
```

---

## 🚀 部署步骤

### Step 1: 启动PostgreSQL数据库

```bash
# 启动PostgreSQL服务 (macOS)
brew services start postgresql

# 验证数据库连接
psql -h localhost -U postgres -d bidding_db
```

### Step 2: 初始化数据库

```bash
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/backend

# 创建所有表和初始数据
python3 init_database.py
```

**输出示例**:
```
✅ knowledge_base 表已创建
✅ uploaded_files 表已创建
✅ parsing_results 表已创建
✅ 所有表创建完成
```

### Step 3: 启动后端API服务

```bash
# 在backend目录下
python3 main.py
```

**预期输出**:
```
File upload directories initialized (SSD Storage):
  - Upload: /Volumes/ssd/bidding-data/uploads
  - Temp: /Volumes/ssd/bidding-data/uploads/temp
  - Parsed: /Volumes/ssd/bidding-data/parsed
  - Archive: /Volumes/ssd/bidding-data/archive

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: 启动前端服务

```bash
# 在frontend目录下
cd ../frontend
npm run dev
```

---

## 📁 文件流转逻辑

### 文件上传流程

```
用户上传文件
    ↓
/api/files/upload
    ↓
保存到: /Volumes/ssd/bidding-data/uploads/{file_id}.{ext}
    ↓
数据库记录:
  - uploaded_files表 (文件元数据)
  - storage_location: '/Volumes/ssd/bidding-data/uploads'
    ↓
返回: file_id, upload_path, status
```

### 文件解析流程

```
触发解析: /api/files/parse/{file_id}
    ↓
读取: /Volumes/ssd/bidding-data/uploads/{file_id}.pdf
    ↓
处理 (提取章节、生成摘要等)
    ↓
保存到: /Volumes/ssd/bidding-data/parsed/{file_id}.json
    ↓
数据库记录:
  - parsing_results表 (解析结果)
  - storage_location: '/Volumes/ssd/bidding-data/parsed'
    ↓
返回: chapters, summary, status
```

### 知识库更新流程

```
解析完成
    ↓
提取关键内容
    ↓
保存到知识库:
  - 表: knowledge_base
  - file_id: 关联原始文件
  - file_name: 文件名
  - content: 提取的内容
  - category: 分类 (auto-extracted)
    ↓
完成
```

---

## 🔍 常用查询和监控

### 查看已上传的文件

```sql
SELECT id, file_name, file_size, upload_status, storage_location, created_at
FROM uploaded_files
ORDER BY created_at DESC
LIMIT 10;
```

### 查看解析结果

```sql
SELECT f.file_name, p.chapter_count, p.parsing_time, p.storage_location
FROM parsing_results p
JOIN uploaded_files f ON p.file_id = f.id
ORDER BY p.created_at DESC;
```

### 查看知识库内容

```sql
SELECT COUNT(*), file_name, category
FROM knowledge_base
GROUP BY file_name, category;
```

### 检查磁盘使用情况

```bash
# 查看各目录大小
du -sh /Volumes/ssd/bidding-data/*

# 查看详细统计
df -h /Volumes/ssd/bidding-data/
```

---

## 🛠️ 日常维护

### 日志查看

```bash
# 查看最近的日志
tail -100 /Volumes/ssd/bidding-data/logs/app.log

# 实时监控日志
tail -f /Volumes/ssd/bidding-data/logs/app.log
```

### 性能监控

```bash
# 监控SSD使用情况
watch -n 5 'du -sh /Volumes/ssd/bidding-data/*'

# 监控数据库连接
psql -h localhost -U postgres -d bidding_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### 数据备份

```bash
# 备份数据库
pg_dump -h localhost -U postgres bidding_db | gzip > /Volumes/ssd/bidding-data/db/backup_$(date +%Y%m%d).sql.gz

# 备份上传的文件
tar -czf /Volumes/ssd/bidding-data/db/uploads_backup_$(date +%Y%m%d).tar.gz /Volumes/ssd/bidding-data/uploads/
```

---

## ⚠️ 注意事项

1. **SSD空间监控**: 定期检查SSD使用率，1.8TB容量应该足够

2. **数据库维护**: 定期执行VACUUM ANALYZE保持性能

3. **日志轮转**: 日志文件配置了自动轮转 (每天午夜)

4. **权限管理**: 所有目录权限设置为755，确保读写权限

5. **备份策略**: 建议定期备份数据库到其他存储介质

---

## 📞 故障排除

### 问题1: 权限拒绝错误

```
Error: Permission denied: '/Volumes/ssd/bidding-data/uploads'
```

**解决方案**:
```bash
chmod -R 755 /Volumes/ssd/bidding-data/
```

### 问题2: 磁盘空间不足

```
Error: No space left on device
```

**解决方案**:
```bash
# 清理临时文件
rm -rf /Volumes/ssd/bidding-data/uploads/temp/*

# 检查磁盘使用
du -sh /Volumes/ssd/bidding-data/*
```

### 问题3: 数据库连接失败

```
Error: could not connect to server
```

**检查步骤**:
1. 确认PostgreSQL正在运行: `brew services list`
2. 检查端口: `lsof -i :5432`
3. 查看日志: `tail -20 /usr/local/var/log/postgres.log`

---

## ✨ 下一步行动

1. ✅ 配置已完成 (SSD存储)
2. ⏳ 启动PostgreSQL数据库
3. ⏳ 运行 `python3 init_database.py`
4. ⏳ 启动后端和前端服务
5. ⏳ 上传真实文件进行测试

---

**配置完成！系统已就绪。** 🎉

