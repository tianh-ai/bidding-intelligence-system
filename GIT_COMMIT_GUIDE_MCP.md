# Git 提交指南 - MCP 服务器集成

**日期**: 2025-12-14  
**变更类型**: 功能增强 + 项目重组

---

## 📝 本次变更概述

### 主要变更

1. **MCP 服务器模块化** ✅
   - 将 `mcp-document-parser/` 移动到 `mcp-servers/document-parser/`
   - 创建统一的 MCP 服务器管理目录结构

2. **文档更新** ✅
   - 更新主 README.md，添加 MCP 集成章节
   - 创建 `mcp-servers/README.md` 索引文档
   - 创建 `MCP_PARSER_SETUP.md` 设置指南

3. **Git 配置优化** ✅
   - 更新 `.gitignore` 添加 MCP 构建产物规则

---

## 📊 变更统计

```
总文件数: 151
├── 新增文件: 127 个
│   ├── mcp-servers/ 目录 (11 个文件)
│   ├── 文档文件 (60+ 个 .md)
│   └── 脚本和工具 (50+ 个)
│
└── 修改文件: 24 个
    ├── .gitignore (添加 MCP 构建规则)
    ├── README.md (添加 MCP 章节)
    └── 其他后端/前端文件
```

---

## 🗂️ 新增 MCP 服务器结构

```
mcp-servers/
├── README.md                          # ✨ 新增：MCP 服务器索引
└── document-parser/                   # 📦 移动自根目录
    ├── package.json
    ├── tsconfig.json
    ├── setup.sh
    ├── mcp-config.example.json
    ├── .gitignore
    ├── README.md
    ├── src/
    │   └── index.ts                   # TypeScript MCP 服务器
    ├── python/
    │   └── document_parser.py         # Python 解析后端
    └── test/
        └── test_parser.py             # 测试套件
```

---

## 📝 Git 提交建议

### 方案一：单次提交（推荐）

```bash
# 1. 添加所有文件
git add .

# 2. 提交
git commit -m "feat: 添加 MCP 服务器模块化架构

- 将文档解析 MCP 移至 mcp-servers/document-parser/
- 新增 mcp-servers/README.md 统一管理 MCP 服务器
- 更新主 README.md 添加 MCP 集成说明
- 优化 .gitignore 添加 MCP 构建产物规则
- 新增 MCP_PARSER_SETUP.md 详细设置指南

模块化优势:
✅ 统一管理所有 MCP 服务器
✅ 便于后续添加新的 MCP 服务
✅ 符合项目结构最佳实践
"

# 3. 推送到远程
git push origin main
```

### 方案二：分阶段提交（详细记录）

```bash
# 阶段 1: MCP 服务器重组
git add mcp-servers/
git commit -m "refactor: 重组 MCP 服务器目录结构

- 创建 mcp-servers/ 统一管理目录
- 移动 document-parser 到 mcp-servers/
- 新增 mcp-servers/README.md 索引文档
"

# 阶段 2: 文档更新
git add README.md MCP_PARSER_SETUP.md
git commit -m "docs: 更新 MCP 服务器集成文档

- README.md 添加 MCP 集成章节
- 新增 MCP_PARSER_SETUP.md 详细指南
- 更新项目结构说明
"

# 阶段 3: Git 配置优化
git add .gitignore
git commit -m "chore: 优化 .gitignore 添加 MCP 构建规则

- 忽略 mcp-servers/*/dist/
- 忽略 mcp-servers/*/node_modules/
- 忽略 TypeScript 构建产物
"

# 阶段 4: 其他文件
git add .
git commit -m "chore: 添加项目文档和配置文件

- 新增各种指南和报告文档
- 更新后端/前端配置
- 添加测试和验证脚本
"

# 推送
git push origin main
```

---

## 🔍 提交前检查清单

### 必须检查

- [ ] **MCP 服务器文件完整**
  ```bash
  ls -la mcp-servers/document-parser/
  # 应该看到: src/, python/, test/, README.md, package.json 等
  ```

- [ ] **README.md 更新正确**
  ```bash
  grep -A 5 "MCP 服务器" README.md
  # 应该看到 MCP 章节
  ```

