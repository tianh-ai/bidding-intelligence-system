# 🚀 配置管理快速指南

## 核心解决方案

**问题**：配置反复出错（改了又错）

**原因**：配置分散在多个文件，手动修改容易遗漏

**解决**：配置守护系统 - 自动验证和修复

---

## 三个关键命令

```bash
./config-guard.sh    # 检查并自动修复所有配置
./check-ports.sh     # 检查端口占用
./start-docker.sh    # 启动系统（自动运行配置检查）
```

---

## 日常使用

### 启动系统
```bash
./start-docker.sh
# 访问: http://localhost:13000
```

### 修改配置的正确方法

#### ❌ 错误（会导致反复出错）
```bash
vim backend/.env          # 改这里
vim frontend/.env         # 又改这里
vim backend/database/connection.py  # 忘了这里
# 结果：配置不一致
```

#### ✅ 正确
```bash
# 1. 编辑配置守护脚本中的金标准
vim config-guard.sh
# 找到：backend/.env:DB_PORT:5433
# 修改为你要的值

# 2. 运行脚本自动同步到所有文件
./config-guard.sh

# 3. 验证
./start-docker.sh
```

---

## 配置金标准

### 数据库
```
DB_PORT=5433          ← Docker 端口，不是 5432！
DB_PASSWORD=postgres123
DB_NAME=bidding_db
```

### 前端 API
```
VITE_API_URL=http://localhost:18888  ← Docker 后端
# 或
VITE_API_URL=http://localhost:8000   ← 本地后端
```

---

## 常见问题

**Q: 为什么是 5433 不是 5432？**
A: Docker 端口映射，避免与系统 PostgreSQL 冲突

**Q: 配置改错了怎么办？**
A: 运行 `./config-guard.sh` 自动修复，或从 `.config-backups/` 恢复

**Q: 怎么知道哪里配置错了？**
A: 运行 `./config-guard.sh` 会自动检测并显示

---

## 核心原则

1. ✅ **唯一真值**：只在 `config-guard.sh` 中定义正确配置
2. ✅ **自动化**：每次启动前自动检查修复
3. ✅ **有备份**：所有修改都在 `.config-backups/`
4. ✅ **不要手动到处改配置**

详细文档见：`CONFIGURATION_GUIDE.md`
