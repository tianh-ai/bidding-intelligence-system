# Copilot 记忆助手 - 端口配置

**用途**: 帮助Copilot记住端口配置，避免重复错误  
**创建时间**: 2025-12-14  
**重要性**: 🔴 极高 - 最常见的错误！

---

## 🚨 我经常犯的错误

### 错误模式
1. ✅ 知道前端`.env`应该用18888
2. ❌ 但创建测试脚本时用8000
3. ❌ 创建诊断脚本时也用8000
4. ❌ 写文档示例时还是用8000

**结果**: 前端能工作，但所有测试都失败！

---

## 💡 记忆规则

### 规则1: Docker = 18888
```
🐳 Docker容器内部端口: <CONTAINER_INTERNAL_PORT> (不要管它)
📍 对外暴露端口: 18888 ← 这个才是重点！
```

### 规则2: 所有地方都用18888
```python
# ✅ Python脚本
API_BASE = "http://localhost:18888"

# ✅ Shell脚本
curl http://localhost:18888/health

# ✅ 前端.env
VITE_API_URL=http://localhost:18888

# ✅ 文档示例
curl http://localhost:18888/api/knowledge/statistics
```

### 规则3: 永远不用8000（在Docker模式下）
```python
# ❌ 错误 - 不要用错误端口
API_BASE = "http://localhost:<WRONG_PORT>"  # 错！
curl http://localhost:<WRONG_PORT>/health   # 错！
```

---

## 🎯 快速检查

### 每次写代码前问自己

> 我要写的代码是在Docker环境中运行的吗？

- 如果是 → 使用 **18888**
- 如果不是 → 你确定吗？（99%情况都是Docker）

### 每次写完代码后

```bash
# 运行检查脚本
./check_ports.sh
```

---

## 📋 常见场景及正确端口

| 场景 | 使用的端口 | 示例 |
|------|----------|------|
| 写Python测试脚本 | 18888 | `API_BASE = "http://localhost:18888"` |
| 写Shell测试脚本 | 18888 | `curl http://localhost:18888/health` |
| 写诊断脚本 | 18888 | `requests.get("http://localhost:18888/api/...")` |
| 写验证脚本 | 18888 | 同上 |
| 写文档示例 | 18888 | 文档中的curl命令 |
| 前端配置 | 18888 | `VITE_API_URL=http://localhost:18888` |
| Docker内部 | <CONTAINER_INTERNAL_PORT> | `docker-compose.yml`中的容器端口（不要改）|

---

## 🔄 我的常见错误流程

### 错误流程（我经常这样做）
```
1. 用户报告知识库不显示
2. 我说："让我写个测试脚本"
3. 我写: API_BASE = "http://localhost:<WRONG_PORT>"  ← 错！

4. 测试失败
5. 用户生气："你又忘了端口！"
6. 我改成18888
7. 测试成功
```

### 正确流程（我应该这样做）
```
1. 用户报告知识库不显示
2. 我先想："Docker端口是18888"  ← 记住这个！
3. 我写: API_BASE = "http://localhost:18888"  ← 对！
4. 测试成功
5. 用户满意
```

---

## 📝 Copilot自我检查清单

### 在生成任何代码前

- [ ] 我要访问的是Docker服务吗？（99%是）
- [ ] 如果是，端口应该是18888
- [ ] 我的代码中所有localhost后面跟的是18888吗？
- [ ] 我的文档示例中用的也是18888吗？

### 生成代码后

 - [ ] 搜索代码中的"<WRONG_PORT>"
- [ ] 确认不是在访问外部服务
- [ ] 如果是本地服务，改成18888
- [ ] 建议用户运行 `./check_ports.sh`

---

## 🎓 学习记忆法

### 数字记忆
- **18888** = **1** 个Docker + **8888** 端口
  - "1" 象征 Docker（单一统一环境）
  - "8888" 象征 后端服务（吉利数字，容易记）

