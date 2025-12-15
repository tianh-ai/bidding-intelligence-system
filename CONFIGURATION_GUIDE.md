# 配置管理规范 - 防止配置反复出错

## 问题根源

**为什么配置总是改了又错？**

1. **多处定义同一配置**：
   - `backend/.env` 文件
   - `backend/database/connection.py` 代码硬编码
   - `frontend/.env` 文件
   - `docker-compose.yml` Docker 配置
   
2. **没有统一的真值来源**（Single Source of Truth）

3. **手动修改容易遗漏**某个文件

4. **Git 不跟踪 `.env` 文件**，本地修改无法同步

## 解决方案：配置守护系统

### 1. 金标准配置（Single Source of Truth）

所有正确的配置值定义在 `config-guard.sh` 中：

```bash
declare -A CORRECT_CONFIGS=(
    ["backend/.env:DB_PORT"]="5433"      # ✅ 唯一真值
    ["backend/.env:DB_PASSWORD"]="postgres123"
    # ... 其他配置
)
```

### 2. 自动验证和修复

**每次启动前自动运行**：

```bash
./config-guard.sh  # 检查所有配置，自动修复错误
```

修复逻辑：
- ✅ 发现错误值 → 自动备份 → 替换为正确值
- ✅ 记录所有修改到 `.config-backups/`
- ✅ 生成配置锁文件检测意外修改

### 3. 集成到启动脚本

已修改 `start-docker.sh` 和 `start-local.sh`，启动前自动执行配置检查。

## 当前配置金标准

### 数据库配置
```bash
DB_HOST=localhost
DB_PORT=5433          # ⚠️ 关键！Docker 映射的端口
DB_USER=postgres
DB_PASSWORD=postgres123   # ⚠️ 与 docker-compose.yml 一致
DB_NAME=bidding_db    # ⚠️ 不是默认的 postgres
```

**为什么是 5433？**
- Docker 内部 PostgreSQL 使用 5432
- Docker Compose 映射到宿主机 5433（避免与系统 PostgreSQL 冲突）
- 代码连接时必须用 5433

### 前端配置
```bash
VITE_API_URL=http://localhost:18888  # ⚠️ Docker 后端端口
```

**为什么是 18888？**
- Docker 内部 FastAPI 使用 8000
- Docker Compose 映射到宿主机 18888
- 前端必须连接 18888（如果用 Docker 后端）

### Redis 配置
```bash
REDIS_PORT=6379   # ⚠️ 代码默认值
```

**Redis 端口特殊情况**：
- Docker 暴露 6380
- 但代码默认连接 6379
- **为什么能工作？** 因为 Redis 客户端会自动处理

## 防止配置出错的工作流

### 方法一：使用配置守护脚本（推荐）

```bash
# 1. 修改配置前，先在 config-guard.sh 中更新金标准
vim config-guard.sh
# 找到 CORRECT_CONFIGS，修改目标值

# 2. 运行守护脚本，自动同步到所有文件
./config-guard.sh

# 3. 验证修改
cat backend/.env | grep DB_PORT
```

### 方法二：使用模板文件

```bash
# 1. 参考 .env.template 文件（只读，不要修改）
cat .env.template

# 2. 手动修改实际配置文件
vim backend/.env

# 3. 运行守护脚本验证
./config-guard.sh
```

### 方法三：直接修改并锁定

```bash
# 1. 确认当前配置正确
./check-ports.sh
curl http://localhost:18888/health

# 2. 生成配置锁
./config-guard.sh

# 3. 锁定文件（防止误修改）
chmod 444 backend/.env frontend/.env  # 只读
# 需要修改时：chmod 644 backend/.env
```

## 代码中的硬编码检查

### 关键文件监控

#### `backend/database/connection.py`

**错误代码示例**（已修复）：
```python
# ❌ 错误！
port=int(os.getenv("DB_PORT", 5432))  # 默认值错误
password=os.getenv("DB_PASSWORD", "your-super-secret...")  # 默认值错误
```

**正确代码**：
```python
# ✅ 正确
port=int(os.getenv("DB_PORT", 5433))  # Docker 映射端口
password=os.getenv("DB_PASSWORD", "postgres123")  # 与 docker-compose 一致
database=os.getenv("DB_NAME", "bidding_db")  # 项目数据库
```

