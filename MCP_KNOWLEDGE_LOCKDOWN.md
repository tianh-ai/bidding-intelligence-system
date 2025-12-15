# MCP 知识库链路（已验证可用）锁定说明

> 目的：记录“当前已验证正常”的 MCP 知识库链路关键代码与不变量，避免后续误改导致再次断链。
> 
> 验收状态（2025-12-14）：
> - `GET http://localhost:18888/api/knowledge/health` => `{"status":"healthy","mode":"mcp"...}`
> - `GET http://localhost:18888/api/knowledge/statistics` => `source=mcp` 且 `total_entries=64`
> - `POST http://localhost:18888/api/knowledge/entries/list` => `source=mcp` 且返回 `entries`、`total` 正常

---

## 1) 必须保持的不变量（改动这里最容易把链路弄断）

### 1.1 运行方式与端口
- 只允许 Docker 方式运行
- 宿主机对外端口固定：`18888`（容器内 backend 端口 `8000`）

### 1.2 MCP 文件必须在容器内可见
- `docker-compose.yml` 必须包含挂载：`./mcp-servers:/app/mcp-servers:ro`
- 容器内必须存在：`/app/mcp-servers/knowledge-base/dist/index.js`

### 1.3 后端镜像必须包含 Node（用于运行 MCP server）
- `backend/Dockerfile` 必须安装 `nodejs` / `npm`
- 验证命令（容器内）：`node -v`

### 1.4 后端知识库 API 必须“严格走 MCP”
- `backend/routers/knowledge.py`：不允许 DB 直连降级（MCP 不可用应直接报错/不健康）

---

## 2) 关键文件清单（这些文件共同决定 MCP 是否能跑通）

### A. Docker 与运行时
1. `docker-compose.yml`
   - `backend`、`celery_worker` 均挂载：`./mcp-servers:/app/mcp-servers:ro`
   - `backend` 映射端口：`0.0.0.0:18888:8000`

2. `backend/Dockerfile`
   - 必须安装：`nodejs`、`npm`

### B. 后端 MCP 桥接
3. `backend/core/mcp_client.py`
   - `KnowledgeBaseMCPClient` 的路径解析必须兼容：
     - 本地源码结构：`<repo>/mcp-servers/...`
     - Docker（compose 挂载 backend 到 `/app`）：`/app/mcp-servers/...`
   - 不能写死仅一种路径，否则会在 Docker 内找不到 dist。

4. `backend/routers/knowledge.py`
   - 必须只调用 `get_knowledge_base_client()`（MCP）
   - 不允许出现 “try MCP -> except DB” 的降级逻辑

### C. MCP server（Node）
5. `mcp-servers/knowledge-base/dist/index.js`
   - 这是 Docker 内实际执行的入口（`node dist/index.js`）
   - 绝对禁止写死宿主机路径（例如 `/Users/tianmac/...`）
   - 目前采用“动态推导路径 + 注入 `sys.path`”调用 Python backend

6. `mcp-servers/knowledge-base/src/index.ts`
   - TS 源码，逻辑应与 `dist/index.js` 一致
   - 若未来重新 `npm run build`，务必确认 dist 中仍是动态路径（不要回退成硬编码路径）

### D. MCP Python backend（知识库 SQL 兼容）
7. `mcp-servers/knowledge-base/python/knowledge_base.py`
   - 关键点：必须兼容当前数据库 `knowledge_base` 表结构
   - 当前实际表结构（见 `backend/init_database.py`）缺少：`keywords`、`importance_score`、`metadata`
   - 因此 `knowledge_base.py` 必须：
     - 动态探测字段（`information_schema.columns`）
     - **不能**在 SQL 里硬写 `SELECT keywords, importance_score` 等不存在字段
     - 缺失字段时返回默认值：`keywords=[]`、`importance_score=0.0`、`metadata={}`

---

## 3) 已修复的历史故障根因（以后遇到同样现象优先查这里）

### 故障 1：`ModuleNotFoundError: No module named 'knowledge_base'`
- 根因：`dist/index.js` 写死了宿主机路径 `/Users/tianmac/...`，容器内不存在
- 正确做法：在 Node 侧动态计算 `kbRoot/repoRoot`，把 `knowledge-base/python` 和 `backend` 注入到 Python 的 `sys.path`

### 故障 2：`column "keywords" does not exist`
- 根因：`knowledge_base.py` 假设 DB 表有 `keywords/importance_score/metadata` 字段，但实际 schema 没有
- 正确做法：动态探测字段后再拼 SELECT/ORDER BY/INSERT；缺失字段返回默认值

---

## 4) 未来修改的“红线”

- 禁止在 `mcp-servers/knowledge-base/dist/index.js` 里引入任何宿主机绝对路径
- 禁止在 `backend/routers/knowledge.py` 加回 DB 降级（用户要求：必须走 MCP）
- 禁止在 `knowledge_base.py` 里硬编码不存在字段（除非你同时做了 DB schema 迁移，并验证全部 API）

---

## 5) 最小回归验证（每次改动后必须跑）

```bash
# 1) 重建（仅当改了 backend/Dockerfile 或依赖）
docker compose up -d --build backend celery_worker

# 2) MCP 健康
curl -sS http://localhost:18888/api/knowledge/health

# 3) 统计（必须 source=mcp）
curl -sS http://localhost:18888/api/knowledge/statistics

# 4) 列表（必须 source=mcp 且 entries 非空）
curl -sS -X POST http://localhost:18888/api/knowledge/entries/list \
  -H 'Content-Type: application/json' \
  -d '{"limit":5,"offset":0}'
```

---

## 6) 一键定位 MCP 断链（出现 unhealthy 时）

```bash
# 容器内检查：Node + dist 是否存在
docker exec -it bidding_backend sh -lc "node -v && ls -la /app/mcp-servers/knowledge-base/dist/index.js"

# 后端日志（看 MCP/Node/Python 报错链）
docker compose logs --tail=200 backend
```
