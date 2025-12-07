<!--
AI Coding Agent Instructions for Bidding Intelligence System
Concise, actionable guidance focused on discoverable patterns and critical context.
-->

# Copilot 使用说明

**在做任何修改前，请先阅读本文件及 `README.md`、`backend/README.md`。**

## 核心架构

这是一个**AI驱动的标书智能系统**，采用三层代理架构 + 本体知识图谱 + 85/10/5智能路由策略。

### 服务结构
```
backend/main.py (FastAPI)
├── routers/          # API路由 (files.py, learning.py, enhanced.py, self_learning.py)
├── agents/           # 三层代理架构
│   ├── preprocessor.py          # Layer 1: 结构化解析 (pdfplumber表格提取)
│   └── constraint_extractor.py  # Layer 2: 约束提取 (OpenAI Function Calling)
├── engines/          # 智能引擎 (15个引擎)
│   ├── smart_router.py          # 85/10/5路由决策
│   ├── multi_agent_evaluator.py # 三层评估系统
│   ├── parse_engine.py          # 文档解析
│   └── ...
├── db/
│   ├── ontology.py              # 本体知识图谱管理
│   └── ontology_schema.sql      # 9节点+7关系类型
├── core/
│   ├── config.py                # 强类型配置 (pydantic-settings)
│   ├── logger.py                # JSON格式日志 (Loguru)
│   └── cache.py                 # Redis缓存装饰器
├── tasks.py          # Celery异步任务
└── worker.py         # Celery Worker

frontend/src/         # React + TypeScript + Refine + Ant Design
├── pages/            # 6个核心页面 (Dashboard, FileUpload, LogicLearning, FileSummary, LLMManagement, Login)
├── components/       # AIChatPanel, AppHeader, AppSidebar
├── layouts/          # MainLayout (VSCode风格三栏布局)
├── store/            # Zustand状态管理 (authStore, chatStore, layoutStore)
├── services/         # API调用层
└── types/            # TypeScript类型定义
```

## 开发工作流

### 后端环境设置
```bash
# 1. 安装依赖
cd backend && pip install -r requirements.txt

# 2. 环境变量（关键配置见 backend/core/config.py）
cp .env.example .env
# 必填: OPENAI_API_KEY, DB_*, REDIS_*

# 3. 初始化数据库
createdb bidding_db
psql -h localhost -U postgres -d bidding_db -f backend/init_database.sql

# 4. 启动服务
cd backend && python main.py              # API (默认端口8000)
cd backend && celery -A worker worker --loglevel=info  # Worker
```

### 前端环境设置
```bash
# 1. 安装依赖
cd frontend && npm install  # 或 pnpm install

# 2. 环境变量
cp .env.example .env
# VITE_API_URL=http://localhost:8000

# 3. 启动开发服务器
npm run dev  # 或 ./start.sh (端口5173)
```

### Docker 一键启动（推荐）
```bash
docker-compose up -d  # 端口: postgres:5433, redis:6380, backend:8001, frontend:5173
```. 启动服务
cd backend && python main.py              # API (默认端口8000)
cd backend && celery -A worker worker --loglevel=info  # Worker

# Docker方式（推荐）
docker-compose up -d                       # 端口: postgres:5433, redis:6380, backend:8001, frontend:5173
```

### 测试
```bash
# 主验证测试
cd backend && python test_final_verification.py

# 专家系统测试
python test_expert_system.py

# 单元测试
pytest tests/ -v
```

## 关键约定（必须遵守）

### 1. 配置管理
- **所有配置**必须在 `backend/core/config.py` 的 `Settings` 类中定义
- 使用 `get_settings()` 获取配置实例（LRU缓存）
- 修改配置名时同步更新 `.env.example`

```python
# ✅ 正确
from core.config import get_settings
settings = get_settings()
api_key = settings.OPENAI_API_KEY

# ❌ 错误
import os
api_key = os.getenv("OPENAI_API_KEY")  # 绕过类型验证
```

### 2. 避免循环导入
- **Celery任务**和长流程函数在函数内部延迟导入引擎（见 `tasks.py` 模式）
- 新增可能互相引用的模块时采用相同策略

```python
# tasks.py 中的标准模式
@celery_app.task
def process_document(file_path: str):
    # ✅ 函数内导入避免循环依赖
    from backend.engines.parse_engine import HybridParseEngine
    parser = HybridParseEngine()
    return parser.parse(file_path)
