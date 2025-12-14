# 🚀 标书智能系统 - 局域网部署快速入门

## ⚡ 三步快速部署

### 第一步：配置环境变量（5分钟）

```bash
# 1. 复制配置文件
cp .env.lan .env

# 2. 编辑配置（必须修改这三项）
nano .env
```

**必须修改的配置**:
```env
DB_PASSWORD=YourStrongPassword123!        # 数据库密码
SECRET_KEY=your-random-32-char-secret     # JWT密钥
DEEPSEEK_API_KEY=sk-your-api-key          # AI模型密钥
```

保存后按 `Ctrl+X` → `Y` → `Enter`

---

### 第二步：一键部署（3分钟）

```bash
./deploy-lan.sh
```

等待脚本自动完成：
- ✅ 检查Docker环境
- ✅ 创建数据目录
- ✅ 启动所有服务
- ✅ 健康检查

---

### 第三步：访问系统

**本机访问**:
```
前端: http://localhost:5173
API文档: http://localhost:8000/docs
```

**局域网访问** (脚本会显示你的IP):
```
前端: http://你的IP:5173
后端: http://你的IP:8000
```

**默认登录**:
- 用户名: `admin`
- 密码: `admin123`

---

## 📱 客户端访问（手机/其他电脑）

1. 连接到同一WiFi
2. 打开浏览器访问 `http://服务器IP:5173`
3. 使用上面的凭据登录

---

## 🔧 常用命令

```bash
# 查看服务状态
docker compose -f docker-compose.lan.yml ps

# 查看日志
docker compose -f docker-compose.lan.yml logs -f

# 停止服务
docker compose -f docker-compose.lan.yml down

# 重启服务
./deploy-lan.sh
```

---

## ⚠️ 防火墙配置（如果局域网无法访问）

**macOS**:
1. 系统偏好设置 → 安全性与隐私 → 防火墙
2. 防火墙选项 → 允许 Docker Desktop

**Windows**:
1. Windows Defender 防火墙 → 允许应用通过防火墙
2. 勾选 Docker Desktop 的"专用"和"公用"

---

## 💾 数据存储位置

所有数据默认存储在：
```
./data/
├── postgres/    # 数据库
├── redis/       # 缓存
├── uploads/     # 上传文件
└── logs/        # 日志
```

**备份数据**:
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz ./data/
```

---

## 📚 详细文档

- 完整部署指南: [LAN_DEPLOYMENT_GUIDE.md](LAN_DEPLOYMENT_GUIDE.md)
- 系统介绍: [README.md](README.md)
- Docker使用: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)

---

## ❓ 遇到问题？

1. 查看日志: `docker compose -f docker-compose.lan.yml logs`
2. 检查服务: `docker compose -f docker-compose.lan.yml ps`
3. 参考故障排查: [LAN_DEPLOYMENT_GUIDE.md#常见问题](LAN_DEPLOYMENT_GUIDE.md#常见问题)

---

**祝您使用愉快！** 🎉
