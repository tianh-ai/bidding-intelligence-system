# 端口管理规范

## 当前端口分配表

| 服务 | Docker端口 | 本地开发端口 | 用途 |
|------|-----------|-------------|------|
| **后端API** | 18888 | 8000 | FastAPI服务 |
| **前端Web** | 13000 | 5173 | Vite开发服务器 |
| **PostgreSQL** | 5433 | 5433 | 数据库（共用） |
| **Redis** | 6380 | 6379 | 缓存（Docker用6380，代码默认6379） |
| **Celery Flower** | - | 5555 | 任务监控 |

## 环境选择规则

### 方案A：只用 Docker（推荐生产环境）
```bash
# 启动所有服务
docker-compose up -d

# 访问地址
前端: http://localhost:13000
后端API: http://localhost:18888
后端文档: http://localhost:18888/docs
```

### 方案B：只用本地开发（推荐开发调试）
```bash
# 1. 停止 Docker 服务（避免端口冲突）
docker-compose stop backend frontend

# 2. 保留数据库和 Redis（共用）
docker-compose up -d postgres redis

# 3. 启动本地服务
cd backend && python3 main.py &  # 后端 8000
cd frontend && npm run dev        # 前端 5173
```

### 方案C：混合模式（当前状态，不推荐）
- Docker: 数据库 + Redis
- 本地: 前端开发
- Docker: 后端容器
**问题**：前端需要配置连接 Docker 后端的 18888 端口

## 配置文件检查清单

### 1. 后端配置 `backend/.env`
```bash
# 数据库（Docker 端口）
DB_HOST=localhost
DB_PORT=5433          # ✅ 固定使用 Docker 暴露的端口
DB_USER=postgres
DB_PASSWORD=postgres123
DB_NAME=bidding_db

# Redis（注意：代码默认6379，Docker暴露6380）
REDIS_HOST=localhost
REDIS_PORT=6379       # ⚠️ 如果用Docker Redis，改为 6380

# API端口（本地开发）
API_PORT=8000
```

### 2. 前端配置 `frontend/.env`
```bash
# 固定使用 Docker 对外后端端口
VITE_API_URL=http://localhost:18888
```

### 3. Docker配置 `docker-compose.yml`
```yaml
services:
  backend:
    ports:
      - "18888:8000"    # 外部18888 → 容器内8000
  
  frontend:
    ports:
      - "13000:5173"    # 外部13000 → 容器内5173
  
  postgres:
    ports:
      - "5433:5432"     # 外部5433 → 容器内5432
  
  redis:
    ports:
      - "6380:6379"     # 外部6380 → 容器内6379
```

## 端口冲突快速诊断

```bash
# 查看端口占用
lsof -i :18888 -i :13000

# 杀死占用进程
lsof -ti :18888 | xargs kill -9

# 查看 Docker 容器状态
docker-compose ps

# 停止所有 Docker 服务
docker-compose down
```

## 启动脚本（防止端口冲突）

### `start-docker.sh`
```bash
#!/bin/bash
# 使用 Docker 环境
echo "🐳 启动 Docker 环境..."

# 1. 停止本地进程
pkill -f "python3 main.py"
pkill -f "vite.*5173"

# 2. 启动 Docker
docker-compose up -d

# 3. 等待服务就绪
sleep 5
echo "✅ 服务已启动："
echo "   前端: http://localhost:13000"
echo "   后端: http://localhost:18888/docs"
```

### `start-local.sh`
```bash
#!/bin/bash
# 已禁用：本项目强制 Docker 运行
echo "❌ 已禁用本地启动（必须使用 Docker）。"
echo "docker compose up -d"
exit 1
```

## 当前问题修复步骤

### 立即执行：统一到 Docker 模式

```bash
# 1. 停止所有本地进程
pkill -f "python3 main.py"
pkill -f "vite.*5173"

# 2. 修改前端配置指向 Docker 后端
echo "VITE_API_URL=http://localhost:18888" > frontend/.env

# 3. 重启 Docker 前端
docker-compose restart frontend

# 4. 验证
curl http://localhost:18888/health
curl http://localhost:13000
```

访问 **http://localhost:13000** 即可正常登录。

## 长期防范措施

1. **在 README.md 中明确说明**启动模式选择
2. **Git 忽略本地配置**：`.env` 文件不提交，只提交 `.env.example`
3. **健康检查脚本**：每次启动前检查端口占用
4. **环境变量验证**：后端启动时打印实际配置
5. **使用统一的启动脚本**：不要手动启动

## 检查清单（每次启动前）

- [ ] 确定使用 Docker 还是本地开发
- [ ] 检查 `.env` 文件的 API_URL 配置
- [ ] 运行 `docker-compose ps` 查看容器状态
- [ ] 运行 `lsof -i :8000` 检查端口占用
- [ ] 验证后端健康检查 `curl localhost:端口/health`
