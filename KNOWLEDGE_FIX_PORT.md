# 知识条目不显示问题 - 解决方案

## 问题根源

**后端服务运行在 Docker 容器中，端口映射为 `18888:8000`**

- 容器内端口：8000
- 宿主机端口：**18888** ← 这是关键！

前端配置可能仍然指向 `http://localhost:8000`，导致连接失败。

## 立即解决

### 方案1：修改前端API地址（推荐）

```bash
# 修改前端配置
vim frontend/.env

# 或直接修改
echo "VITE_API_URL=http://localhost:18888" > frontend/.env
```

### 方案2：测试后端服务

```bash
# 测试正确的端口
curl http://localhost:18888/

# 应该返回:
{
  "message": "标书智能系统API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 方案3：登录并获取token

```bash
# 使用正确的端口登录
curl -X POST http://localhost:18888/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "bidding2024"}'

# 应该返回token
```

### 方案4：测试知识库API

```bash
# 使用token访问知识库
TOKEN="你的token"

curl -X POST http://localhost:18888/api/knowledge/entries/list \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"limit": 5}'
```

## 快速验证

运行以下脚本验证：

```bash
python diagnose_knowledge_18888.py
```

## 前端配置检查

检查以下文件中的API地址：

1. `frontend/.env` 或 `frontend/.env.local`
   ```
   VITE_API_URL=http://localhost:18888
   ```

2. `frontend/src/config/constants.ts`
   ```typescript
   export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:18888'
   ```

## 测试账号

- **admin** / **bidding2024**
- **user** / **user2024**

## 下一步

1. 修改前端API地址为 `http://localhost:18888`
2. 重启前端开发服务器
3. 清除浏览器缓存和localStorage
4. 重新登录
5. 上传文件并查看知识库

## Docker 端口说明

```yaml
# docker-compose.yml
backend:
  ports:
    - "0.0.0.0:18888:8000"  # 外部18888 → 容器内8000
```

**记住：外部访问使用 18888，容器内使用 8000**
