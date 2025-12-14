# SSD 存储配置完成

## ✅ 完成事项

### 1. 存储位置配置
所有数据已配置存储到 SSD 盘：
```
/Volumes/ssd/files/bidding-system/
├── data/              # 数据库数据
│   ├── postgres/      # PostgreSQL 数据 (当前: 10MB, 25个表)
│   └── redis/         # Redis 数据 (当前: 1.46MB)
├── uploads/           # 上传文件
│   ├── temp/          # 临时文件
│   ├── parsed/        # 解析后的文件
│   └── archive/       # 归档文件
│       ├── 2024/
│       └── 2025/
├── logs/              # 日志文件
│   ├── backend/       # 后端日志
│   └── celery/        # Celery任务日志
└── backups/           # 备份文件
    ├── db/            # 数据库备份
    └── files/         # 文件备份
```

### 2. 磁盘状态
- **总容量**: 1.8TB
- **已使用**: 2.4MB
- **可用空间**: 1.8TB
- **使用率**: 1%

### 3. 服务状态
所有服务已成功启动并连接到 SSD 存储：

| 服务 | 状态 | 端口 | 存储位置 |
|------|------|------|----------|
| PostgreSQL | ✅ Healthy | 15432 | `/Volumes/ssd/files/bidding-system/data/postgres` |
| Redis | ✅ Healthy | 16379 | `/Volumes/ssd/files/bidding-system/data/redis` |
| 后端 API | ✅ Running | 18888 | 日志: `/Volumes/ssd/files/bidding-system/logs/backend` |
| Celery Worker | ✅ Running | - | 日志: `/Volumes/ssd/files/bidding-system/logs/celery` |
| 前端 | ✅ Running | 13000 | - |

### 4. 自动化脚本

#### 初始化存储目录
```bash
./init-ssd-storage.sh
```
- 自动创建所有必需的目录结构
- 设置正确的权限
- 生成 README 和 .gitignore

#### 检查存储状态
```bash
./check-ssd-storage.sh
```
- 检查 SSD 挂载状态
- 显示磁盘使用情况
- 检查各服务连接状态
- 显示数据库和 Redis 状态
- 提供存储建议

## 📝 重要说明

### 数据持久化
- ✅ 所有数据库数据存储在 SSD
- ✅ 所有上传文件存储在 SSD
- ✅ 所有日志文件存储在 SSD
- ✅ Docker 容器重启后数据不会丢失

### 访问地址
- **前端**: http://localhost:13000 或 http://局域网IP:13000
- **后端 API**: http://localhost:18888 或 http://局域网IP:18888
- **数据库**: localhost:15432 (用户: postgres, 密码见 .env.lan)
- **Redis**: localhost:16379

### 登录账号
- **管理员**: `admin / bidding2024`
- **普通用户**: `user / user2024`

## 🔧 常用维护命令

### 查看存储使用
```bash
# 查看总体使用情况
du -sh /Volumes/ssd/files/bidding-system/*

# 查看上传文件
ls -lh /Volumes/ssd/files/bidding-system/uploads/

# 查看归档文件
ls -lh /Volumes/ssd/files/bidding-system/uploads/archive/2025/
```

### 备份数据库
```bash
# 备份到 SSD 备份目录
docker exec bidding_postgres pg_dump -U postgres bidding_db > \
  /Volumes/ssd/files/bidding-system/backups/db/backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker exec -i bidding_postgres psql -U postgres bidding_db < backup.sql
```

### 清理临时文件
```bash
# 清理临时上传文件
rm -rf /Volumes/ssd/files/bidding-system/uploads/temp/*

# 清理旧日志（保留最近7天）
find /Volumes/ssd/files/bidding-system/logs -name "*.log" -mtime +7 -delete
```

### 查看日志
```bash
# 后端日志
tail -f /Volumes/ssd/files/bidding-system/logs/backend/*.log

# Docker 容器日志
docker logs -f bidding_backend
docker logs -f bidding_celery_worker
```

## ⚠️ 注意事项

### SSD 断开连接
如果 SSD 被意外断开：
1. 重新连接 SSD
2. 确认挂载到 `/Volumes/ssd`
3. 重启 Docker 容器：
   ```bash
   docker compose -f docker-compose.lan.yml restart
   ```

### 迁移到新 SSD
如果需要更换 SSD：
1. 停止所有服务：
   ```bash
   docker compose -f docker-compose.lan.yml down
   ```
2. 复制整个目录到新 SSD：
   ```bash
   cp -R /Volumes/ssd/files/bidding-system /Volumes/新SSD/files/
   ```
3. 更新 `.env.lan` 中的路径
4. 重新启动服务

### 磁盘空间监控
建议：
- 定期运行 `./check-ssd-storage.sh` 检查空间
- 当使用率超过 70% 时，清理旧的归档文件
- 定期备份重要数据到其他位置

## 🚀 下一步

系统已完全配置完成，可以开始使用：

1. **访问前端**: http://localhost:13000
2. **登录**: 使用 `admin / bidding2024`
3. **上传文件**: 文件会自动存储到 SSD 的 uploads 目录
4. **查看处理状态**: 文件会经过解析、归档、向量化等流程
5. **监控存储**: 定期运行 `./check-ssd-storage.sh`

---

**配置完成时间**: $(date '+%Y-%m-%d %H:%M:%S')
**SSD 可用空间**: 1.8TB
**服务状态**: 全部正常运行
