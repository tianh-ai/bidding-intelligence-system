# 环境快照 - 当前正确配置
## 生成时间：2025年12月14日

⚠️ **警告：此文件记录的是当前正确运行的环境配置**
⚠️ **任何修改前必须先备份，不要随意安装或修改！**

---

## Python 环境

### Python 版本
```bash
# 当前使用版本
Python 3.11.9
```

### 已安装包（核心依赖）
```bash
# 运行命令查看当前已安装
pip3 freeze > backend/requirements.txt.snapshot

# 关键包版本（已验证可用）
openai==2.11.0
redis==5.2.1
loguru==0.7.3
psycopg2==2.9.10
fastapi==0.115.6
uvicorn==0.34.0
pydantic==2.10.4
celery==5.4.0
```

### ⚠️ 禁止操作
```bash
# ❌ 不要执行这些命令（除非明确需要）
pip3 install xxx          # 可能破坏现有环境
pip3 upgrade xxx          # 可能引入不兼容版本
pip3 uninstall xxx        # 可能删除关键依赖
```

---

## Docker 环境

### 容器状态（当前正常运行）
```
NAME                    STATUS              PORTS
bidding_backend         Up 3 days           0.0.0.0:18888->8000/tcp
bidding_frontend        Up 3 days           0.0.0.0:13000->5173/tcp
bidding_postgres        Up 3 days (healthy) 0.0.0.0:5433->5432/tcp
bidding_redis           Up 3 days (healthy) 0.0.0.0:6380->6379/tcp
bidding_celery_worker   Up 3 days           8000/tcp
```

### Docker 镜像版本
```
pgvector/pgvector:pg15
redis:7-alpine
bidding-intelligence-system-backend (自构建)
bidding-intelligence-system-frontend (自构建)
```

### ⚠️ 禁止操作
```bash
# ❌ 不要执行这些命令
docker-compose down       # 会删除容器
docker system prune       # 会删除所有未使用资源
docker rmi xxx            # 会删除镜像
docker-compose pull       # 可能更新到不兼容版本
```

---

## 数据库配置（已验证正确）

```env
DB_HOST=localhost
DB_PORT=5433              # ✅ 已确认正确
DB_USER=postgres
DB_PASSWORD=postgres123   # ✅ 已确认正确
DB_NAME=bidding_db        # ✅ 已确认正确
```

### 数据库连接测试（当前正常）
```bash
psql -h localhost -p 5433 -U postgres -d bidding_db -c "SELECT 1;"
# 输出: ?column? 
#        1
```

---

## 前端配置（已验证正确）

```env
VITE_API_URL=http://localhost:18888  # ✅ 连接 Docker 后端
VITE_DEFAULT_ADMIN_USERNAME=admin
VITE_DEFAULT_ADMIN_PASSWORD=bidding2024
```

### Node.js 环境
```bash
# 当前版本（待确认）
node --version
npm --version
```

---

## Redis 配置（已验证正确）

```env
REDIS_HOST=localhost
REDIS_PORT=6379           # ✅ 代码默认端口（Docker 映射会处理）
```

### Redis 连接测试（当前正常）
```bash
redis-cli -h localhost -p 6380 ping
# 输出: PONG
```

---

## 文件系统配置（已验证正确）

### SSD 存储路径
```
/Volumes/ssd/bidding-data/
├── uploads/              # 上传文件
│   └── temp/            # 临时文件
├── parsed/              # 解析结果
├── archive/             # 归档文件
└── logs/                # 日志文件
```

### 权限验证（当前正常）
```bash
ls -ld /Volumes/ssd/bidding-data/*
# 所有目录可读写
```

---

## 端口占用情况（当前正确）

```
✅ 5173  - 本地前端 (空闲，可按需启动)
✅ 8000  - 本地后端 (空闲，可按需启动)
✅ 5433  - PostgreSQL (Docker 占用)
✅ 6380  - Redis (Docker 占用)
✅ 13000 - Docker 前端 (Docker 占用)
✅ 18888 - Docker 后端 (Docker 占用)
```

---

## 健康检查（当前全部通过）

