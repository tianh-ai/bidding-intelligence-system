# 📱 在 iPad 上使用 VSCode 开发指南

> **完整教程**: 如何在 iPad 上使用 VSCode 开发标书智能系统  
> 📄 **[快速参考卡](VSCODE_IPAD_QUICK_REF.md)** - 一页纸速查，可打印或保存到 iPad

---

## 📖 概述

本指南将帮助您在 iPad 上使用 VSCode 进行开发工作。iPad 虽然不能直接运行桌面版 VSCode，但通过以下方法可以获得完整的开发体验：

### 可用方案对比

| 方案 | 推荐度 | 成本 | 功能完整度 | 性能 | 网络要求 |
|------|--------|------|-----------|------|---------|
| **GitHub Codespaces** | ⭐⭐⭐⭐⭐ | 免费额度 + 付费 | 100% | 优秀 | 稳定网络 |
| **VSCode for Web (vscode.dev)** | ⭐⭐⭐⭐ | 完全免费 | 80% | 良好 | 稳定网络 |
| **Code-server (自托管)** | ⭐⭐⭐ | 服务器成本 | 95% | 取决于服务器 | 稳定网络 |
| **SSH + Terminus/Blink** | ⭐⭐ | 免费/付费 | 60% | 一般 | 稳定网络 |

---

## 🚀 方案一：GitHub Codespaces（推荐）

### 优点
- ✅ **完整的 VSCode 体验** - 所有扩展和功能
- ✅ **预配置环境** - Docker、Python、Node.js 等
- ✅ **强大的计算资源** - 2-32核 CPU，最高 64GB 内存
- ✅ **免费额度** - 每月 120 核心小时（约 60 小时 2核机器）
- ✅ **自动保存和同步** - 代码自动保存到 GitHub

### 使用步骤

#### 1. 在 iPad 上访问 GitHub

打开 Safari 或 Chrome 浏览器，访问：
```
https://github.com/tianh-ai/bidding-intelligence-system
```

#### 2. 创建 Codespace

- 点击仓库页面上的绿色 **Code** 按钮
- 选择 **Codespaces** 标签
- 点击 **Create codespace on main**（或其他分支）
- 等待环境初始化（首次约 2-3 分钟）

#### 3. 开始开发

环境启动后，您将看到完整的 VSCode 界面：
- 左侧：文件浏览器
- 中间：代码编辑器
- 底部：终端
- 右侧：扩展和设置

#### 4. 运行项目

在终端中运行：

```bash
# 检查端口配置
./check_ports.sh

# 启动 Docker 服务（如果 Codespace 支持 Docker）
docker-compose up -d

# 或者使用本地开发模式
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 18888 --reload
```

#### 5. 访问应用

- Codespaces 会自动转发端口
- 点击终端中显示的 URL 或使用"端口"面板
- 前端: `http://localhost:13000`
- 后端: `http://localhost:18888`

### 💡 Codespaces 优化建议

#### 保持 Codespace 活跃
Codespace 在 30 分钟无活动后会自动暂停。建议：
- 定期保存代码（自动保存已开启）
- 长时间离开前手动停止 Codespace
- 恢复时数据和环境都会保留

#### 选择合适的机器类型
```
2 核心 8GB RAM  → 轻量开发（免费额度足够）
4 核心 16GB RAM → 标准开发
8 核心 32GB RAM → 重度开发（AI 训练）
```

#### 安装常用扩展
Codespace 会自动安装 `.vscode/extensions.json` 中的扩展，或手动安装：
- Python
- ESLint
- Prettier
- Docker
- GitLens

---

## 🌐 方案二：VSCode for Web (vscode.dev)

### 优点
- ✅ **完全免费** - 无需付费
- ✅ **即开即用** - 无需配置
- ✅ **轻量级** - 不占用服务器资源
- ⚠️ **限制**: 无法运行服务器或终端命令

### 使用步骤

#### 1. 访问 vscode.dev

