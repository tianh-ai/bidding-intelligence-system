# 投标智能系统 - Docker 部署指南

## 📦 部署方式说明

本系统支持**两种运行方式**：

### 方式 1: Docker 容器化部署（推荐生产环境）
- ✅ 环境隔离，无需手动安装依赖
- ✅ 一键启动所有服务
- ✅ 自动配置数据库和 Redis
- ✅ 便于扩展和部署

### 方式 2: 本地直接运行（开发调试）
- ✅ 代码修改立即生效
- ✅ 便于调试
- ✅ 性能更好

---

## 🐳 Docker 部署（推荐）

### 端口配置

为避免端口冲突，已修改为：

| 服务 | 容器内端口 | 主机端口 | 说明 |
|-----|----------|---------|-----|
| 前端 | 5173 | 5173 | Vite 默认端口 |
| 后端 | 8888 | 8888 | FastAPI 服务 |
| PostgreSQL | 5432 | 5433 | 数据库 |
| Redis | 6379 | 6380 | 缓存/队列 |

### 快速启动

#### 1. 配置 API Keys

编辑 `.env.docker` 文件，填写你的 API Keys：

```bash
# 复制环境变量模板
cp .env.docker .env

# 编辑并填写 API Keys
nano .env  # 或使用其他编辑器
```

必填项：
```env
OPENAI_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=your-deepseek-key
QWEN_API_KEY=your-qwen-key
```

#### 2. 启动所有服务

```bash
# 构建并启动所有容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 3. 访问系统

- **前端**: http://localhost:13000
- **后端 API**: http://localhost:18888
- **API 文档**: http://localhost:18888/docs

默认账号：`admin` / `admin123`

#### 4. 停止服务

```bash
# 停止所有容器
docker-compose down

# 停止并删除数据卷（慎用）
docker-compose down -v
```

---

## 💻 本地直接运行（已禁用）

为保持端口与依赖一致性，本项目仅支持通过 Docker 运行。
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填写数据库连接和 API Keys

# 初始化数据库
createdb bidding_db
psql -d bidding_db -f init_database.sql

# 启动后端（端口 8888）
uvicorn main:app --host 0.0.0.0 --port 8888 --reload
```

#### 3. 启动 Celery Worker

```bash
# 新终端
cd backend
source venv/bin/activate
celery -A worker worker --loglevel=info
```

#### 4. 启动前端

```bash
# 新终端
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 确认 VITE_API_URL=http://localhost:18888

# 本项目仅支持通过 Docker 对外提供服务（前端:13000 / 后端:18888）
# 如需开发请在容器内进行，不建议本地直接 npm run dev
```

#### 5. 访问

- 前端: http://localhost:13000
- 后端: http://localhost:18888

---

## 🔧 Docker 常用命令

### 查看状态

```bash
# 查看运行中的容器
docker-compose ps

# 查看所有容器（包括停止的）
docker-compose ps -a

# 查看资源使用
docker stats
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart frontend
```

### 进入容器

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入数据库容器
docker-compose exec postgres psql -U postgres -d bidding_db

# 进入 Redis 容器
docker-compose exec redis redis-cli
```

### 查看日志

```bash
# 实时查看所有日志
docker-compose logs -f

# 查看最近 100 行
docker-compose logs --tail=100

# 查看特定服务
docker-compose logs -f backend
```

### 更新服务

```bash
# 代码修改后重新构建
docker-compose up -d --build

# 只重建特定服务
docker-compose up -d --build backend
```

---

## 🐛 故障排除

### 问题 1: 端口被占用

```bash
# 查看端口占用
lsof -i :5173
lsof -i :8888

# 杀掉进程
kill -9 <PID>

# 或修改 docker-compose.yml 中的端口映射
```

### 问题 2: 数据库连接失败

```bash
# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres

# 检查数据库健康状态
docker-compose exec postgres pg_isready -U postgres
```

### 问题 3: 前端无法连接后端

检查 `frontend/.env` 中的 API 地址：
```env
VITE_API_URL=http://localhost:8888
```

### 问题 4: 容器启动失败

```bash
# 查看详细错误
docker-compose logs <服务名>

# 重建容器
docker-compose down
docker-compose up -d --build
```

### 问题 5: 清理所有数据重新开始

```bash
# 停止并删除所有容器和数据卷
docker-compose down -v

# 清理未使用的镜像
docker system prune -a

# 重新启动
docker-compose up -d --build
```

---

## 📊 服务架构

```
┌─────────────────────────────────────────────────┐
│                   用户浏览器                     │
│            http://localhost:13000               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│              Frontend (React)                   │
│          Container: bidding_frontend            │
│      Container Port: 5173 / Host Port: 13000     │
└──────────────────┬──────────────────────────────┘
                   │
                   │ API Calls
                   ▼
┌─────────────────────────────────────────────────┐
│           Backend (FastAPI)                     │
│          Container: bidding_backend             │
│      Container Port: 8000 / Host Port: 18888     │
└─────────┬──────────────┬────────────────────────┘
          │              │
          ▼              ▼
┌──────────────┐  ┌─────────────────┐
│  PostgreSQL  │  │  Celery Worker  │
│   Port:5433  │  │  (Background)   │
└──────────────┘  └─────────────────┘
          │              │
          ▼              ▼
     ┌─────────────────────┐
     │       Redis         │
     │     Port: 6380      │
     └─────────────────────┘
```

---

## 🚀 生产环境部署建议

### 1. 使用 nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:13000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:18888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 使用环境变量管理密钥

```bash
# 不要将 .env 提交到 Git
echo ".env" >> .gitignore

# 在服务器上设置环境变量
export OPENAI_API_KEY=xxx
export DEEPSEEK_API_KEY=xxx
```

### 3. 配置持久化存储

确保数据卷正确挂载，数据不会丢失：
```yaml
volumes:
  - ./data/postgres:/var/lib/postgresql/data
  - ./data/redis:/data
  - ./uploads:/app/uploads
```

### 4. 监控和日志

```bash
# 设置日志轮转
docker-compose logs -f > app.log &

# 使用 Prometheus + Grafana 监控
```

---

## 📝 总结

### Docker 方式（推荐）

```bash
# 1. 配置 API Keys
cp .env.docker .env
nano .env

# 2. 启动
docker-compose up -d

# 3. 访问
浏览器打开: http://localhost:13000
```

### 本地方式

```bash
本项目本地直跑（绕过 Docker）已禁用。
```

**端口总结**:
- 前端: **13000**
- 后端: **18888**
- 数据库: **5433**
- Redis: **6380**

有任何问题请随时反馈！🎉
