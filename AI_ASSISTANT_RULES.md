# AI 助手行为准则

## 🚨 核心原则

**环境是正确的，不要瞎改！**

当前系统已经正常运行，99% 的问题是**配置不一致**，不是缺少依赖。

---

## ❌ 严格禁止的操作

### 1. 不要随意安装 Python 包
```bash
# ❌ 禁止！可能破坏环境
pip3 install xxx
pip3 install openai redis loguru  # 已经安装过了！
pip3 upgrade xxx
```

**为什么？**
- 可能引入不兼容版本
- 可能破坏现有依赖关系
- 可能覆盖已验证的包版本

**正确做法**：
1. 先检查是否已安装：`pip3 show xxx`
2. 查看快照：`cat backend/requirements.snapshot.txt`
3. 如果确实需要，先创建快照：`./CHANGE_MANAGEMENT.sh` → 选项 1

### 2. 不要修改数据库连接代码
```bash
# ❌ 禁止直接编辑
vim backend/database/connection.py
```

**为什么？**
- 代码中的硬编码已经修正
- 修改代码会导致配置守护失效
- 环境变量优先级更高

**正确做法**：
只修改 `.env` 文件，通过 `config-guard.sh` 验证

### 3. 不要修改 Docker 配置
```bash
# ❌ 禁止
vim docker-compose.yml
docker-compose down
docker-compose build --no-cache
```

**为什么？**
- Docker 容器已运行 3 天，稳定可靠
- 重新构建可能引入新问题
- 可能丢失数据

**正确做法**：
只使用 `docker-compose restart` 重启服务

### 4. 不要清理 Docker 资源
```bash
# ❌ 禁止
docker system prune
docker volume prune
docker image prune
```

**为什么？**
- 可能删除正在使用的卷
- 可能删除自定义镜像
- 恢复成本高

---

## ✅ 遇到错误时的正确流程

### 第1步：诊断（不要修改）
```bash
# 运行诊断脚本
./check-ports.sh          # 检查端口占用
./config-guard.sh         # 检查配置一致性
docker-compose logs backend  # 查看日志
```

### 第2步：对比快照
```bash
# 查看当前环境
pip3 freeze | diff - backend/requirements.snapshot.txt
docker-compose ps
cat backend/.env
```

### 第3步：确认问题类型

#### 问题类型 A：配置不一致（90%的情况）
**症状**：
- 端口连接失败
- 数据库认证失败
- 前端 API 请求失败

**解决**：
```bash
./config-guard.sh  # 自动修复配置
```

#### 问题类型 B：端口冲突
**症状**：
- Address already in use
- bind: address already in use

**解决**：
```bash
./check-ports.sh   # 查看占用
./start-docker.sh  # 使用正确的启动脚本
```

#### 问题类型 C：代码错误
**症状**：
- 语法错误
- 导入错误（但不是 ModuleNotFoundError）
- 逻辑错误

**解决**：
- 检查代码逻辑
- 查看完整堆栈跟踪
- 不要安装包！

#### 问题类型 D：真的缺少依赖（<1%的情况）
**症状**：
- `ModuleNotFoundError: No module named 'xxx'`
- 确认 `requirements.snapshot.txt` 中没有这个包
- 确认是新功能需要的包

**解决**：
```bash
# 1. 创建快照
./CHANGE_MANAGEMENT.sh  # 选项 1

# 2. 安装包
pip3 install xxx

# 3. 对比变化
./CHANGE_MANAGEMENT.sh  # 选项 2

# 4. 验证
./config-guard.sh
```

---

## 🔧 标准操作流程（SOP）

### SOP-1: 启动系统
```bash
./start-docker.sh
# 或
./start-local.sh
```

### SOP-2: 检查配置
```bash
./config-guard.sh
```

### SOP-3: 检查端口
```bash
./check-ports.sh
```

### SOP-4: 查看日志
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### SOP-5: 修改配置
```bash
# 1. 编辑配置守护脚本
vim config-guard.sh
# 找到配置金标准部分，修改值

# 2. 运行守护脚本同步
./config-guard.sh

# 3. 验证
./start-docker.sh
```

### SOP-6: 环境变更（必须）
```bash
# 变更前
./CHANGE_MANAGEMENT.sh  # 选项 1: 创建快照

# 执行变更
# ... 你的操作 ...

# 变更后
./CHANGE_MANAGEMENT.sh  # 选项 2: 对比差异
./CHANGE_MANAGEMENT.sh  # 选项 5: 验证环境
```

