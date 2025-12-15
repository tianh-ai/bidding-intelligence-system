# 🚀 知识库显示问题 - 快速解决

> **一键修复，3分钟搞定**

---

## ⚡ 立即执行（最快）

```bash
# 一键修复所有问题
chmod +x fix_knowledge_docker.sh
./fix_knowledge_docker.sh
```

**完成！** 然后：
1. 打开 http://localhost:5173
2. 登录 (admin / bidding2024)
3. 上传文件
4. 查看知识库条目

---

## 🎯 问题原因

1. ❌ 后端在Docker中，端口是 **18888** (不是8000)
2. ❌ Docker容器中的代码可能是旧版本
3. ❌ 前端配置可能指向错误端口

---

## 📋 核心原则

> **🐳 所有服务必须通过Docker运行**
> 
> **🔌 前端必须使用端口18888**

详见: `DOCKER_PRINCIPLES.md`

---

## 🔧 手动修复（如需要）

### 步骤1：修复前端配置
```bash
# 编辑 frontend/.env
echo "VITE_API_URL=http://localhost:18888" > frontend/.env
```

### 步骤2：重新构建Docker
```bash
docker-compose down
docker-compose build backend
docker-compose up -d
```

### 步骤3：验证
```bash
# 测试后端
curl http://localhost:18888/

# 测试知识库API
python test_port_18888.py
```

---

## 🆘 常见问题

### Q: 前端连接失败？
**A**: 检查端口
```bash
# 查看Docker端口映射
docker-compose port backend 8000
# 应该显示: 0.0.0.0:18888

# 检查前端配置
cat frontend/.env | grep VITE_API_URL
# 应该是: http://localhost:18888
```

### Q: 知识库API返回404？
**A**: 重新构建Docker
```bash
docker-compose down
docker-compose build backend
docker-compose up -d
```

### Q: 登录失败？
**A**: 使用正确的账号
- 用户名: **admin**
- 密码: **bidding2024**

---

## 📚 相关文档

| 文档 | 用途 |
|------|------|
| `DOCKER_PRINCIPLES.md` | Docker使用原则（必读） |
| `KNOWLEDGE_FIX_PORT.md` | 端口问题详解 |
| `CODE_PROTECTION.md` | 代码保护规范 |
| `fix_knowledge_docker.sh` | 一键修复脚本 |
| `test_port_18888.py` | API测试脚本 |

---

## ✅ 验证清单

修复后检查：
- [ ] `docker-compose ps` 显示3个服务running
- [ ] `curl http://localhost:18888/` 返回API信息
- [ ] 浏览器能访问 http://localhost:5173
- [ ] 能成功登录 (admin / bidding2024)
- [ ] 上传文件后能看到知识库条目

---

## 🎯 服务端口速查

| 服务 | 访问地址 |
|------|---------|
| 前端 | http://localhost:5173 |
| 后端API | **http://localhost:18888** ← 重要！ |
| 数据库 | localhost:5433 |
| Redis | localhost:6380 |

---

**记住两点：**
1. 🐳 **只用Docker，不绕过**
2. 🔌 **后端端口是18888**

搞定！ 🎉
