# 🎯 Network Error 根因修复报告

## ❌ 根本原因

前端运行在浏览器中，API 地址必须指向“宿主机对外端口”。当 `VITE_API_URL` 配错为旧端口/错误端口时，浏览器请求后端会失败并出现 `Network Error`。

## ✅ 唯一正确的对外端口（Docker）

- 前端（浏览器访问）：`http://localhost:13000`
- 后端（浏览器访问）：`http://localhost:18888`
- 容器内端口（仅说明）：前端 `5173`、后端 `8000`

## ✅ 修复方案

### 1) 修正 docker-compose 的前端环境变量

```yaml
frontend:
  environment:
    VITE_API_URL: http://localhost:18888
```

### 2) 重启前端容器使其生效

```bash
docker compose up -d --force-recreate frontend
```

## ✅ 验证

```bash
docker ps
# bidding_frontend ... 0.0.0.0:13000->5173/tcp
# bidding_backend  ... 0.0.0.0:18888->8000/tcp

curl http://localhost:18888/health
```

浏览器验证：打开 `http://localhost:13000`，F12 Console 不应再出现 `Failed to fetch`。

## 技术说明：为什么不是 `backend:8000`？

- `backend:8000` 只适用于容器间通信（Docker 内网）。
- 浏览器访问必须使用宿主机对外端口：`localhost:18888`。
