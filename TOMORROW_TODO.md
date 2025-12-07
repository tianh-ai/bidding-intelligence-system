# 明天待验证清单 (Mac mini)

## 📅 日期：2025年12月8日晚 → 2025年12月9日

---

## ✅ 今日已完成（已推送到 GitHub）

### 后端修复
- [x] 文件上传 422 错误修复（`frontend/src/utils/axios.ts` - 移除 FormData 默认 Content-Type）
- [x] 数据库事务异常自动回滚（`backend/database/connection.py`）
- [x] `uploaded_files` 表字段迁移补全（`backend/routers/files.py`）
- [x] Docker backend 禁用热重载避免连接中断（`backend/Dockerfile`, `docker-compose.yml`）

### 前端优化
- [x] Grok 暗色主题实现
- [x] 三栏可调整宽度布局（`MainLayout.tsx`）
- [x] AI 输入框扩大（`AIChatPanel.tsx` - minRows:3, maxRows:10）
- [x] 提示词管理页面完成
- [x] Admin 角色显示逻辑修正（`authStore.ts`）

### Docker 问题
- [x] 前端容器端口转发异常 → 已通过 `docker compose down + up` 解决

### 服务状态
- ✅ 后端健康检查：`http://localhost:8000/health` → 200 OK
- ✅ 前端页面加载：`http://localhost:5173` → 200 OK（curl 验证通过）

---

## 🎯 明天待验证事项（Mac mini）

### 1️⃣ 启动服务
```bash
# 进入项目目录
cd /path/to/bidding-intelligence-system

# 拉取最新代码
git pull origin main

# 启动 Docker 服务
docker compose up -d

# 等待服务就绪（约 10 秒）
sleep 10

# 验证服务状态
curl http://localhost:8000/health  # 应返回 {"status":"healthy","service":"bidding-system"}
curl http://localhost:5173         # 应返回 HTML（包含 <title>投标智能系统</title>）
```

### 2️⃣ 浏览器功能验证

#### 🔐 登录测试
1. 打开浏览器访问：`http://localhost:5173`
2. 应该看到登录页面（Grok 暗色主题）
3. **如果 Admin 角色显示为"访客"**：
   - 按 `F12` 打开开发者工具
   - 切换到 `Application` → `Local Storage` → `http://localhost:5173`
   - 删除 `auth-storage` 键
   - 刷新页面重新登录
4. 使用凭据登录：
   - 用户名：`admin`
   - 密码：`admin123`
5. ✅ **验证点**：Header 右上角应显示 **"管理员"** 标签（而非"访客"）

#### 📤 文件上传测试（**核心验证**）
1. 点击侧边栏 **"文件上传"**
2. 准备测试文件（PDF、Word、Excel、TXT 均可）
3. 拖拽或点击上传文件
4. ✅ **验证点 1**：上传成功后应显示：
   - 文件大小统计（如 "总大小: 1.2 MB"）
   - 文件数量（如 "共 3 个文件"）
   - 文件列表（带文件名、大小、上传时间）
5. ✅ **验证点 2**：**不应再出现 422 错误**
6. ✅ **验证点 3**：控制台无报错（`Network` 标签查看请求返回 200）

#### 📚 知识库存档页面测试
1. 点击侧边栏 **"知识库存档"** 或 **"文件总结"**
2. ✅ **验证点 1**：页面应显示：
   - 左侧目录树（已上传文件按类型/日期分组）
   - 右侧统计面板（总文件数、总大小、各类型占比）
3. ✅ **验证点 2**：刷新页面后数据仍然存在（证明数据库持久化成功）

#### 🎨 界面交互测试
1. **三栏布局调整**：
   - 拖动左侧边栏分隔线（应能调整宽度，最小 200px）
   - 点击右上角 AI 助手图标打开右侧面板
   - 拖动 AI 面板分隔线（应能调整宽度，最小 300px）
   
2. **AI 输入框**：
   - 打开 AI 助手
   - 验证输入框默认 3 行高度（不再是 1 行）
   - 测试 `Shift+Enter` 换行
   - 测试 `Enter` 发送消息

3. **提示词管理**：
   - 点击侧边栏 **"提示词管理"**
   - 测试新建、编辑、删除提示词功能

---

## ⚠️ 可能遇到的问题及解决方案

### 问题 1：`docker compose` 命令不可用
**现象**：提示 `command not found: docker compose`

**解决**：
```bash
# 检查 Docker Desktop 是否安装
open -a Docker

# 或使用旧版命令
docker-compose up -d
```

### 问题 2：端口被占用
**现象**：`bind: address already in use`

**解决**：
```bash
# 查看占用端口的进程
lsof -i :5173  # 前端
lsof -i :8000  # 后端

# 停止冲突进程（PID 替换为实际值）
kill -9 <PID>

# 或更改端口（修改 docker-compose.yml）
```

### 问题 3：前端页面空白或无法加载
**现象**：浏览器显示 "ERR_EMPTY_RESPONSE"

**解决**：
```bash
# 重启前端容器（刷新端口转发）
docker compose down frontend
docker compose up -d frontend

# 等待 5 秒后重新访问
```

### 问题 4：数据库连接失败
**现象**：后端日志显示 "connection refused"

**解决**：
```bash
# 检查 PostgreSQL 容器健康状态
docker compose ps

# 重启数据库容器
docker compose restart postgres

# 查看数据库日志
docker logs bidding_postgres
```

---

## 📊 预期验证结果

| 功能项 | 预期结果 | 验证方法 |
|--------|---------|---------|
| **服务启动** | Backend + Frontend 正常运行 | `curl` 命令返回 200 |
| **登录** | Admin 显示"管理员" | 浏览器 Header 检查 |
| **文件上传** | 上传成功 + 显示统计 | 拖拽文件后查看响应 |
| **知识库页面** | 显示目录树 + 统计面板 | 页面元素检查 |
| **三栏布局** | 可拖动调整宽度 | 鼠标拖拽测试 |
| **AI 输入框** | 默认 3 行高度 | 视觉检查 |

---

## 🔗 相关资源

- **GitHub 仓库**：https://github.com/tianh-ai/bidding-intelligence-system
- **最新 Commit**：`a223bd2` (2025-12-08)
- **测试账号**：
  - 用户名：`admin`
  - 密码：`admin123`

---

## 📝 验证后需记录的信息

请在验证后填写：

- [ ] 服务启动是否成功？
- [ ] 文件上传功能是否正常？
- [ ] 上传后统计数据是否显示？
- [ ] 知识库页面目录是否展示？
- [ ] Admin 角色是否正确显示？
- [ ] 遇到的新问题（如有）：

---

**最后更新时间**：2025年12月8日 凌晨  
**推送状态**：✅ 已推送到 GitHub main 分支  
**下次工作环境**：Mac mini（单位）
