# 端口一致性原则

**创建时间**: 2025-12-14  
**状态**: 强制执行  
**优先级**: 🔴 最高

---

## 🚨 核心问题

**我经常忘记端口配置，导致反复出错！**

### 错误表现
- ✅ 前端配置正确 (`frontend/.env` → 18888)
- ❌ 测试脚本错误 (`test_*.py` → 8000) ← 问题所在！
- ❌ 诊断脚本错误 (`diagnose_*.py` → 8000)
- ❌ 验证脚本错误 (`verify_*.py` → 8000)

**结果**: 前端能工作，但所有测试都失败！

---

## 📏 唯一正确的配置

> **Docker模式下，所有地方都必须使用 18888 端口！**

### 端口映射规则

```
Docker容器内: 8000  (固定，不要改)
       ↓
宿主机端口: 18888  (对外访问)
       ↓
所有配置都用: 18888 ← 重要！
```

---

## ✅ 正确配置清单

### 1. 前端配置
```bash
# frontend/.env
VITE_API_URL=http://localhost:18888  # ✅ 正确
```

### 2. Python测试脚本
```python
# verify_knowledge_display.py
API_BASE = "http://localhost:18888"  # ✅ 正确

# test_knowledge_api.py
API_BASE = "http://localhost:18888"  # ✅ 正确

# test_knowledge_auth.py
API_BASE = "http://localhost:18888"  # ✅ 正确

# diagnose_knowledge.py
# 所有curl命令都用18888
```

### 3. Shell脚本
```bash
# 任何测试或诊断脚本
curl http://localhost:18888/health  # ✅ 正确
```

### 4. Markdown文档
```markdown
# 所有示例命令
curl http://localhost:18888/api/...  # ✅ 正确
```

---

## ❌ 错误配置（禁止）

```python
# ❌ 错误示例 - 不要写旧端口/容器内端口
API_BASE = "http://localhost:<WRONG_PORT>"

# ❌ 错误 - 注释里也不要出现旧端口URL，避免复制粘贴误操作
# 测试: curl http://localhost:<WRONG_PORT>/health
```

```bash
# ❌ 错误示例
curl http://localhost:<WRONG_PORT>/api/...
```

---

## 🔍 自动检查

### 使用端口检查脚本
# 建议仅使用自动脚本检查与修复
./check_ports.sh
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 全面端口一致性检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 检查Python脚本
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ verify_knowledge_display.py - 端口配置正确
  ✅ test_knowledge_api.py - 端口配置正确
  ✅ diagnose_knowledge.py - 端口配置正确

2. 检查前端配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ frontend/.env - 端口配置正确 (18888)

✅ 所有关键文件端口配置正确！
```

### 手动检查

```bash
# 仅建议使用自动脚本检查与修复
./check_ports.sh
```

---

## 🔄 迁移指南

### 从8000迁移到18888

统一迁移与验证请直接运行：

```bash
./check_ports.sh
```

---

## 📝 开发规范

### 编写新代码时

```python
# ✅ 正确 - 永远使用18888
import requests

API_BASE = "http://localhost:18888"  # Docker端口

def test_api():
    response = requests.get(f"{API_BASE}/health")
    assert response.status_code == 200
```

```bash
# ✅ 正确 - Shell脚本
#!/bin/bash
API_URL="http://localhost:18888"
curl $API_URL/health
```

### 编写文档时

```markdown
## 测试API

\`\`\`bash
# ✅ 正确 - 使用18888
curl http://localhost:18888/api/knowledge/statistics
\`\`\`
```

---

## 🎯 记忆技巧

### 端口数字含义

- **18888** = **1**个Docker + **8888**端口
  - "1" 代表 Docker（单一统一环境）
  - "8888" 代表后端服务

### 快速检查口诀

```
写代码前先检查，
端口必须18888。
Docker原则不能忘，
check_ports保平安。
```

---

## ⚠️ 常见错误及修复

### 错误1: 测试脚本连接失败

**症状**:
```python
# test_knowledge_api.py
requests.exceptions.ConnectionError: Connection refused
```

**原因**: 脚本用的8000端口，Docker是18888

**修复**:
```python
# 修改
API_BASE = "http://localhost:18888"  # 不是8000！
```

### 错误2: curl命令返回401

**症状**:
```bash
$ curl http://localhost:<WRONG_PORT>/health
{"message":"Unauthorized"}
```

**原因**: 8000端口没有服务，或者是旧的本地服务

**修复**:
```bash
# 使用正确端口
curl http://localhost:18888/health
```

### 错误3: 前端能连接，测试不能

**症状**:
- 浏览器能访问后端 ✅
- Python测试失败 ❌

**原因**: 前端用18888，测试脚本用8000

**修复**:
```bash
# 运行检查脚本
./check_ports.sh
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| `DOCKER_PRINCIPLES.md` | Docker使用原则（必读） |
| `check_ports.sh` | 端口检查脚本 |
| `docker-compose.yml` | Docker配置 |
| `frontend/.env` | 前端环境变量 |

---

## ✅ 提交前检查清单

每次提交代码前：

- [ ] 运行 `./check_ports.sh`
- [ ] 确认所有测试脚本用18888
- [ ] 确认前端`.env`用18888
- [ ] 确认文档示例用18888
- [ ] 没有硬编码8000端口

---

## 🚀 快速修复

```bash
# 一键检查并修复所有端口问题
./check_ports.sh

# 如果有问题，会自动修复并显示
# 备份文件保存为 *.bak

# 验证修复
./check_ports.sh
```

---

**总结**: 
- 🐳 **只用Docker**
- 🔌 **只用18888**  
- ✅ **定期检查**

记住这三条，不再出错！