### 后端 API
```bash
curl http://localhost:18888/health
# 输出: {"status":"healthy","service":"bidding-system"}
```

### 前端访问
```bash
curl -I http://localhost:13000
# 输出: HTTP/1.1 200 OK
```

### 登录 API
```bash
curl -X POST http://localhost:18888/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"bidding2024"}'
# 输出: {"token":"eyJ...","user":{...}}
```

---

## 变更管理规则

### 🔴 严格禁止的操作（未经审查）

1. **不要安装新的 Python 包**
   ```bash
   # ❌ 禁止
   pip3 install xxx
   pip3 install -r requirements.txt  # 除非明确需要
   ```

2. **不要修改 Docker 配置**
   ```bash
   # ❌ 禁止
   vim docker-compose.yml
   docker-compose down
   docker-compose build --no-cache
   ```

3. **不要修改数据库连接代码**
   ```bash
   # ❌ 禁止直接编辑
   backend/database/connection.py
   ```

4. **不要删除或清理容器**
   ```bash
   # ❌ 禁止
   docker system prune
   docker volume prune
   ```

### 🟡 需要审查的操作

1. **修改环境变量**
   - 必须先运行 `./config-guard.sh` 验证
   - 必须备份原配置文件

2. **重启服务**
   - 使用标准脚本：`./start-docker.sh`
   - 不要手动 kill 进程

3. **修改端口配置**
   - 必须更新 `PORT_MANAGEMENT.md`
   - 必须运行 `./check-ports.sh` 验证

### 🟢 允许的操作

1. **查看状态**
   ```bash
   ./check-ports.sh
   ./config-guard.sh
   docker-compose ps
   docker-compose logs
   ```

2. **使用标准启动脚本**
   ```bash
   ./start-docker.sh
   ./start-local.sh
   ```

3. **读取配置**
   ```bash
   cat backend/.env
   cat frontend/.env
   ```

---

## 环境变更记录

### 2025-12-14 初始快照
- ✅ Docker 环境正常运行 3 天
- ✅ 所有服务健康检查通过
- ✅ 登录功能正常
- ✅ 数据库连接正常
- ✅ Redis 缓存正常

### 后续变更（记录格式）
```
日期: YYYY-MM-DD
操作: 具体操作内容
原因: 为什么需要这个变更
影响: 影响的组件
回滚: 如何回滚
验证: 如何验证成功
结果: ✅ 成功 / ❌ 失败
```

---

## 故障恢复

### 如果环境被破坏

1. **从 Docker 恢复**
   ```bash
   docker-compose restart
   ```

2. **从配置备份恢复**
   ```bash
   ls .config-backups/
   cp .config-backups/.env.latest backend/.env
   ```

3. **重新构建 Docker**（最后手段）
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

---

## 检查清单

每次修改前执行：

```bash
# 1. 创建环境快照
docker-compose ps > /tmp/docker_before.txt
pip3 freeze > /tmp/pip_before.txt

# 2. 备份配置
cp backend/.env .config-backups/.env.$(date +%Y%m%d_%H%M%S)

# 3. 记录当前状态
./check-ports.sh > /tmp/ports_before.txt

# 4. 执行变更
# ... 你的操作 ...

# 5. 验证变更
./config-guard.sh
curl http://localhost:18888/health

# 6. 对比差异
diff /tmp/docker_before.txt <(docker-compose ps)
diff /tmp/pip_before.txt <(pip3 freeze)
```

---

## 金科玉律

**🚨 当遇到错误时：**

1. ❌ **不要立即安装包** - 先检查是否是配置问题
2. ❌ **不要立即修改环境** - 先检查是否是代码问题
3. ✅ **先运行诊断脚本** - `./check-ports.sh`, `./config-guard.sh`
4. ✅ **查看日志** - `docker-compose logs backend`
5. ✅ **对比快照** - 检查什么变了

**记住：当前环境是正确的，99% 的问题是配置不一致，不是缺少依赖！**

---

## 联系信息

如果必须修改环境，请先：
1. 阅读此文档
2. 创建变更计划
3. 备份当前环境
4. 小步骤验证
5. 记录变更日志
