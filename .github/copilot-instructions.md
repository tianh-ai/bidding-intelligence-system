<!--
Guidance for AI coding agents working on the Bidding Intelligence System.
Keep this file concise and focused on concrete, discoverable patterns.
-->
# Copilot 使用说明（面向 AI 编码助手）

此文档面向直接在仓库中编码的 AI 代理，提供让你迅速产出高质量改动所需的“关键上下文、约定与示例”。请在执行任何改动前先阅读本文件和 `README.md`、`backend/README.md`。

**大局结构**
- **服务入口**：`backend/main.py`（FastAPI）。API 路由在 `backend/routers/`（如 `files.py`, `learning.py`）注册。
- **三层代理架构**：实现分布在 `backend/agents/`，其中 `preprocessor.py`（Layer 1）和 `constraint_extractor.py`（Layer 2）是已实现的两个示例。
- **核心引擎**：`backend/engines/` 包含路由决策、解析、章节/全局学习等（例如 `smart_router.py`, `multi_agent_evaluator.py`）。
- **任务与异步**：Celery 任务定义在 `backend/tasks.py`，Worker 在 `backend/worker.py`（使用 `celery_app`）。任务通常在函数内部延迟导入引擎以避免循环依赖（见 `tasks.py`）。
- **配置与运行时**：强类型配置集中在 `backend/core/config.py`（基于 `pydantic-settings`），日志在 `backend/core/logger.py` 配置。
- **知识图谱与 DB**：本体管理在 `backend/db/ontology.py`，模式在 `backend/db/ontology_schema.sql`。初始化脚本在 `backend/init_database.sql`。

**关键开发/运行工作流（复制可直接运行的命令）**
- 安装（poetry 推荐）：
  - `poetry install` 或 `pip install -r backend/requirements.txt`（在 `backend/`）
- 复制并编辑环境变量：
  - `cp .env.example .env` 然后填写 `OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL` 等（见 `backend/core/config.py` 的字段名）。
- 初始化 DB：
  - `createdb bidding_db`
  - `psql -h localhost -U postgres -d bidding_db -f backend/init_database.sql`
- 启动开发服务：
  - `cd backend && python main.py` 或 `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- 启动 Celery worker：
  - `cd backend && celery -A worker worker --loglevel=info`（确保 Redis 可用或 `CELERY_BROKER_URL` 被正确设置）
- 运行主要测试：
  - `cd backend && python test_final_verification.py`
  - 或 `pytest tests/ -v`

**项目约定与常见模式（请严格遵守）**
- 配置从 `backend/core/config.py` 的 `Settings` 读取；改动配置名需同步 `.env.example` 与使用点。使用 `get_settings()` 获取缓存实例。
- 为避免循环导入，Celery 任务与长流程函数常在函数内部导入引擎模块（见 `backend/tasks.py`）。新增模块若可能被互相引用，请采用相同的延迟导入策略。
- 日志使用 `backend/core/logger.py` 提供的 `logger` 与专用的 `log_task_*` 辅助函数；保持 JSON 格式日志为默认（`LOG_FORMAT`）。
- 数据库连接分为异步和同步两种 URL（见 `database_url` 与 `sync_database_url`），迁移/脚本倾向使用同步 URL。
- 缓存/队列：Redis 同时作为缓存与 Celery broker/result backend（见 `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` 配置优先级）。
- 向量/检索：项目提到 `pgvector` 与向量表 `vectors`，检索逻辑集中于 `backend/db/ontology.py` 與 `engines/smart_router.py`。

**修改/新增代码要点（执行改动前务必检查）**
- 优先阅读 `README.md`、`backend/README.md` 以核对设计目标与未实现功能（例如 `GenerationEngine` 标记为待实现）。
- 修改 API 时更新或添加路由需在 `backend/main.py` 中注册。
- 新增 Celery 任务：在 `backend/tasks.py` 中定义并在 `worker.py` 的 `celery_app` 所在模块导入（遵守任务内延迟导入引擎的惯例）。
- 对数据库 schema 的变更请同时更新 `backend/init_database.sql` 或 `backend/db/ontology_schema.sql`。

**示例片段（常用参考）**
- 调用预处理代理（异步示例）:
```python
from agents.preprocessor import PreprocessorAgent
agent = PreprocessorAgent()
result = await agent.parse_document("tender_document.pdf")
```
- 智能路由器使用示例（来自 README）:
```python
from engines.smart_router import SmartRouter
router = SmartRouter(db_connection)
decision = await router.route_content(requirement)
```

**集成点与外部依赖**
- OpenAI（或其他 LLM）: 由 `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL` 控制（见 `backend/core/config.py`）。
- Redis: 缓存与 Celery broker/result。确保 `REDIS_URL` 或 `CELERY_BROKER_URL` 在 `.env` 中配置。
- PostgreSQL: 主数据库 + 本体知识图谱（pgvector 可选）。

**不要做的事（反面指令）**
- 不要在不理解 `backend/engines/` 设计的情况下重构路由决策逻辑；先写单元测试覆盖再改。
- 不要把全局配置散落到模块内：集中到 `backend/core/config.py`，并通过 `get_settings()` 访问。

如果你需要我把说明调整为更具体的任务（例如：修复某个测试、实现某个引擎或添加 API 路由），请指出目标文件或测试名，我将基于仓库上下文给出精确修改补丁。

---
请审阅此草稿并指出是否需要更多示例或引用其他文件以便补充。 
