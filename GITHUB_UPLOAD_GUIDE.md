# GitHub 上传指南

本文档指导如何将标书智能系统上传到GitHub。

## 📝 准备工作

### 1. 创建GitHub仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - **Repository name**: `bidding-intelligence-system`
   - **Description**: `AI-powered bidding document analysis and generation system`
   - **Visibility**: Public 或 Private
   - ⚠️ **不要**勾选 "Initialize this repository with a README"
4. 点击 "Create repository"

### 2. 配置Git（首次使用）

```bash
# 配置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 配置默认分支名
git config --global init.defaultBranch main
```

## 🚀 上传步骤

### 方式一：使用 HTTPS（推荐）

```bash
# 1. 进入项目目录
cd /Users/tianmac/docker/supabase/bidding-system

# 2. 初始化Git仓库（已完成）
# git init
# git add .

# 3. 创建首次提交
git commit -m "feat: initial commit - Bidding Intelligence System v1.0.0

- Add document parsing engine (PDF/Word)
- Add dual-layer learning system
- Add RESTful API endpoints
- Add database schema (31 tables)
- Add deployment scripts and documentation
- Add comprehensive README and guides"

# 4. 添加远程仓库（替换成您的GitHub用户名）
git remote add origin https://github.com/YOUR-USERNAME/bidding-intelligence-system.git

# 5. 推送到GitHub
git branch -M main
git push -u origin main
```

### 方式二：使用 SSH

```bash
# 1. 生成SSH密钥（如果没有）
ssh-keygen -t ed25519 -C "your.email@example.com"

# 2. 添加SSH密钥到GitHub
# 复制公钥内容
cat ~/.ssh/id_ed25519.pub
# 访问 GitHub Settings → SSH and GPG keys → New SSH key
# 粘贴公钥并保存

# 3. 添加远程仓库并推送
git remote add origin git@github.com:YOUR-USERNAME/bidding-intelligence-system.git
git branch -M main
git push -u origin main
```

## 📋 上传后的检查清单

在GitHub页面验证：

- [ ] README.md 正确显示
- [ ] 项目结构完整
- [ ] .gitignore 生效（venv, .env 等未上传）
- [ ] LICENSE 文件存在
- [ ] 文档链接正常工作
- [ ] GitHub Actions 配置正确

## 🔖 创建Release

### 1. 创建Tag

```bash
# 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0

Initial release of Bidding Intelligence System

Features:
- Document parsing and analysis
- Dual-layer learning system
- RESTful API with Swagger UI
- Automated deployment scripts
- Comprehensive documentation"

# 推送标签到GitHub
git push origin v1.0.0
```

### 2. 在GitHub创建Release

1. 访问仓库页面 → "Releases" → "Create a new release"
2. 选择刚创建的tag: `v1.0.0`
3. Release title: `v1.0.0 - Initial Release`
4. 描述中填写 CHANGELOG.md 的内容
5. 上传打包文件（可选）：
   ```bash
   # 先创建打包文件
   cd /Users/tianmac/docker/supabase
   ./package.sh
   
   # 上传 packages/bidding-system-*.tar.gz 到Release
   ```
6. 点击 "Publish release"

## 📦 附加打包文件

如果要在Release中提供打包版本：

```bash
# 1. 创建最新打包
cd /Users/tianmac/docker/supabase
./package.sh

# 2. 获取生成的文件
ls -lh packages/

# 3. 在GitHub Release页面上传
# bidding-system-YYYYMMDD-HHMMSS.tar.gz
# bidding-system-YYYYMMDD-HHMMSS.manifest.txt
```

## 🔄 后续更新流程

### 日常提交

```bash
# 1. 修改代码后
git add .
git commit -m "feat: add new feature"
git push

# 2. 或者分步骤
git add backend/specific_file.py
git commit -m "fix: resolve database connection issue"
git push
```

### 创建新版本

```bash
# 1. 更新版本号和CHANGELOG.md
nano CHANGELOG.md

# 2. 提交更改
git add .
git commit -m "chore: bump version to 1.1.0"

# 3. 创建并推送标签
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0

# 4. 在GitHub创建Release
```

## 🌿 分支管理策略

推荐使用 Git Flow 工作流：

```bash
# 创建开发分支
git checkout -b develop
git push -u origin develop

# 创建功能分支
git checkout -b feature/new-feature develop
# ... 开发完成后
git checkout develop
git merge --no-ff feature/new-feature
git push origin develop

# 准备发布
git checkout -b release/1.1.0 develop
# ... 修复bug、更新文档
git checkout main
git merge --no-ff release/1.1.0
git tag -a v1.1.0
git push origin main --tags

# 合并回develop
git checkout develop
git merge --no-ff release/1.1.0
git push origin develop
```

## 🛡️ 保护敏感信息

确保以下文件不会被上传：

```bash
# 检查 .gitignore 包含：
.env
.env.local
.env.production
*.log
venv/
__pycache__/

# 如果不小心提交了敏感信息
git rm --cached backend/.env
git commit -m "chore: remove sensitive file"
git push
```

## 📊 GitHub Actions

项目已包含 CI/CD 配置（`.github/workflows/ci.yml`），推送后会自动：

- ✅ 运行代码测试
- ✅ 检查代码规范
- ✅ 扫描安全漏洞

查看结果：仓库页面 → "Actions" 标签

## 🎯 项目配置建议

### 1. 设置分支保护规则

Settings → Branches → Add rule:
- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Include administrators

### 2. 配置 GitHub Pages（可选）

如果要发布文档：
- Settings → Pages
- Source: Deploy from a branch
- Branch: main / docs folder

### 3. 添加 Topics（标签）

仓库页面点击 "Add topics"，建议添加：
- `python`
- `fastapi`
- `postgresql`
- `ai`
- `nlp`
- `document-processing`
- `bidding-system`

## ⚠️ 注意事项

1. **不要上传敏感信息**
   - 数据库密码
   - API密钥
   - 用户数据

2. **检查文件大小**
   - GitHub单文件限制: 100MB
   - 不要上传大型数据文件
   - 不要上传虚拟环境 (venv/)

3. **使用 .gitignore**
   - 项目已包含完整的 .gitignore
   - 上传前检查 `git status`

4. **提交信息规范**
   - 使用有意义的提交信息
   - 遵循约定式提交规范

## 📞 遇到问题？

### 常见问题

**问题1**: 推送被拒绝
```bash
# 解决方案：先拉取远程更改
git pull origin main --rebase
git push origin main
```

**问题2**: 文件太大无法推送
```bash
# 解决方案：从历史中移除大文件
git filter-branch --tree-filter 'rm -f path/to/large/file' HEAD
git push origin main --force
```

**问题3**: 忘记添加文件
```bash
# 解决方案：修改最后一次提交
git add forgotten_file.py
git commit --amend --no-edit
git push origin main --force  # 谨慎使用
```

## ✅ 完成后

项目成功上传到GitHub后，您可以：

1. **分享项目**
   ```
   https://github.com/YOUR-USERNAME/bidding-intelligence-system
   ```

2. **在README添加徽章**
   ```markdown
   ![GitHub stars](https://img.shields.io/github/stars/YOUR-USERNAME/bidding-intelligence-system)
   ![GitHub forks](https://img.shields.io/github/forks/YOUR-USERNAME/bidding-intelligence-system)
   ![GitHub issues](https://img.shields.io/github/issues/YOUR-USERNAME/bidding-intelligence-system)
   ```

3. **邀请协作者**
   Settings → Collaborators → Add people

---

**祝您的项目在GitHub上获得成功！⭐**