在 iPad 浏览器中打开：
```
https://vscode.dev
```

#### 2. 打开 GitHub 仓库

两种方式：

**方式 A: 直接 URL**
```
https://vscode.dev/github/tianh-ai/bidding-intelligence-system
```

**方式 B: 在 vscode.dev 中打开**
- 点击左上角 "打开远程仓库"
- 输入: `tianh-ai/bidding-intelligence-system`
- 选择分支

#### 3. 编辑代码

您可以：
- ✅ 浏览和编辑代码
- ✅ 提交更改到 GitHub
- ✅ 创建和切换分支
- ✅ 查看文件差异
- ❌ 无法运行终端命令
- ❌ 无法启动开发服务器

### 💡 vscode.dev 使用技巧

#### 同步设置
使用 GitHub 账号登录，同步：
- 主题和外观
- 键盘快捷键
- 扩展设置

#### 配合 GitHub Actions
由于无法本地运行，可以：
1. 在 vscode.dev 编辑代码
2. 提交到 GitHub
3. GitHub Actions 自动运行测试和部署

---

## 🖥️ 方案三：自托管 Code-Server

### 适用场景
- 有自己的服务器或云主机
- 需要完整的终端访问
- 希望更灵活的配置

### 部署步骤

#### 1. 在服务器上安装 code-server

```bash
# 使用安装脚本
curl -fsSL https://code-server.dev/install.sh | sh

# 或使用 Docker
docker run -d \
  --name code-server \
  -p 8080:8080 \
  -v "$HOME/.config:/home/coder/.config" \
  -v "$PWD:/home/coder/project" \
  -e "PASSWORD=your-password" \
  codercom/code-server:latest
```

#### 2. 配置访问

编辑 `~/.config/code-server/config.yaml`:
```yaml
bind-addr: 0.0.0.0:8080
auth: password
password: your-secure-password
cert: false
```

#### 3. 启动服务

```bash
sudo systemctl enable --now code-server@$USER
```

#### 4. 在 iPad 上访问

打开浏览器访问:
```
http://your-server-ip:8080
```

#### 5. 配置反向代理（推荐）

使用 Nginx 配置 HTTPS:
```nginx
server {
    listen 80;
    server_name code.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name code.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection upgrade;
        proxy_set_header Accept-Encoding gzip;
    }
}
```

---

## ⚙️ iPad 开发环境配置

### Safari 浏览器设置

#### 1. 启用桌面模式
Settings → Safari → Request Desktop Website → All Websites

#### 2. 禁用自动缩放
在 VSCode 界面中双击并调整缩放级别，Safari 会记住设置

### 外接键盘配置

#### 推荐快捷键

| 功能 | 快捷键 |
|------|--------|
| 命令面板 | `⌘⇧P` |
| 快速打开文件 | `⌘P` |
| 查找 | `⌘F` |
| 全局搜索 | `⌘⇧F` |
| 终端 | `⌃`` |
| 侧边栏 | `⌘B` |
| 保存 | `⌘S` |
| 保存全部 | `⌘⌥S` |

#### 自定义键盘映射
在 VSCode 设置中搜索 "keybindings" 自定义快捷键

### 触控操作优化

#### 手势支持
- **双指滚动**: 浏览代码
- **双指缩放**: 调整字体大小
- **长按**: 右键菜单
- **双击**: 选择单词

#### 触控菜单
- 点击行号: 断点
- 点击文件名: 打开/关闭
- 点击面包屑: 导航

---

## 🔧 项目特定配置

### 环境变量配置

在 Codespaces 或 code-server 中配置环境变量：

#### 方法 1: Codespaces Secrets（推荐）

1. 访问 GitHub Settings → Codespaces → Secrets
2. 添加以下密钥:
   - `OPENAI_API_KEY`
   - `DEEPSEEK_API_KEY`
   - `DB_PASSWORD`
   - `REDIS_PASSWORD`

#### 方法 2: .env 文件

在项目根目录创建 `.env`:
```bash
cp .env.example .env
nano .env  # 或使用 VSCode 编辑
```

填写必要配置:
```env
# OpenAI API
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo

# 数据库
DB_HOST=localhost
DB_PORT=5433
DB_NAME=bidding_db
DB_USER=postgres
DB_PASSWORD=postgres123

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_PASSWORD=
```

### Docker in Codespaces

Codespaces 支持 Docker，但需要特殊配置:

#### .devcontainer/devcontainer.json
```json
{
  "name": "Bidding Intelligence System",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "backend",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "postCreateCommand": "pip install -r requirements.txt",
  "forwardPorts": [18888, 13000, 5433, 6380],
  "portsAttributes": {
    "18888": {
      "label": "Backend API",
      "onAutoForward": "notify"
    },
    "13000": {
      "label": "Frontend",
      "onAutoForward": "openBrowser"
    }
  }
}
```

### 端口转发配置

确保以下端口被正确转发:
- **18888**: 后端 API
- **13000**: 前端应用
- **5433**: PostgreSQL
- **6380**: Redis

在 Codespaces 中，转到"端口"面板手动添加端口。

---

## 🎯 开发工作流

### 典型开发流程

#### 1. 启动 Codespace
```bash
# GitHub 网页操作或使用 gh CLI
gh codespace create --repo tianh-ai/bidding-intelligence-system
```

#### 2. 检查环境
```bash
# 验证端口配置
./check_ports.sh

# 检查 Docker 状态
docker-compose ps

# 验证 Python 环境
python --version
pip list
```

#### 3. 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

#### 4. 开发和测试
```bash
# 运行后端测试
cd backend
pytest tests/ -v

# 运行前端
cd frontend
npm install
npm run dev
```

#### 5. 提交更改
```bash
git add .
git commit -m "feat: add new feature"
git push
```

### 调试配置

在 `.vscode/launch.json` 中配置调试:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "18888"
      ],
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## 📱 iPad 专用工具推荐

### 终端应用（配合 SSH）

#### Blink Shell（付费，推荐）
- 完整的终端模拟器
- 支持 Mosh（弱网络环境）
- 自定义键盘
- 价格: $19.99

#### Terminus（免费）
- SSH/SFTP 客户端
- 代码片段
- 多标签支持

### Git 客户端

#### Working Copy（免费 + 内购）
- 完整的 Git 客户端
- 支持所有 Git 操作
- 与 Shortcuts 集成

### Markdown 编辑器

#### Taio（免费）
- Markdown 编辑和预览
- iCloud 同步
- JavaScript 脚本

---

## ⚠️ 常见问题

### Q1: Codespace 无法启动服务？

**A:** 检查端口配置和 Docker 状态:
```bash
# 查看端口占用
lsof -i :18888
lsof -i :13000

