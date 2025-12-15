# 🛡️ 代码保护机制 - 快速开始

> **防止新代码破坏已完成的程序**

---

## 🚀 立即开始

### 1️⃣ 验证系统状态（30秒）

```bash
# 一键检查整个系统
./scripts/quick_verify.sh
```

**看到这个说明一切正常**：
```
✅ 没有未提交的修改
✅ 前端编译成功
✅ 后端服务运行正常
✅ 数据库连接正常
✅ MCP服务器已构建
✅ 验证完成
```

### 2️⃣ 安装保护机制（10秒）

```bash
# 安装Git hook（自动防护）
cp scripts/pre-commit-protection.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**完成！** 现在每次提交都会自动检查是否修改了受保护的文件。

### 3️⃣ 记住核心规则

> **⚠️ 不要修改已经工作的代码！**

**受保护的文件**：
- `frontend/src/pages/FileUpload.tsx` ⛔
- `frontend/src/services/api.ts` ⛔
- `backend/routers/files.py` ⛔
- `backend/agents/preprocessor.py` ⛔
- `backend/engines/smart_router.py` ⛔

---

## 📚 详细文档

### 核心文档（按优先级）

| 文档 | 用途 | 何时阅读 |
|------|------|---------|
| **CODE_PROTECTION.md** | 完整的保护规范 | 修改任何代码前 |
| **KNOWLEDGE_DISPLAY_DIAGNOSIS.md** | 知识库问题诊断 | 知识库不显示时 |
| **FRONTEND_BEHAVIOR.md** | 前端行为规范 | 修改前端代码前 |
| **CODE_PROTECTION_IMPLEMENTATION.md** | 实施报告 | 了解保护机制 |

### 工具脚本

| 脚本 | 功能 | 使用场景 |
|------|------|---------|
| `verify_knowledge_display.py` | Python诊断工具 | 知识库问题排查 |
| `scripts/quick_verify.sh` | 快速验证脚本 | 日常开发检查 |
| `scripts/pre-commit-protection.sh` | Git提交保护 | 自动运行（已安装） |

---

## 🎯 常见场景

### 场景1: 我要修改 FileUpload.tsx

```bash
# 1. 先检查是否允许修改
cat CODE_PROTECTION.md | grep FileUpload

# 2. 如果必须修改，先备份
git checkout -b fix-fileupload-bug

# 3. 修改代码
vim frontend/src/pages/FileUpload.tsx

# 4. 立即测试
./scripts/quick_verify.sh

# 5. 如果有问题，立即回滚
git checkout -- frontend/src/pages/FileUpload.tsx
```

### 场景2: 知识库不显示

```bash
# 1. 运行诊断（最重要！）
python verify_knowledge_display.py

# 2. 按照诊断结果修复
# 如果后端未运行 → cd backend && python main.py
# 如果数据库无数据 → 上传文件并等待处理
# 如果MCP未构建 → cd mcp-servers/knowledge-base && npm run build

# 3. 检查前端代码是否被修改
git diff frontend/src/pages/FileUpload.tsx

# 4. 如果被修改且不应该，回滚
git checkout -- frontend/src/pages/FileUpload.tsx
```

### 场景3: Git提交时收到警告

```
⚠️ 警告：检测到修改了受保护的文件！
  - frontend/src/pages/FileUpload.tsx

是否继续提交？(y/N)
```

**正确做法**：
```bash
# 1. 选择 N（取消提交）

# 2. 检查修改
git diff --cached frontend/src/pages/FileUpload.tsx

# 3. 如果修改不应该存在，回滚
git reset HEAD frontend/src/pages/FileUpload.tsx
git checkout -- frontend/src/pages/FileUpload.tsx

# 4. 如果确实需要修改，添加说明
git commit -m "fix(FileUpload): 修复XXX问题（已测试）"

# 5. 如果hook仍然拦截，且确认安全，使用
git commit --no-verify -m "你的提交信息"
```

---

## ⚡ 快速命令

```bash
# 检查系统状态
./scripts/quick_verify.sh

# 诊断知识库问题
python verify_knowledge_display.py

# 检查代码修改
git diff

# 回滚文件
git checkout -- <file>

# 查看受保护文件
cat CODE_PROTECTION.md | grep "受保护"

# 测试前端编译
cd frontend && npm run build

# 测试后端API
curl http://localhost:8000/health
```

---

## 🔧 开发流程

### 每次开发前
```bash
1. ./scripts/quick_verify.sh  # 确认系统正常
2. git status                  # 确认没有未提交的修改
3. git checkout -b feature-xxx # 创建新分支
```

### 开发过程中
```bash
# 小步提交
git add <file>
git commit -m "feat: 描述"

# 定期测试
./scripts/quick_verify.sh
```

### 开发完成后
```bash
# 最终测试
./scripts/quick_verify.sh
python verify_knowledge_display.py

# 浏览器测试
# 打开 http://localhost:5173
# 测试所有功能

# 合并到主分支
git checkout main
git merge feature-xxx
```

---

## 🆘 紧急救援

### 破坏了重要功能怎么办？

```bash
# 1. 立即停止修改
# 不要慌！

# 2. 查看修改了什么
git diff

# 3. 回滚到上一次提交
git reset --hard HEAD

# 4. 如果已经提交，回滚到更早的版本
git log                    # 找到工作的commit
git reset --hard <commit>  # 回滚到那个commit

# 5. 重新测试
./scripts/quick_verify.sh
```

### 不确定代码是否正确？

```bash
# 1. 运行诊断
python verify_knowledge_display.py

# 2. 检查代码
git diff frontend/src/pages/FileUpload.tsx

# 3. 对比文档
cat CODE_PROTECTION.md
cat FRONTEND_BEHAVIOR.md

# 4. 如有疑问，先回滚
git checkout -- .

# 5. 在新分支尝试
git checkout -b test-changes
```

---

## 📞 获取帮助

### 问题排查顺序

1. **运行诊断脚本** → `python verify_knowledge_display.py`
2. **查看文档** → `CODE_PROTECTION.md`
3. **检查修改** → `git diff`
4. **回滚测试** → `git checkout -- <file>`
5. **重新开始** → 在新分支上尝试

### 相关资源

- 代码保护规范: `CODE_PROTECTION.md`
- 诊断报告: `KNOWLEDGE_DISPLAY_DIAGNOSIS.md`
- 前端规范: `FRONTEND_BEHAVIOR.md`
- 实施报告: `CODE_PROTECTION_IMPLEMENTATION.md`
- Copilot指令: `.github/copilot-instructions.md`

---

## ✅ 检查清单

开发前：
- [ ] 已运行 `./scripts/quick_verify.sh`
- [ ] 已阅读相关文档
- [ ] 已创建新分支（如需要）
- [ ] 系统状态正常

修改后：
- [ ] 已立即测试
- [ ] 编译通过
- [ ] 功能正常
- [ ] 无错误日志

提交前：
- [ ] 已运行诊断
- [ ] 代码已审查
- [ ] 提交信息清晰
- [ ] 受保护文件修改有说明

---

## 🎉 记住

**核心原则**：
> 如果代码已经工作，不要修改它！

**安全做法**：
> 测试 → 备份 → 小心修改 → 立即验证 → 出问题回滚

**工具帮助**：
> 有疑问先运行 `./scripts/quick_verify.sh`

---

**准备好了？开始安全开发！** 🚀

```bash
# 立即执行
./scripts/quick_verify.sh
```