```

### 3. 数据库连接
### 5. Pydantic模型优先（后端）
- 所有数据结构用 `BaseModel` 定义（强类型验证）
- API响应、配置、数据流都遵循此模式
- OpenAI Function Calling通过Pydantic schema生成

```python
from pydantic import BaseModel, Field

class RoutingDecision(BaseModel):
    requirement_id: str
    source: ContentSource  # Enum
    similarity_score: float
    reasoning: str
```

## 实现模式参考

### 后端模式

#### API路由注册ore/` 目录：`authStore.ts`, `chatStore.ts`, `layoutStore.ts`
- 组件中通过 hooks 访问状态

```typescript
// 使用 Zustand store
import { useChatStore } from '@/store/chatStore'

const { messages, addMessage, isLoading } = useChatStore()
```

### 7. 前端路由约定
- 使用 React Router v6，路由定义在 `App.tsx`
- 受保护路由通过 `MainLayout` 包裹，自动检查 `isAuthenticated`
- 所有页面组件在 `pages/` 目录

### 5. Pydantic模型优先
- 所有数据结构用 `BaseModel` 定义（强类型验证）
- API响应、配置、数据流都遵循此模式
- OpenAI Function Calling通过Pydantic schema生成

```python
from pydantic import BaseModel, Field

class RoutingDecision(BaseModel):
    requirement_id: str
    source: ContentSource  # Enum
    similarity_score: float
    reasoning: str
### 多代理评估
```python
from engines.multi_agent_evaluator import MultiAgentEvaluator

evaluator = MultiAgentEvaluator()
result = await evaluator.evaluate(
    generated_content=content,
    requirements=requirements,
    use_ontology=True  # 启用知识图谱验证
)
# 返回: score, violations, recommendations
```

## 外部依赖集成

### 后端依赖

| 服务 | 配置 | 用途 |
|------|------|------|
| **OpenAI** | `OPENAI_API_KEY`, `OPENAI_MODEL` (gpt-4-turbo) | LLM推理 + Function Calling |
| **PostgreSQL** | `DB_HOST`, `DB_PORT`, `DB_NAME` | 主数据库 + 本体图谱 (24张表) |
| **Redis** | `REDIS_HOST`, `REDIS_PORT` | 缓存 + Celery broker/backend |
| **pdfplumber** | 无需配置 | 表格提取（准确率90% vs PyPDF 30%） |

### 前端依赖

| 库 | 版本 | 用途 |
|------|------|------|
| **React** | 18.2 | UI框架 |
| **Ant Design** | 5.12 | UI组件库（暗色主题 Grok 风格） |
| **Refine** | 4.47 | 数据管理框架 |
| **Zustand** | 4.4 | 轻量级状态管理 |
| **React Router** | 6.21 | 路由管理 |
| **react-split** | 2.0 | 可调整宽度的分栏布局 |
| **react-markdown** | 9.0 | Markdown 渲染 |
  // 1. State hooks
  const [currentStep, setCurrentStep] = useState(0)
## 反面指令（禁止）

### 后端禁止事项
- ❌ 不要直接修改 `backend/engines/smart_router.py` 的路由逻辑，除非有单元测试覆盖
- ❌ 不要在多个文件重复配置逻辑，统一到 `core/config.py`
- ❌ 不要跳过 Pydantic 验证直接操作字典
- ❌ 不要在循环中多次调用 LLM（使用批处理或缓存）
- ❌ 不要修改数据库schema而不更新 `init_database.sql`
## 核心文件索引

### 后端核心文件

| 文件 | 作用 | 行数 |
|------|------|------|
| `backend/main.py` | FastAPI入口 | 61 |
| `backend/core/config.py` | 配置管理 | 147 |
| `backend/agents/preprocessor.py` | 文档解析 | 380 |
| `backend/engines/smart_router.py` | 智能路由 | 433 |
| `backend/engines/multi_agent_evaluator.py` | 评估系统 | 563 |
| `backend/db/ontology.py` | 知识图谱 | 478 |
| `backend/tasks.py` | Celery任务 | 255 |

### 前端核心文件

| 文件 | 作用 | 关键特性 |
|------|------|---------|
| `frontend/src/App.tsx` | 应用入口，路由配置 | Grok 暗色主题 |
| `frontend/src/layouts/MainLayout.tsx` | VSCode 风格三栏布局 | react-split 可调整宽度 |
| `frontend/src/components/AIChatPanel.tsx` | AI 对话面板 | Markdown 渲染，多轮对话 |
| `frontend/src/pages/LogicLearning.tsx` | 逻辑学习页面（最复杂） | 章节/全局学习，4步流程 |
| `frontend/src/store/chatStore.ts` | 对话状态管理 | Zustand store |
| `frontend/src/services/api.ts` | API 调用封装 | Axios + 统一错误处理 |nd
  return (
    <div className="space-y-6">
      <Card className="grok-card">
        {/* Content */}
      </Card>
    </div>
  )
}
```