### 口诀记忆
```
Docker必须用，
端口18888。
测试脚本写，
还是18888。
文档示例打，
依然18888。
永远不要忘，
全都18888！
```

---

## 🚫 违规案例

### 案例1: 测试脚本端口错误
```python
# ❌ 我生成的错误代码
# verify_knowledge_display.py
API_BASE = "http://localhost:<WRONG_PORT>"  # 错了！

# 后果：
# - 测试失败
# - 用户困惑："为什么前端能工作，测试不行？"
# - 浪费时间调试
```

### 案例2: 诊断脚本端口错误
```python
# ❌ 我生成的错误代码
# diagnose_knowledge.py
def check_health():
  return requests.get("http://localhost:<WRONG_PORT>/health")  # 错了！

# 后果：
# - 诊断工具本身就是错的
# - 误导用户以为服务没启动
# - 用户开始怀疑Docker配置
```

### 案例3: 文档示例端口错误
```markdown
<!-- ❌ 我写的错误文档 -->
## 测试API

\`\`\`bash
curl http://localhost:<WRONG_PORT>/api/knowledge/statistics
\`\`\`

<!-- 后果：
- 用户按文档操作，失败
- 用户失去信任："文档都是错的？"
- 需要更新所有文档
-->
```

---

## ✅ 正确案例

### 案例1: 测试脚本端口正确
```python
# ✅ 正确的代码
# verify_knowledge_display.py
API_BASE = "http://localhost:18888"  # 对了！

# 结果：
# - 测试成功
# - 用户满意
# - 节省时间
```

### 案例2: 诊断脚本端口正确
```python
# ✅ 正确的代码
# diagnose_knowledge.py
def check_health():
    return requests.get("http://localhost:18888/health")  # 对了！

# 结果：
# - 诊断准确
# - 快速定位问题
# - 用户信任工具
```

### 案例3: 文档示例端口正确
```markdown
<!-- ✅ 正确的文档 -->
## 测试API

\`\`\`bash
curl http://localhost:18888/api/knowledge/statistics
\`\`\`

<!-- 结果：
- 用户按文档操作，成功
- 用户信任文档
- 减少支持请求
-->
```

---

## 🔧 修复工具

### 自动检查脚本
```bash
# 运行这个脚本检查所有端口
./check_ports.sh

# 如果发现错误，会自动修复
# 备份文件会保存为 *.bak
```

### 手动检查命令
```bash
# 搜索所有可能的端口错误
grep -r "localhost:<WRONG_PORT>" . \
  --include="*.py" \
  --include="*.sh" \
  --include=".env" \
  --include="*.md"

# 应该只在 docker-compose.yml 中出现（容器内部端口）
```

---

## 📚 相关文档

阅读顺序（重要性递减）：

1. **PORT_CONSISTENCY.md** - 端口一致性原则（最重要！）
2. **DOCKER_PRINCIPLES.md** - Docker使用原则
3. **CODE_PROTECTION.md** - 代码保护规范
4. **.github/copilot-instructions.md** - Copilot完整说明

---

## 🎯 最终总结

### 我需要记住的最重要的一件事

> **Docker环境 = 端口18888，不是8000！**

### 我需要养成的习惯

```
写代码前 → 想一下："Docker端口是18888"
写代码时 → 搜索代码中的"8000"
写代码后 → 运行 ./check_ports.sh
```

### 当我不确定时

```bash
# 1. 看一眼前端配置
cat frontend/.env
# 应该看到: VITE_API_URL=http://localhost:18888

# 2. 看一眼Docker配置
cat docker-compose.yml | grep "18888"
# 应该看到: "18888:8000"

# 3. 测试一下
curl http://localhost:18888/health
# 应该返回: {"status":"healthy"}
```

---

**最后提醒自己**:

```
每次生成代码时，我都要问自己：
"这个端口是18888吗？"

如果不是，立即改正！
如果是，继续保持！
```

记住：**用户已经多次提醒我这个问题，不能再犯了！**