---

## 📋 决策树

```
遇到错误
    ↓
┌─ 是端口占用？
│   └─ Yes → 运行 ./check-ports.sh
│       └─ 使用 ./start-docker.sh 统一启动
│
├─ 是配置错误？
│   └─ Yes → 运行 ./config-guard.sh
│       └─ 自动修复
│
├─ 是连接失败？
│   └─ Yes → 检查配置文件
│       ├─ backend/.env (DB_PORT=5433, DB_PASSWORD=postgres123)
│       └─ frontend/.env (VITE_API_URL=http://localhost:18888)
│
├─ 是代码错误？
│   └─ Yes → 查看堆栈跟踪
│       └─ 修复代码逻辑
│       └─ 不要安装包！
│
└─ 是缺少依赖？
    └─ Yes → 确认：
        ├─ 检查 requirements.snapshot.txt
        ├─ 这是新功能需要的包吗？
        └─ 如果确认需要：
            ├─ ./CHANGE_MANAGEMENT.sh (创建快照)
            ├─ pip3 install xxx
            └─ ./CHANGE_MANAGEMENT.sh (对比验证)
```

---

## 📚 参考文档优先级

1. **ENVIRONMENT_SNAPSHOT.md** - 当前正确的环境配置
2. **CONFIGURATION_GUIDE.md** - 配置详细说明
3. **PORT_MANAGEMENT.md** - 端口管理规范
4. **QUICKSTART_CONFIG.md** - 快速参考

---

## 🎯 工作检查清单

**每次协助前确认**：
- [ ] 阅读 ENVIRONMENT_SNAPSHOT.md
- [ ] 运行 `./config-guard.sh` 检查配置
- [ ] 运行 `./check-ports.sh` 检查端口
- [ ] 查看 Docker 容器状态 `docker-compose ps`
- [ ] 确认问题类型（配置/端口/代码/依赖）

**修改配置前确认**：
- [ ] 已备份配置文件
- [ ] 已运行 `./CHANGE_MANAGEMENT.sh` 创建快照
- [ ] 修改 `config-guard.sh` 中的金标准
- [ ] 运行 `./config-guard.sh` 同步
- [ ] 验证修改结果

**安装包前确认**（99%不需要）：
- [ ] 确认 `requirements.snapshot.txt` 中没有
- [ ] 确认这是新功能需要的包
- [ ] 已创建环境快照
- [ ] 记录安装原因和版本
- [ ] 安装后对比差异

---

## 💡 常见误区

### 误区 1："看到 ModuleNotFoundError 就 pip install"
**错误**：可能破坏环境
**正确**：
1. 检查是否是导入路径问题
2. 检查是否是循环导入
3. 检查 requirements.snapshot.txt
4. 确认真的需要后才安装

### 误区 2："配置文件改了不生效就改代码"
**错误**：导致配置管理混乱
**正确**：
1. 检查环境变量优先级
2. 检查是否重启服务
3. 运行 config-guard.sh 验证
4. 不要直接改代码硬编码

### 误区 3："有错误就重启 Docker"
**错误**：可能丢失有用信息
**正确**：
1. 先查看日志 `docker-compose logs`
2. 检查配置是否一致
3. 只用 `restart` 不用 `down`
4. 记录重启原因

---

## 🔐 金科玉律（背下来）

1. **当前环境是正确的** - 不要轻易改
2. **99% 是配置问题** - 不是缺依赖
3. **先诊断再修改** - 不要瞎改
4. **修改前先备份** - 可以回滚
5. **所有变更要记录** - 可以追溯
6. **使用标准脚本** - 不要手动操作
7. **配置有金标准** - 在 config-guard.sh
8. **不要安装包** - 除非万不得已

---

## 📞 求助流程

如果确实需要修改环境：

1. **先自查**：运行所有诊断脚本
2. **查文档**：ENVIRONMENT_SNAPSHOT.md
3. **做快照**：./CHANGE_MANAGEMENT.sh
4. **小步骤**：一次只改一个地方
5. **立即验证**：每步都检查
6. **记录变更**：更新 ENVIRONMENT_SNAPSHOT.md

---

**最后提醒：这不是开发环境，是生产环境！三思而后行！**
