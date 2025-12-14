# 🌐 标书智能系统 - 局域网部署指南

> **部署模式**: 本机作为局域网服务器，所有数据本地存储  
> **适用场景**: 公司内网、团队协作、数据隐私保护  
> **更新日期**: 2025-12-08

---

## 📋 目录

- [系统要求](#系统要求)
- [快速部署](#快速部署)
- [配置说明](#配置说明)
- [局域网访问](#局域网访问)
- [数据管理](#数据管理)
- [常见问题](#常见问题)
- [安全建议](#安全建议)

---

## 🖥️ 系统要求

### 硬件要求
- **CPU**: 4核心以上（推荐8核心）
- **内存**: 8GB以上（推荐16GB）
- **磁盘**: 至少50GB可用空间（数据量大时需更多）
- **网络**: 千兆局域网（建议有线连接）

### 软件要求
- **操作系统**: macOS 12.0+ / Linux / Windows 10+
- **Docker Desktop**: 最新版本
- **Docker Compose**: V2 版本

### 网络要求
- 服务器和客户端在同一局域网
- 路由器支持设备互联（非客户端隔离模式）
- 防火墙允许端口 5173 和 8000

---

## 🚀 快速部署

### 第一步：准备配置文件

```bash
# 1. 进入项目目录
cd /path/to/bidding-intelligence-system

# 2. 复制局域网配置模板
cp .env.lan .env

# 3. 编辑配置文件（重要！）
nano .env
```

**必须修改的配置项**:

```env
# 修改数据库密码（强密码）
DB_PASSWORD=YourStrongPassword123!

# 修改JWT密钥（随机字符串）
SECRET_KEY=your-random-secret-key-32-chars-long

# 填写AI模型API密钥（至少填一个）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
QWEN_API_KEY=sk-your-qwen-api-key
OPENAI_API_KEY=sk-your-openai-api-key  # 可选
```

**可选修改的配置项**:

```env
# 数据存储路径（默认在项目目录下）
HOST_DATA_POSTGRES=/Users/yourname/bidding-data/postgres
HOST_DATA_REDIS=/Users/yourname/bidding-data/redis
HOST_DATA_UPLOADS=/Users/yourname/bidding-data/uploads
HOST_DATA_LOGS=/Users/yourname/bidding-data/logs

# 端口配置（如有冲突可修改）
PORT=8000              # 后端API端口
FRONTEND_PORT=5173     # 前端端口
DB_EXTERNAL_PORT=5433  # PostgreSQL外部端口
REDIS_EXTERNAL_PORT=6380  # Redis外部端口
```

### 第二步：初始化数据目录（可选）

如果配置了自定义数据目录，运行初始化脚本：

```bash
# 自动创建数据存储目录
./init-data-dirs.sh
```

该脚本会：
- 创建所有必需的数据目录
- 设置正确的权限
- 更新 .env 文件中的路径

### 第三步：一键部署

```bash
# 运行部署脚本
./deploy-lan.sh
```

部署脚本会自动：
1. ✅ 检查 Docker 环境
2. ✅ 验证配置文件
3. ✅ 检测局域网 IP
4. ✅ 检查端口占用
5. ✅ 构建并启动所有服务
6. ✅ 执行健康检查
7. ✅ 显示访问地址

### 第四步：验证部署

部署成功后，访问以下地址验证：

**本机访问**:
- 前端: http://localhost:5173
- 后端API文档: http://localhost:8000/docs

**局域网访问** (假设服务器IP是 192.168.1.100):
- 前端: http://192.168.1.100:5173
- 后端: http://192.168.1.100:8000

**默认登录凭据**:
- 用户名: `admin`
- 密码: `admin123`

---

## ⚙️ 配置说明

### 端口说明

| 服务 | 容器内端口 | 主机端口 | 说明 |
|------|-----------|---------|------|
| 前端 | 5173 | 5173 | 用户访问界面 |
| 后端API | 8000 | 8000 | REST API服务 |
| PostgreSQL | 5432 | 5433 | 数据库（避免与本地冲突） |
| Redis | 6379 | 6380 | 缓存服务（避免与本地冲突） |

### 数据存储位置

默认情况下，所有数据存储在 `./data/` 目录下：

```
./data/
├── postgres/    # 数据库文件（24张表+向量索引）
├── redis/       # Redis持久化数据
├── uploads/     # 用户上传的标书文件
└── logs/        # 系统日志文件
```

**自定义存储位置**:

编辑 `.env` 文件中的路径：

```env
HOST_DATA_POSTGRES=/Volumes/Data/bidding/postgres
HOST_DATA_REDIS=/Volumes/Data/bidding/redis
HOST_DATA_UPLOADS=/Volumes/Data/bidding/uploads
HOST_DATA_LOGS=/Volumes/Data/bidding/logs
```

---

## 🌐 局域网访问配置

### 1. 获取服务器局域网IP

**macOS**:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# 示例输出: inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
```

**Linux**:
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

**Windows**:
```cmd
ipconfig
# 查找 "IPv4 地址"
```

### 2. 配置防火墙（macOS）

**方法一：系统偏好设置（推荐）**

1. 打开 **系统偏好设置** → **安全性与隐私** → **防火墙**
2. 点击 **防火墙选项**
3. 确保 **Docker Desktop** 或 **com.docker.backend** 允许传入连接
4. 如果列表中没有，点击 **+** 添加 Docker Desktop

**方法二：命令行配置**

```bash
# 允许端口 5173（前端）
sudo pfctl -f /etc/pf.conf
sudo pfctl -e

# 或者临时关闭防火墙测试
sudo pfctl -d
```

### 3. 客户端访问

在局域网内的其他设备上：

1. 打开浏览器
2. 访问 `http://服务器IP:5173`
3. 使用默认凭据登录

**示例**:
- 服务器IP: `192.168.1.100`
- 前端访问: `http://192.168.1.100:5173`
- API访问: `http://192.168.1.100:8000`

### 4. 移动设备访问

手机/平板连接到同一WiFi后，直接访问服务器IP即可。

**推荐浏览器**:
- iOS: Safari
- Android: Chrome

---

## 💾 数据管理

### 备份数据

**完整备份**:
```bash
# 停止服务
docker compose -f docker-compose.lan.yml down

# 打包数据目录
tar -czf bidding-backup-$(date +%Y%m%d).tar.gz ./data/

# 重启服务
./deploy-lan.sh
```

**仅备份数据库**:
```bash
# 导出PostgreSQL数据
docker compose -f docker-compose.lan.yml exec postgres \
  pg_dump -U postgres bidding_db > backup-$(date +%Y%m%d).sql
```

### 恢复数据

**从完整备份恢复**:
```bash
# 停止服务
docker compose -f docker-compose.lan.yml down

# 删除旧数据
rm -rf ./data/

# 解压备份
tar -xzf bidding-backup-20251208.tar.gz

# 重启服务
./deploy-lan.sh
```

**从SQL备份恢复**:
```bash
# 导入数据库
docker compose -f docker-compose.lan.yml exec -T postgres \
  psql -U postgres bidding_db < backup-20251208.sql
```

### 数据清理

**清理上传文件**:
```bash
# 删除30天前的文件
find ./data/uploads/ -type f -mtime +30 -delete
```

**清理日志**:
```bash
# 保留最近7天的日志
find ./data/logs/ -type f -name "*.log" -mtime +7 -delete
```

---

## 🔧 常用命令

### 服务管理

```bash
# 启动服务
./deploy-lan.sh

# 停止服务
docker compose -f docker-compose.lan.yml down

# 重启服务
docker compose -f docker-compose.lan.yml restart

# 重新构建并启动
docker compose -f docker-compose.lan.yml up -d --build

# 查看服务状态
docker compose -f docker-compose.lan.yml ps
```

### 日志查看

```bash
# 查看所有服务日志
docker compose -f docker-compose.lan.yml logs -f

# 查看后端日志
docker compose -f docker-compose.lan.yml logs -f backend

# 查看数据库日志
docker compose -f docker-compose.lan.yml logs -f postgres

# 查看最近100行日志
docker compose -f docker-compose.lan.yml logs --tail=100
```

### 数据库操作

```bash
# 进入数据库容器
docker compose -f docker-compose.lan.yml exec postgres bash

# 连接数据库
docker compose -f docker-compose.lan.yml exec postgres \
  psql -U postgres -d bidding_db

# 查看数据库大小
docker compose -f docker-compose.lan.yml exec postgres \
  psql -U postgres -d bidding_db -c "SELECT pg_size_pretty(pg_database_size('bidding_db'));"

# 查看表数量
docker compose -f docker-compose.lan.yml exec postgres \
  psql -U postgres -d bidding_db -c "\dt"
```

---

## ❓ 常见问题

### 1. 客户端无法访问服务器

**症状**: 浏览器无法打开 `http://服务器IP:5173`

**排查步骤**:

1. **检查服务是否运行**
   ```bash
   docker compose -f docker-compose.lan.yml ps
   # 所有服务应显示 "Up"
   ```

2. **测试本机访问**
   ```bash
   curl http://localhost:5173
   # 应返回HTML内容
   ```

3. **检查防火墙**
   ```bash
   # macOS 检查防火墙状态
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   
   # 测试端口是否可访问
   nc -zv 服务器IP 5173
   ```

4. **检查网络连通性**
   ```bash
   # 在客户端ping服务器
   ping 服务器IP
   
   # 检查客户端和服务器是否在同一网段
   ```

5. **检查路由器设置**
   - 确保路由器未开启客户端隔离（AP隔离）
   - 检查是否有访客网络限制

### 2. 文件上传失败

**症状**: 上传文件时提示 422 错误或上传失败

**解决方案**:

1. **检查上传目录权限**
   ```bash
   ls -la ./data/uploads/
   # 确保目录可写
   
   chmod -R 755 ./data/uploads/
   ```

2. **检查磁盘空间**
   ```bash
   df -h ./data/
   # 确保有足够的可用空间
   ```

3. **检查文件大小限制**
   ```bash
   # 在.env中调整
   MAX_FILE_SIZE=104857600  # 100MB
   ```

### 3. 数据库连接失败

**症状**: 后端日志显示 "database connection failed"

**解决方案**:

1. **检查数据库服务**
   ```bash
   docker compose -f docker-compose.lan.yml logs postgres
   ```

2. **重启数据库**
   ```bash
   docker compose -f docker-compose.lan.yml restart postgres
   ```

3. **检查密码配置**
   ```bash
   # 确保.env中的DB_PASSWORD与docker-compose.lan.yml一致
   grep DB_PASSWORD .env
   ```

### 4. 前端页面空白

**症状**: 访问前端地址显示空白页

**解决方案**:

1. **检查浏览器控制台**
   - 按 F12 打开开发者工具
   - 查看 Console 标签是否有错误

2. **检查API地址配置**
   ```bash
   # 前端构建时需要正确的API地址
   # 重新构建前端
   docker compose -f docker-compose.lan.yml up -d --build frontend
   ```

3. **清除浏览器缓存**
   - Ctrl+Shift+Delete（Windows/Linux）
   - Cmd+Shift+Delete（macOS）

### 5. 性能问题

**症状**: 系统响应缓慢，文件解析时间过长

**优化方案**:

1. **增加资源限制**
   ```yaml
   # 在docker-compose.lan.yml中添加
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '4'
             memory: 4G
   ```

2. **调整并发数**
   ```env
   # 在.env中修改
   MAX_CONCURRENT_TASKS=10
   ```

3. **启用GPU加速（如果有独立显卡）**
   ```env
   OCR_USE_GPU=true
   ```

---

## 🔒 安全建议

### 生产环境部署

1. **修改默认密码**
   - 数据库密码：`DB_PASSWORD`
   - JWT密钥：`SECRET_KEY`
   - 系统登录密码（首次登录后立即修改）

2. **限制访问来源**
   ```env
   # 只允许特定IP段访问
   CORS_ORIGINS=http://192.168.1.0/24:5173
   ```

3. **启用HTTPS（可选）**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书

4. **定期备份**
   - 设置自动备份脚本
   - 异地存储备份文件

5. **监控日志**
   ```bash
   # 查看异常访问
   docker compose -f docker-compose.lan.yml logs backend | grep ERROR
   ```

6. **更新系统**
   ```bash
   # 定期拉取最新镜像
   docker compose -f docker-compose.lan.yml pull
   docker compose -f docker-compose.lan.yml up -d
   ```

---

## 📞 技术支持

如遇到其他问题，请：

1. 查看系统日志：`docker compose -f docker-compose.lan.yml logs`
2. 查看GitHub Issues
3. 联系系统管理员

---

## 📝 附录

### A. 完整配置示例

参见 `.env.lan` 文件

### B. 数据库表结构

系统包含 24 张核心表：
- 文件表（files, uploaded_files）
- 章节表（chapters）
- 逻辑规则表（8张）
- 知识图谱表（9张）
- 评估表（4张）

详见 `backend/init_database.sql`

### C. API文档

访问 `http://服务器IP:8000/docs` 查看完整API文档

---

**最后更新**: 2025-12-08  
**版本**: 1.0.0