# 重启服务
docker-compose down
docker-compose up -d
```

### Q2: 网络连接不稳定怎么办？

**A:** 优化策略:
1. 使用自动保存（默认已开启）
2. 频繁提交代码
3. 使用 Blink + Mosh（终端场景）
4. 考虑使用国内服务器部署 code-server

### Q3: iPad 键盘快捷键不工作？

**A:** 解决方案:
1. 检查 iPad 系统快捷键设置
2. 在 VSCode 中自定义键绑定
3. 使用触控替代方案

### Q4: 如何在 iPad 上访问本地文件？

**A:** 
- **Codespaces**: 使用 GitHub 仓库
- **vscode.dev**: 打开本地文件夹（有限支持）
- **code-server**: 通过服务器访问

### Q5: 代码运行很慢？

**A:** 优化建议:
1. 升级 Codespace 机器类型
2. 关闭不必要的扩展
3. 使用 Docker 缓存
4. 优化 Python 依赖安装

### Q6: 如何备份开发环境？

**A:**
- **Codespaces**: 代码自动同步到 GitHub
- **配置备份**: 使用 Settings Sync
- **数据库备份**: 定期导出 PostgreSQL 数据

---

## 🔐 安全建议

### 1. 使用强密码
Codespaces 和 code-server 都需要设置强密码

### 2. 启用 2FA
GitHub 账号启用双因素认证

### 3. 环境变量管理
- 不要在代码中硬编码 API 密钥
- 使用 GitHub Secrets 或环境变量
- 定期轮换密钥

### 4. HTTPS 访问
自托管服务务必配置 SSL 证书

### 5. 防火墙配置
```bash
# 只允许特定 IP 访问
sudo ufw allow from YOUR_IP to any port 8080
sudo ufw enable
```

---

## 📊 成本分析

### GitHub Codespaces

| 机器类型 | 核心 | 内存 | 存储 | 价格/小时 | 免费额度 |
|---------|------|------|------|----------|---------|
| 2-core | 2 | 8GB | 32GB | $0.18 | 120 核心小时/月 |
| 4-core | 4 | 16GB | 32GB | $0.36 | - |
| 8-core | 8 | 32GB | 64GB | $0.72 | - |

**估算**:
- 轻量开发: 免费额度足够（2核 × 60小时）
- 标准开发: ~$20/月（4核 × 50小时）
- 重度开发: ~$50/月（8核 × 70小时）

### Code-Server 自托管

| 服务商 | 配置 | 价格/月 | 备注 |
|--------|------|---------|------|
| 阿里云 | 2核4GB | ¥50-80 | 国内访问快 |
| 腾讯云 | 2核4GB | ¥50-80 | 国内访问快 |
| DigitalOcean | 2核4GB | $12 | 国际稳定 |
| Vultr | 2核4GB | $12 | 多地域可选 |

---

## 🎓 学习资源

### 官方文档
- [GitHub Codespaces 文档](https://docs.github.com/en/codespaces)
- [VSCode Web 文档](https://code.visualstudio.com/docs/editor/vscode-web)
- [Code-Server 文档](https://coder.com/docs/code-server/latest)

### 视频教程
- [在 iPad 上使用 Codespaces](https://www.youtube.com/results?search_query=github+codespaces+ipad)
- [VSCode Web 完整教程](https://www.youtube.com/results?search_query=vscode+web+tutorial)

### 社区
- [GitHub Discussions](https://github.com/github/feedback/discussions/categories/codespaces-feedback)
- [VSCode Reddit](https://www.reddit.com/r/vscode/)
- [iPad 开发者社区](https://www.reddit.com/r/iPadPro/)

---

## 📝 总结

在 iPad 上使用 VSCode 进行开发已经非常成熟，通过本指南介绍的方法，您可以：

✅ **完整的开发体验** - 与桌面版几乎无差异
✅ **随时随地编码** - 只需要 iPad 和网络
✅ **强大的计算资源** - 云端服务器提供算力
✅ **无缝协作** - 与团队成员实时协作

### 推荐方案选择

| 使用场景 | 推荐方案 |
|---------|---------|
| 快速查看/编辑代码 | vscode.dev |
| 完整项目开发 | GitHub Codespaces |
| 长期频繁使用 | Code-Server 自托管 |
| 预算有限 | vscode.dev + GitHub Actions |
| 需要运行 AI 模型 | 8核 Codespace 或自托管 |

### 下一步

1. 选择适合您的方案
2. 按照步骤配置环境
3. 开始在 iPad 上愉快编码！

---

## 💬 反馈与支持

如有问题或建议，欢迎：
- 提交 [Issue](https://github.com/tianh-ai/bidding-intelligence-system/issues)
- 发起 [Discussion](https://github.com/tianh-ai/bidding-intelligence-system/discussions)
- 查看项目 [Wiki](https://github.com/tianh-ai/bidding-intelligence-system/wiki)

---

**祝您在 iPad 上开发愉快！** 🚀📱✨