**为什么需要正确的默认值？**
- `.env` 文件可能丢失
- 其他开发者可能没有配置环境变量
- 默认值应该与 Docker 配置一致

### 自动检测代码硬编码

`config-guard.sh` 会检查这些模式：
```bash
# 检测错误的端口默认值
grep 'DB_PORT.*5432' backend/database/connection.py

# 检测错误的密码
grep 'your-super-secret' backend/database/connection.py

# 检测错误的数据库名
grep 'DB_NAME.*"postgres"' backend/database/connection.py
```

## 配置变更检查清单

**每次修改配置后执行**：

```bash
# 1. 运行配置守护
./config-guard.sh

# 2. 检查端口占用
./check-ports.sh

# 3. 重启服务
./start-docker.sh  # 或 ./start-local.sh

# 4. 验证健康检查
curl http://localhost:18888/health

# 5. 测试登录
curl -X POST http://localhost:18888/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"bidding2024"}'
```

## Git 版本控制策略

### 应该提交的文件
✅ `.env.template` - 配置模板（不含敏感信息）
✅ `config-guard.sh` - 配置守护脚本
✅ `CONFIGURATION_GUIDE.md` - 本文档
✅ `docker-compose.yml` - Docker 配置

### 不应该提交的文件
❌ `backend/.env` - 包含 API 密钥
❌ `frontend/.env` - 本地开发配置
❌ `.config-backups/` - 配置备份目录
❌ `.config.lock` - 配置锁文件

### .gitignore 配置
```gitignore
# 环境变量
backend/.env
frontend/.env

# 配置备份
.config-backups/
.config.lock

# 日志
*.log
/tmp/
```

## 配置优先级

当多处定义同一配置时，优先级顺序：

1. **环境变量**（最高优先级）
   ```bash
   DB_PORT=5433 python3 main.py
   ```

2. **.env 文件**
   ```bash
   # backend/.env
   DB_PORT=5433
   ```

3. **代码默认值**（最低优先级）
   ```python
   port = int(os.getenv("DB_PORT", 5433))  # 仅当前两者都不存在时使用
   ```

## 常见配置错误和修复

### 错误 1：数据库连接失败
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**原因**：端口配置错误（5432 vs 5433）

**修复**：
```bash
./config-guard.sh  # 自动修复
```

### 错误 2：前端登录无响应
```
Network Error: Failed to fetch
```

**原因**：前端连接了错误的后端端口（8000 vs 18888）

**修复**：
```bash
# 检查前端配置
cat frontend/.env | grep VITE_API_URL
# 应该是: VITE_API_URL=http://localhost:18888

# 自动修复
./config-guard.sh
```

### 错误 3：Redis 连接失败
```
redis.exceptions.ConnectionError: Error 61 connecting to localhost:6379
```

**原因**：Redis 端口配置与 Docker 不一致

**修复**：
```bash
# 确认 Docker Redis 端口
docker-compose ps | grep redis
# 输出: 0.0.0.0:6380->6379/tcp

# 代码应该连接 6379（Docker 会映射）
# 或者修改代码连接 6380
```

## 高级技巧：配置版本管理

### 为不同环境创建配置文件

```bash
# 开发环境
cp .env.template backend/.env.development
# 编辑: VITE_API_URL=http://localhost:18888

# 生产环境（Docker）
cp .env.template backend/.env.production
# 编辑: VITE_API_URL=http://localhost:18888

# 使用时链接到 .env
ln -sf .env.development backend/.env
```

### 配置加密（敏感信息）

```bash
# 加密 API 密钥
echo "your-api-key" | openssl enc -aes-256-cbc -salt -out .api_key.enc

# 在启动脚本中解密
openssl enc -aes-256-cbc -d -in .api_key.enc > /tmp/api_key
export OPENAI_API_KEY=$(cat /tmp/api_key)
```

## 总结

**防止配置反复出错的核心原则**：

1. ✅ **唯一真值来源**：`config-guard.sh` 定义所有正确值
2. ✅ **自动化验证**：每次启动前自动检查配置
3. ✅ **备份机制**：所有修改都有备份，可随时恢复
4. ✅ **文档化**：配置决策记录在本文档中
5. ✅ **版本控制**：模板文件提交到 Git，实际配置不提交

**记住**：不要手动到处修改配置，只在 `config-guard.sh` 中修改金标准，然后运行脚本自动同步！
