# 投标智能系统 - 部署快速参考

## 🚀 快速启动

### Docker 方式（推荐）

```bash
# 1. 配置 API Keys
cp .env.docker .env
nano .env  # 填写 OPENAI_API_KEY, DEEPSEEK_API_KEY, QWEN_API_KEY

# 2. 启动所有服务
docker-compose up -d

# 3. 访问系统
# 前端: http://localhost:5173
# 后端: http://localhost:8888
```

### 本地方式

```bash
# 后端
cd backend
uvicorn main:app --host 0.0.0.0 --port 8888 --reload

# 前端（新终端）
cd frontend
npm run dev
```

### 一键脚本

```bash
./start_all.sh
# 选择: 1-Docker启动  2-本地启动
```

---

## 🌐 端口配置（已修改避免冲突）

| 服务 | 端口 | 访问地址 |
|-----|------|---------|
| **前端** | 5173 | http://localhost:5173 |
| **后端** | 8888 | http://localhost:8888 |
| **API 文档** | 8888 | http://localhost:8888/docs |
| **PostgreSQL** | 5433 | localhost:5433 |
| **Redis** | 6380 | localhost:6380 |

---

## 🐳 Docker 命令速查

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 重启
docker-compose restart

# 重建
docker-compose up -d --build

# 进入容器
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres -d bidding_db
```

---

## 📁 项目结构

```
bidding-intelligence-system/
├── backend/              # 后端（FastAPI + Python）
│   ├── main.py          # 入口 - 端口 8888
│   ├── routers/         # API 路由
│   ├── engines/         # 6个核心引擎
│   └── Dockerfile       # Docker 配置
│
├── frontend/            # 前端（React + TypeScript）
│   ├── src/
│   │   ├── pages/      # 6个主要页面
│   │   ├── components/ # UI 组件
│   │   └── services/   # API 封装
│   └── Dockerfile      # Docker 配置
│
├── docker-compose.yml  # Docker 编排（5个服务）
├── .env.docker         # Docker 环境变量模板
└── start_all.sh        # 统一启动脚本
```

---

## 🔑 必填配置

### `.env` 文件（Docker 方式）

```env
# 必填 - LLM API Keys
OPENAI_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=your-deepseek-key
QWEN_API_KEY=your-qwen-key

# 自动配置（无需修改）
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@postgres:5432/bidding_db
REDIS_URL=redis://redis:6379/0
```

### `frontend/.env` 文件（本地方式）

```env
VITE_API_URL=http://localhost:8888
```

---

## 🐛 常见问题

### 端口冲突

```bash
# 查看端口占用
lsof -i :5173
lsof -i :8888

# 杀掉进程
kill -9 <PID>

# 修改端口（编辑文件）
# vite.config.ts - 前端端口
# docker-compose.yml - 所有端口映射
```

### Docker 启动失败

```bash
# 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 完全重建
docker-compose down -v
docker-compose up -d --build
```

### 前端无法连接后端

检查环境变量：
```bash
cat frontend/.env
# 应该是: VITE_API_URL=http://localhost:8888
```

---

## 📚 完整文档

| 文档 | 内容 |
|-----|------|
| `DOCKER_GUIDE.md` | Docker 详细部署指南 |
| `FRONTEND_GUIDE.md` | 前端系统完整说明 |
| `frontend/README.md` | 前端开发文档 |
| `frontend/QUICKSTART.md` | 前端快速启动 |

---

## 💡 开发提示

```bash
# 查看实时日志
docker-compose logs -f backend

# 进入数据库
docker-compose exec postgres psql -U postgres -d bidding_db

# 清空数据重新开始
docker-compose down -v
docker-compose up -d

# 只重建某个服务
docker-compose up -d --build backend
```

---

**默认登录**: `admin` / `admin123`

**完整启动只需 3 步**: 配置 → 启动 → 访问 ✅