- [ ] **.gitignore 包含 MCP 规则**
  ```bash
  grep "mcp-servers" .gitignore
  # 应该看到: mcp-servers/*/dist/, mcp-servers/*/node_modules/
  ```

- [ ] **敏感文件未包含**
  ```bash
  git status | grep -E "\.env$|\.env\.local"
  # 不应该有输出（.env 文件应被忽略）
  ```

### 可选检查

- [ ] **测试 MCP 服务器可访问**
  ```bash
  cd mcp-servers/document-parser
  ls -la src/index.ts python/document_parser.py
  ```

- [ ] **验证文档链接**
  ```bash
  grep -o "mcp-servers/README.md" README.md
  grep -o "MCP_PARSER_SETUP.md" README.md
  ```

---

## 📋 提交消息模板

### 标准格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 本次推荐

```
feat(mcp): 添加 MCP 服务器模块化架构

主要变更:
- 重组 MCP 服务器到 mcp-servers/ 目录
- document-parser 提供文档解析能力（4个工具）
- 新增统一的 MCP 服务器索引和文档

架构优势:
✅ 统一管理所有 MCP 服务器
✅ 符合 Model Context Protocol 标准
✅ 便于集成到 Claude Desktop/VS Code
✅ 代码复用现有 backend/engines/

文档更新:
- README.md: 添加 MCP 集成章节
- mcp-servers/README.md: MCP 服务器索引
- MCP_PARSER_SETUP.md: 详细设置指南
- .gitignore: 添加 MCP 构建规则

Breaking Changes: 无
Migration Guide: 见 MCP_PARSER_SETUP.md

Refs: #issue-number (如果有相关 issue)
```

---

## 🚀 推送后验证

### 1. GitHub 上验证

访问仓库页面，确认：
- ✅ `mcp-servers/` 目录可见
- ✅ `mcp-servers/README.md` 正确显示
- ✅ 主 `README.md` 包含 MCP 章节
- ✅ `.gitignore` 包含 MCP 规则

### 2. 克隆测试

```bash
# 在另一个目录测试克隆
cd /tmp
git clone https://github.com/tianh-ai/bidding-intelligence-system.git test-clone
cd test-clone

# 验证结构
ls -la mcp-servers/
cat mcp-servers/README.md

# 测试 MCP 安装
cd mcp-servers/document-parser
./setup.sh
```

### 3. MCP 服务器测试

```bash
# 在克隆的仓库中
cd mcp-servers/document-parser

# 安装
npm install
npm run build

# 测试
python test/test_parser.py
```

---

## ⚠️ 注意事项

### 不要提交的文件

已在 `.gitignore` 中配置，但仍需注意：

```bash
# 敏感配置
.env
.env.local
backend/.env

# 构建产物
mcp-servers/*/dist/
mcp-servers/*/node_modules/
mcp-servers/*/*.tsbuildinfo

# 用户数据
/Volumes/ssd/bidding-data/
backend/uploads/
```

### 大文件警告

如果遇到大文件警告：

```bash
# 检查文件大小
find . -type f -size +10M

# 如果有误提交的大文件
git rm --cached <large-file>
echo "<large-file>" >> .gitignore
```

---

## 📚 相关文档

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [项目主 README](README.md)
- [MCP 服务器索引](mcp-servers/README.md)
- [MCP 设置指南](MCP_PARSER_SETUP.md)
- [Git 提交规范](CONTRIBUTING.md)

---

## ✅ 快速执行

**推荐命令**（复制粘贴即可）:

```bash
# 回到项目根目录
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system

# 查看状态
git status

# 添加所有文件
git add .

# 提交
git commit -m "feat(mcp): 添加 MCP 服务器模块化架构

主要变更:
- 重组 MCP 服务器到 mcp-servers/ 目录
- document-parser 提供文档解析能力
- 新增 MCP 服务器索引和详细文档

优化:
✅ 统一管理所有 MCP 服务器
✅ 更新 README.md 添加 MCP 集成章节
✅ 优化 .gitignore 添加 MCP 构建规则
"

# 推送（首次推送到新分支）
git push origin main

# 或者推送到其他分支
# git checkout -b feature/mcp-servers
# git push origin feature/mcp-servers
```

---

**最后更新**: 2025-12-14  
**下一步**: 执行提交并推送到 GitHub
