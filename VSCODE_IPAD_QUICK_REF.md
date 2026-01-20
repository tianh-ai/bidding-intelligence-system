# 🎯 iPad VSCode 快速参考卡

> 一页纸快速查阅 - 打印或保存到 iPad 备用

---

## 🚀 三种方案速览

| 方案 | 网址 | 特点 | 适用场景 |
|------|------|------|---------|
| **GitHub Codespaces** | [github.com](https://github.com) → Code → Codespaces | 完整功能 + 免费额度 | 日常开发 ⭐⭐⭐⭐⭐ |
| **VSCode Web** | [vscode.dev](https://vscode.dev) | 完全免费 + 轻量 | 快速编辑 ⭐⭐⭐⭐ |
| **Code-Server** | 自己的服务器 | 完全控制 | 高级用户 ⭐⭐⭐ |

---

## ⚡ 快速启动

### Codespaces（推荐）
```
1. 打开 https://github.com/tianh-ai/bidding-intelligence-system
2. 点击绿色 "Code" 按钮 → "Codespaces" 标签
3. 点击 "Create codespace on main"
4. 等待 2-3 分钟初始化
5. 开始编码！
```

### VSCode Web（最快）
```
1. 直接访问:
   https://vscode.dev/github/tianh-ai/bidding-intelligence-system
   
2. 或在浏览器输入: vscode.dev
   然后打开远程仓库
```

---

## ⌨️ iPad 键盘快捷键

### 必备快捷键
```
⌘⇧P     命令面板（最重要！）
⌘P       快速打开文件
⌘F       当前文件查找
⌘⇧F      全局搜索
⌃`       打开/关闭终端
⌘B       显示/隐藏侧边栏
⌘S       保存
⌘,       设置
⌘W       关闭当前标签
⌘⇧E      资源管理器
⌘⇧G      源代码管理（Git）
```

### 编辑快捷键
```
⌘D       选择下一个匹配项
⌘⇧L      选择所有匹配项
⌥↑/↓     移动行
⌥⇧↑/↓    复制行
⌘/       切换行注释
⌘⇧K      删除行
⌘Enter   在下方插入行
⌘⇧Enter  在上方插入行
```

### 导航快捷键
```
F12      跳转到定义
⌥F12     查看定义
⇧F12     查找所有引用
⌘K ⌘0    折叠所有区域
⌘K ⌘J    展开所有区域
```

---

## 🔧 快速命令

### 检查和启动
```bash
# 验证端口配置（重要！）
./check_ports.sh

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 后端开发
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行服务
uvicorn main:app --host 0.0.0.0 --port 18888 --reload

# 运行测试
pytest tests/ -v

# 代码格式化
black .
ruff check .
```

### 前端开发
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
```

---

## 🌐 访问地址

### 本地/Codespace
```
前端:    http://localhost:13000
后端:    http://localhost:18888
API文档: http://localhost:18888/docs
数据库:  localhost:5433
Redis:   localhost:6380
```

### 端口映射（重要！）
```
18888 → 后端 API（不是 8000！）
13000 → 前端应用
5433  → PostgreSQL
6380  → Redis
```

---

## 📱 Safari 优化设置

```
Settings → Safari:
✅ Request Desktop Website → All Websites
✅ 禁用"阻止弹出窗口"（仅对 vscode.dev）
✅ 允许 JavaScript
✅ 清除历史记录和网站数据（如遇问题）
```

---

## 🔐 环境变量配置

### 必须设置（Codespaces Secrets）
```
OPENAI_API_KEY       - OpenAI API 密钥
DB_PASSWORD          - 数据库密码
```

### 可选设置
```
DEEPSEEK_API_KEY     - DeepSeek API（可选）
REDIS_PASSWORD       - Redis 密码
```

### 在 Codespace 中设置
```
1. GitHub Settings → Codespaces → Secrets
2. 点击 "New secret"
3. 输入名称和值
4. 选择仓库访问权限
```

---

## 🐛 快速故障排除

### 问题：无法连接服务
```bash
# 检查服务状态
docker-compose ps

# 重启所有服务
docker-compose restart

# 查看详细日志
docker-compose logs --tail=100
```

### 问题：端口冲突
```bash
# 运行端口检查脚本
./check_ports.sh

# 查看所有使用的端口
netstat -tulpn | grep -E '18888|13000|5433|6380'
```

### 问题：Codespace 很慢
```
1. 检查网络连接
2. 升级机器类型（2核 → 4核）
3. 重启 Codespace
4. 清除浏览器缓存
```

### 问题：代码没有保存
```
检查：
✅ 自动保存已开启（默认）
✅ 文件标签页没有 "●" 标记
✅ Git 面板显示更改

手动保存：⌘S
```

---

## 📦 常用代码片段

### 测试 API
```bash
# 健康检查
curl http://localhost:18888/health

# 列出文件
curl http://localhost:18888/api/files/list | jq

# 上传文件
curl -X POST http://localhost:18888/api/files/upload \
  -F "file=@test.pdf" \
  -F "file_type=tender"
```

### Git 操作
```bash
# 查看状态
git status

# 查看差异
git diff

# 暂存所有更改
git add .

# 提交
git commit -m "feat: your message"

# 推送
git push

# 拉取最新
git pull
```

---

## 💡 生产力技巧

### 1. 使用多光标编辑
```
⌘D 选择下一个相同内容
⌥⌘↑/↓ 在上方/下方添加光标
⌥+点击 在点击位置添加光标
```

### 2. 代码片段
```
输入 "if" 然后 Tab → 自动补全 if 语句
输入 "def" 然后 Tab → 自动补全函数定义
```

### 3. 命令面板（⌘⇧P）
```
> Format Document      - 格式化代码
> Transform to Upper   - 转大写
> Transform to Lower   - 转小写
> Sort Lines Ascending - 排序行
```

### 4. 快速导航
```
⌘P 然后:
  @符号名    → 跳转到符号
  :行号      → 跳转到行
  #搜索词    → 全局搜索
```

### 5. 使用内置终端
```
⌃`           打开终端
⌘K ⌘W        关闭终端
⌘\           拆分终端
终端右键菜单  → 新建终端、重命名等
```

---

## 🔗 重要链接

```
📖 完整指南:    VSCODE_IPAD_GUIDE.md
🐳 Docker 部署: DOCKER_GUIDE.md
⚙️  端口配置:    PORT_CONSISTENCY.md
🔒 代码保护:    CODE_PROTECTION.md
🏠 项目首页:    README.md
```

---

## ☁️ Codespace 配额管理

### 免费额度
```
120 核心小时/月
= 2核机器 × 60小时
= 4核机器 × 30小时
= 8核机器 × 15小时
```

### 节省技巧
```
✅ 不用时手动停止（30分钟自动停止）
✅ 使用最小满足需求的机器类型
✅ 定期删除不用的 Codespace
✅ 设置超时时间（Settings → Timeout）
```

### 查看使用情况
```
GitHub Settings → Billing and plans → Usage this month
```

---

## 📞 获取帮助

```
🐛 报告问题:
   https://github.com/tianh-ai/bidding-intelligence-system/issues

💬 讨论交流:
   https://github.com/tianh-ai/bidding-intelligence-system/discussions

📧 邮件支持:
   team@example.com
```

---

<div align="center">

**💡 提示**: 将此页面添加到 iPad 主屏幕，方便随时查阅！

Safari → 分享 → 添加到主屏幕

---

**最后更新**: 2026-01-20  
**版本**: v1.0

</div>
