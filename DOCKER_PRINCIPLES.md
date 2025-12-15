# Docker 使用原则

**创建时间**: 2025-12-14  
**状态**: 强制执行

## 🔒 核心原则

> **所有服务必须通过 Docker 运行，严禁绕过 Docker 直接运行服务**

### 为什么必须使用 Docker？

1. **环境一致性** - 开发、测试、生产环境完全一致
2. **依赖隔离** - 避免本地环境污染和版本冲突
3. **部署简单** - 一键启动所有服务
4. **可重现性** - 任何人都能快速启动相同环境
5. **资源管理** - 统一的资源限制和监控

## 🚫 禁止的操作

```bash
# ❌ 禁止：直接运行后端
cd backend && python main.py

# ❌ 禁止：直接运行前端
cd frontend && npm run dev

# ❌ 禁止：本地安装服务
brew install postgresql
brew install redis

# ❌ 禁止：混合使用（部分Docker，部分本地）
docker-compose up postgres redis  # 只启动部分服务
cd backend && python main.py      # 本地运行后端 ← 禁止！
```

## ✅ 正确的操作

```bash
# ✅ 正确：启动所有服务
docker-compose up -d

# ✅ 正确：查看服务状态
docker-compose ps

# ✅ 正确：查看日志
docker-compose logs -f backend

# ✅ 正确：重启服务
docker-compose restart backend

# ✅ 正确：重新构建并启动
docker-compose up -d --build
```

## 📋 服务端口映射

| 服务 | 容器内端口 | 宿主机端口 | 访问地址 |
|------|-----------|-----------|---------|
| **Backend** | 8000 | **18888** | http://localhost:18888 |
| **Frontend** | 5173 | **13000** | http://localhost:13000 |
| **PostgreSQL** | 5432 | **5433** | localhost:5433 |
| **Redis** | 6379 | **6380** | localhost:6380 |

**重要**: 
- 前端配置必须使用 `http://localhost:18888`
- 数据库连接使用 `localhost:5433`
- Redis连接使用 `localhost:6380`

## 🔧 配置文件检查清单

### 前端配置
```bash
# frontend/.env
VITE_API_URL=http://localhost:18888  # ✅ 必须是 18888
```

### Docker配置
```yaml
# docker-compose.yml
backend:
  ports:
    - "0.0.0.0:18888:8000"  # ✅ 外部18888，内部8000
```

## 🛠️ 常见任务

### 0. 端口一致性检查（新增！）
```bash
# 检查所有文件中的端口配置
chmod +x check_ports.sh
./check_ports.sh

# 会自动修复以下文件：
# - Python测试脚本 (*.py)
# - 前端配置 (frontend/.env)
# - Shell脚本提示
```

### 1. 启动整个系统
```bash
# 完整启动
docker-compose up -d

# 查看状态
docker-compose ps

# 预期输出：
# bidding_backend   running   0.0.0.0:18888->8000/tcp
# bidding_postgres  running   0.0.0.0:5433->5432/tcp
# bidding_redis     running   0.0.0.0:6380->6379/tcp
```

### 2. 代码更新后重新构建
```bash
# 停止服务
docker-compose down

# 重新构建（包含最新代码）
docker-compose build backend

# 启动服务
docker-compose up -d

# 验证
docker-compose logs -f backend
```

### 3. 查看服务日志
```bash
# 后端日志
docker-compose logs -f backend

# 数据库日志
docker-compose logs -f postgres

# 所有日志
docker-compose logs -f
```

### 4. 进入容器调试
```bash
# 进入后端容器
docker-compose exec backend bash

# 在容器内检查
ls -la
python -c "import routers.knowledge; print('OK')"
```

### 5. 重启特定服务
```bash
# 只重启后端
docker-compose restart backend

# 重启所有服务
docker-compose restart
```

## 🔍 问题排查

### 问题1: 知识库API返回404

**症状**: 
```bash
curl http://localhost:18888/api/knowledge/statistics
# 返回: {"detail":"Not Found"}
```

**原因**: Docker容器中的代码是旧版本

**解决**:
```bash
# 1. 停止服务
docker-compose down

# 2. 重新构建（包含最新knowledge.py）
docker-compose build backend

# 3. 启动服务
docker-compose up -d

# 4. 验证
docker-compose exec backend ls -la routers/knowledge.py
```

### 问题2: 前端连接失败

**症状**: 浏览器控制台显示 `ERR_CONNECTION_REFUSED`

**检查**:
```bash
# 1. 检查后端是否运行
docker-compose ps backend

# 2. 检查端口映射
docker-compose port backend 8000
# 应该显示: 0.0.0.0:18888

# 3. 检查前端配置
cat frontend/.env | grep VITE_API_URL
# 应该是: VITE_API_URL=http://localhost:18888
```

### 问题3: 数据库连接失败

**症状**: 后端日志显示数据库连接错误

**检查**:
```bash
# 1. 检查数据库是否运行
docker-compose ps postgres

# 2. 测试连接
docker-compose exec postgres psql -U postgres -d bidding_db -c "SELECT 1"

# 3. 查看环境变量
docker-compose exec backend env | grep DB_
```

## 📝 开发工作流

### 日常开发流程
```bash
# 1. 早上启动系统
docker-compose up -d

# 2. 开发代码
vim backend/routers/knowledge.py

# 3. 如果修改了Python代码，重新构建
docker-compose up -d --build backend

# 4. 如果只是配置修改，重启即可
docker-compose restart backend

# 5. 查看日志验证
docker-compose logs -f backend

# 6. 下班停止服务（可选）
docker-compose down
```

### 添加新依赖
```bash
# 1. 修改 backend/requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# 2. 重新构建镜像
docker-compose build backend

# 3. 启动服务
docker-compose up -d
```

### 数据库迁移
```bash
# 1. 修改 init_database.sql

# 2. 删除旧数据（慎重！）
docker-compose down -v  # -v 删除卷

# 3. 重新启动（自动初始化）
docker-compose up -d
```

## 🎯 快速命令参考

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 进入容器
docker-compose exec backend bash

# 重启服务
docker-compose restart backend

# 查看端口
docker-compose port backend 8000
```

## ⚠️ 注意事项

1. **绝不绕过Docker** - 所有服务必须通过docker-compose启动
2. **端口一致性** - 前端必须使用18888端口
3. **代码更新** - 修改代码后必须重新构建
4. **环境变量** - 修改.env后必须重启容器
5. **数据持久化** - 使用Docker volumes，不要直接操作宿主机文件

## ✅ 验证清单

开发前检查：
- [ ] `docker-compose ps` 显示所有服务running
- [ ] `frontend/.env` 配置为 `http://localhost:18888`
- [ ] `curl http://localhost:18888/` 返回API信息

代码修改后：
- [ ] 运行 `docker-compose build backend`
- [ ] 运行 `docker-compose up -d`
- [ ] 检查 `docker-compose logs -f backend`
- [ ] 测试API: `curl http://localhost:18888/api/knowledge/statistics`

部署前检查：
- [ ] 所有服务通过Docker运行
- [ ] 没有本地运行的服务
- [ ] 端口配置正确
- [ ] 环境变量配置完整

## 🚀 下一步行动

**立即执行**:
```bash
# 1. 停止任何本地运行的服务
killall python  # 如果有的话
killall node    # 如果有的话

# 2. 重新构建并启动Docker服务
docker-compose down
docker-compose build backend
docker-compose up -d

# 3. 验证服务
docker-compose ps
curl http://localhost:18888/

# 4. 测试知识库API
python test_port_18888.py
```

---

**记住：Docker优先，永远不要绕过！**