#### VSCode 风格布局（MainLayout.tsx）
```typescript
import Split from 'react-split'

// 使用 react-split 实现可调整宽度的三栏布局
<Split
  sizes={isChatOpen ? [70, 30] : [100, 0]}
  minSize={[400, 300]}
  direction="horizontal"
>
  <Content>{/* 主工作区 */}</Content>
  {isChatOpen && <AIChatPanel />}
</Split>
```

#### AI 对话调用
```typescript
import { llmAPI } from '@/services/api'

const response = await llmAPI.chat({
  message: input,
  conversationId: conversationId || undefined,
})
```
### 智能路由器调用
```python
from engines.smart_router import SmartRouter

router = SmartRouter()
decision = await router.route_requirement(
    requirement_id="req_001",
    query_text="项目经理资质要求",
    threshold=0.85  # 相似度阈值
)
# decision.source: kb_exact_match | llm_adapt | llm_generate
```

### 预处理代理使用
```python
from agents.preprocessor import PreprocessorAgent

agent = PreprocessorAgent()
doc_structure = agent.parse_document(file_path="tender.pdf")
# 返回 DocumentStructure (包含 TextBlock, TableBlock, ChapterNode)
```

### 多代理评估
```python
from engines.multi_agent_evaluator import MultiAgentEvaluator

evaluator = MultiAgentEvaluator()
result = await evaluator.evaluate(
    generated_content=content,
    requirements=requirements,
    use_ontology=True  # 启用知识图谱验证
)
# 返回: score, violations, recommendations
```

## 外部依赖集成

| 服务 | 配置 | 用途 |
|------|------|------|
| **OpenAI** | `OPENAI_API_KEY`, `OPENAI_MODEL` (gpt-4-turbo) | LLM推理 + Function Calling |
| **PostgreSQL** | `DB_HOST`, `DB_PORT`, `DB_NAME` | 主数据库 + 本体图谱 (24张表) |
| **Redis** | `REDIS_HOST`, `REDIS_PORT` | 缓存 + Celery broker/backend |
| **pdfplumber** | 无需配置 | 表格提取（准确率90% vs PyPDF 30%） |

## 反面指令（禁止）

- ❌ 不要直接修改 `backend/engines/smart_router.py` 的路由逻辑，除非有单元测试覆盖
- ❌ 不要在多个文件重复配置逻辑，统一到 `core/config.py`
- ❌ 不要跳过 Pydantic 验证直接操作字典
- ❌ 不要在循环中多次调用 LLM（使用批处理或缓存）
- ❌ 不要修改数据库schema而不更新 `init_database.sql`

## 核心文件索引

| 文件 | 作用 | 行数 |
|------|------|------|
| `backend/main.py` | FastAPI入口 | 61 |
| `backend/core/config.py` | 配置管理 | 147 |
| `backend/agents/preprocessor.py` | 文档解析 | 380 |
| `backend/engines/smart_router.py` | 智能路由 | 433 |
| `backend/engines/multi_agent_evaluator.py` | 评估系统 | 563 |
| `backend/db/ontology.py` | 知识图谱 | 478 |
| `backend/tasks.py` | Celery任务 | 255 |

---

**需要特定任务的实现细节？** 指定文件名或功能模块，我可基于代码库提供精确补丁。
