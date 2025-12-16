# 🏗️ 模块化架构设计方案

> **设计理念**: 通过 MCP 服务器 + 独立技能（Skills）实现功能解耦、接口统一、易于调试和升级  
> **更新日期**: 2025-12-16

---

## 📋 目录

- [1. 架构设计原则](#1-架构设计原则)
- [2. 模块分类策略](#2-模块分类策略)
- [3. 标准目录结构](#3-标准目录结构)
- [4. 接口规范](#4-接口规范)
- [5. 现有功能模块清单](#5-现有功能模块清单)
- [6. 迁移实施计划](#6-迁移实施计划)
- [7. 开发指南](#7-开发指南)
- [8. 质量保障](#8-质量保障)

---

## 1. 架构设计原则

### 1.1 核心原则

#### ✅ 单一职责原则（SRP）
- 每个 MCP 服务器只负责一个领域
- 每个 Skill 只实现一个具体功能
- 避免功能耦合和交叉依赖

#### ✅ 接口标准化
- 所有 MCP 服务器遵循 Model Context Protocol 规范
- 统一的输入输出格式（JSON Schema）
- 标准的错误处理机制

#### ✅ 可插拔设计
- 任何模块可独立升级或替换
- 不影响其他模块运行
- 支持多种实现方式（本地/远程/第三方）

#### ✅ 易于测试和调试
- 每个模块有独立测试套件
- 清晰的日志和错误追踪
- 支持单元测试和集成测试

---

## 2. 模块分类策略

### 2.1 MCP 服务器（适用场景）

**特征**: 需要 AI 助手（Claude、Copilot）直接调用的功能

**适用功能**:
- ✅ **文档解析** - AI 需要理解文档结构
- ✅ **知识库检索** - AI 需要查询历史数据
- ✅ **逻辑验证** - AI 需要检查内容一致性
- ✅ **专家咨询** - AI 需要获取领域知识

**优势**:
- AI 可直接调用，无需编写胶水代码
- 标准化接口，多平台兼容
- 独立进程，故障隔离

**劣势**:
- 启动开销（需要 Node 进程）
- 跨语言通信（TypeScript ↔ Python）

---

### 2.2 独立技能（Skills）

**特征**: 后端 API 调用的纯功能模块

**适用功能**:
- ✅ **表格提取** - 纯技术处理
- ✅ **OCR识别** - 图像处理
- ✅ **格式转换** - 数据转换
- ✅ **缓存管理** - 基础设施

**优势**:
- 轻量级，无额外进程
- Python 直接调用，性能高
- 易于单元测试

**实现方式**:
```python
# backend/skills/table_extractor.py
class TableExtractorSkill:
    """表格提取技能 - 独立可测试"""
    
    def extract(self, pdf_path: str) -> List[Table]:
        """提取表格"""
        # 纯功能实现
        pass
```

---

### 2.3 混合模式

**场景**: 既需要 AI 调用，又需要后端直接调用

**示例**: 知识库（Knowledge Base）
- **MCP 层**: 供 AI 助手查询知识
- **HTTP API 层**: 供前端调用
- **Python SDK 层**: 供后端引擎调用

**架构**:
```
┌─────────────────────────────────────────┐
│  AI 助手（Claude Desktop）               │
│  ↓ MCP 协议                              │
│  知识库 MCP 服务器 (Node.js)              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  前端（React）                           │
│  ↓ HTTP API                              │
│  FastAPI 路由 (routers/knowledge.py)     │
│  ↓ Python SDK                            │
│  知识库引擎 (engines/knowledge_engine.py)│
└─────────────────────────────────────────┘
```

---

## 3. 标准目录结构

### 3.1 整体结构

```
bidding-intelligence-system/
├── .github/
│   └── copilot-instructions.md        # AI 助手使用规范
│
├── docs/                               # 📚 规范文档（骨架）
│   ├── MODULAR_ARCHITECTURE.md        # 本文件
│   ├── DOCKER_PRINCIPLES.md           # Docker 规范
│   ├── PORT_CONSISTENCY.md            # 端口规范
│   ├── CODE_PROTECTION.md             # 代码保护规范
│   ├── API_STANDARDS.md               # 🆕 API 接口规范
│   ├── TESTING_GUIDE.md               # 🆕 测试指南
│   └── DEPLOYMENT_GUIDE.md            # 部署指南
│
├── mcp-servers/                        # 🔌 MCP 服务器集合
│   ├── README.md                       # MCP 总览
│   ├── document-parser/                # 文档解析 MCP
│   ├── knowledge-base/                 # 知识库 MCP
│   ├── logic-checking/                 # 🆕 逻辑验证 MCP
│   ├── logic-learning/                 # 🆕 逻辑学习 MCP
│   └── expert-advisor/                 # 🆕 专家顾问 MCP
│
├── backend/
│   ├── skills/                         # 🎯 独立技能模块（新增）
│   │   ├── __init__.py
│   │   ├── table_extractor.py         # 表格提取技能
│   │   ├── ocr_processor.py           # OCR 处理技能
│   │   ├── format_converter.py        # 格式转换技能
│   │   ├── cache_manager.py           # 缓存管理技能
│   │   └── image_processor.py         # 图像处理技能
│   │
│   ├── engines/                        # 🚀 业务引擎（调用 Skills）
│   │   ├── parse_engine.py            # 调用 table_extractor
│   │   ├── smart_router.py            # 调用 cache_manager
│   │   └── ...
│   │
│   ├── routers/                        # 🌐 HTTP API 路由
│   │   ├── files.py
│   │   ├── knowledge.py               # 调用 knowledge MCP
│   │   └── ...
│   │
│   ├── core/                           # 🔧 核心基础设施
│   │   ├── mcp_client.py              # MCP 客户端基类
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── cache.py
│   │
│   └── tests/                          # 🧪 测试套件
│       ├── test_skills/               # 技能单元测试
│       ├── test_engines/              # 引擎集成测试
│       └── test_mcp/                  # MCP 端到端测试
│
└── frontend/                           # 前端（保持现状）
```

---

### 3.2 MCP 服务器标准结构

每个 MCP 服务器遵循统一结构：

```
mcp-servers/<service-name>/
├── package.json                # Node.js 配置
├── tsconfig.json               # TypeScript 配置
├── setup.sh                    # 一键安装脚本
├── README.md                   # 服务文档
│
├── src/
│   └── index.ts                # MCP 协议实现（TypeScript）
│
├── python/                     # Python 后端（可选）
│   └── <service>_backend.py   # 实际业务逻辑
│
├── test/
│   ├── test_mcp.py            # MCP 协议测试
│   ├── test_backend.py        # 后端逻辑测试
│   └── test_integration.sh    # 集成测试脚本
│
└── dist/                       # 编译输出（自动生成）
    └── index.js
```

---

### 3.3 Skill 模块标准结构

```python
# backend/skills/<skill_name>.py

from typing import Any, Dict, List
from pydantic import BaseModel

class <Skill>Input(BaseModel):
    """输入模型 - 强类型验证"""
    pass

class <Skill>Output(BaseModel):
    """输出模型 - 标准化返回"""
    pass

class <Skill>Skill:
    """
    <功能描述>
    
    职责:
        - 单一功能实现
        - 无外部依赖（除标准库）
        - 可独立测试
    
    示例:
        >>> skill = <Skill>Skill()
        >>> result = skill.execute(input_data)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
    
    def execute(self, input_data: <Skill>Input) -> <Skill>Output:
        """执行技能主逻辑"""
        raise NotImplementedError
    
    def validate(self, input_data: Any) -> bool:
        """验证输入数据"""
        return True
```

---

## 4. 接口规范

### 4.1 MCP 服务器接口规范

#### 初始化响应格式
```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": {
    "tools": {}
  },
  "serverInfo": {
    "name": "service-name",
    "version": "1.0.0"
  }
}
```

#### 工具定义格式
```typescript
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "action_name",
      description: "清晰的功能描述（中文）",
      inputSchema: {
        type: "object",
        properties: {
          param1: {
            type: "string",
            description: "参数说明"
          }
        },
        required: ["param1"]
      }
    }
  ]
}));
```

#### 错误响应格式
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "详细错误信息",
    "details": {
      "field": "field_name",
      "reason": "validation failed"
    }
  }
}
```

---

### 4.2 HTTP API 接口规范

遵循 RESTful 设计：

```python
# POST /api/<resource>/action
@router.post("/<resource>/action")
async def action(request: ActionRequest) -> ActionResponse:
    """
    功能描述
    
    Args:
        request: 请求体（Pydantic 模型）
    
    Returns:
        ActionResponse: 标准响应
    
    Raises:
        HTTPException: 错误情况
    """
    try:
        # 调用 Skill 或 Engine
        result = skill.execute(request)
        return ActionResponse(
            success=True,
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**标准响应格式**:
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2025-12-16T10:00:00Z"
}
```

---

### 4.3 Skill 接口规范

```python
class SkillInterface:
    """技能接口规范（抽象基类）"""
    
    @abstractmethod
    def execute(self, input_data: BaseModel) -> BaseModel:
        """执行主逻辑"""
        pass
    
    def validate(self, input_data: Any) -> bool:
        """验证输入"""
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """返回技能元数据"""
        return {
            "name": self.__class__.__name__,
            "version": "1.0.0",
            "description": self.__doc__
        }
```

---

## 5. 现有功能模块清单

### 5.1 已实现 MCP 服务器 ✅

| MCP 服务器 | 路径 | 状态 | 调用方式 |
|-----------|------|------|---------|
| **document-parser** | `mcp-servers/document-parser/` | ✅ 已完成 | AI 助手直接调用 |
| **knowledge-base** | `mcp-servers/knowledge-base/` | ✅ 已完成 | AI + HTTP API + Python SDK |
| **logic-checking** | `mcp-servers/logic-checking/` | 🟡 部分实现 | 需要完善 |
| **logic-learning** | `mcp-servers/logic-learning/` | 🟡 部分实现 | 需要完善 |

---

### 5.2 待转换为 MCP 的功能 🔄

| 功能模块 | 当前实现 | 优先级 | 转换难度 | 建议 |
|---------|---------|-------|---------|-----|
| **逻辑验证** | `engines/chapter_logic_engine.py` | 🔴 高 | 中 | → MCP: `logic-checking` |
| **逻辑学习** | `engines/logic_learning_engine.py` | 🔴 高 | 中 | → MCP: `logic-learning` |
| **专家系统** | `engines/multi_agent_evaluator.py` | 🟡 中 | 高 | → MCP: `expert-advisor` |
| **文档分类** | `engines/smart_document_classifier.py` | 🟢 低 | 低 | → Skill |
| **格式提取** | `engines/format_extractor.py` | 🟢 低 | 低 | → Skill |

---

### 5.3 适合作为 Skill 的功能 🎯

| 功能 | 当前实现 | 新位置 | 状态 |
|------|---------|--------|-----|
| **表格提取** | `agents/preprocessor.py` (部分) | `skills/table_extractor.py` | 🆕 待创建 |
| **OCR 处理** | `engines/ocr_extractor.py` | `skills/ocr_processor.py` | 🆕 待创建 |
| **图像处理** | `engines/image_extractor.py` | `skills/image_processor.py` | 🆕 待创建 |
| **格式转换** | 分散在多个文件 | `skills/format_converter.py` | 🆕 待创建 |
| **缓存管理** | `core/cache.py` | `skills/cache_manager.py` | 🆕 待创建 |

---

### 5.4 保持现状的模块 ✋

| 模块 | 原因 | 位置 |
|------|------|------|
| **路由层** | FastAPI 标准实现 | `routers/*` |
| **数据库层** | SQLAlchemy ORM | `db/*` |
| **配置管理** | 已标准化 | `core/config.py` |
| **日志系统** | 已标准化 | `core/logger.py` |
| **前端** | 独立 React 应用 | `frontend/*` |

---

## 6. 迁移实施计划

### 阶段 1: 基础设施准备（Week 1）

**目标**: 建立规范和模板

- [x] 创建 `MODULAR_ARCHITECTURE.md`（本文件）
- [ ] 创建 `docs/API_STANDARDS.md`
- [ ] 创建 `docs/TESTING_GUIDE.md`
- [ ] 创建 `backend/skills/` 目录
- [ ] 创建 Skill 模板和测试模板

**验收标准**:
- ✅ 所有规范文档完成
- ✅ 目录结构就绪
- ✅ 开发指南可用

---

### 阶段 2: 提取核心 Skills（Week 2-3）

**优先级**: 🔴 高

**任务列表**:
1. **表格提取 Skill**
   - 从 `agents/preprocessor.py` 提取 `pdfplumber` 逻辑
   - 创建 `skills/table_extractor.py`
   - 编写单元测试 `tests/test_skills/test_table_extractor.py`
   - 更新 `engines/parse_engine.py` 调用新 Skill

2. **图像处理 Skill**
   - 迁移 `engines/image_extractor.py` → `skills/image_processor.py`
   - 标准化输入输出格式
   - 保持原有 API 兼容性

3. **格式转换 Skill**
   - 整合分散的格式转换逻辑
   - 创建 `skills/format_converter.py`
   - 支持 PDF/DOCX/TXT 互转

**验收标准**:
- ✅ 所有 Skill 有独立测试
- ✅ 原有功能零破坏
- ✅ 代码覆盖率 > 80%

---

### 阶段 3: 完善 MCP 服务器（Week 4-5）

**优先级**: 🔴 高

**任务列表**:
1. **逻辑验证 MCP**
   - 完善 `mcp-servers/logic-checking/`
   - 实现章节逻辑一致性检查
   - 提供 AI 可调用的验证工具

2. **逻辑学习 MCP**
   - 完善 `mcp-servers/logic-learning/`
   - 实现学习结果存储和检索
   - 支持增量学习

3. **专家顾问 MCP**（可选）
   - 新建 `mcp-servers/expert-advisor/`
   - 封装 `multi_agent_evaluator` 功能
   - 提供专家评审建议

**验收标准**:
- ✅ MCP 服务器可独立运行
- ✅ AI 助手可成功调用
- ✅ HTTP API 同步提供

---

### 阶段 4: 测试和文档（Week 6）

**优先级**: 🟡 中

**任务列表**:
- [ ] 编写集成测试套件
- [ ] 更新 README.md
- [ ] 录制使用演示视频
- [ ] 性能基准测试

**验收标准**:
- ✅ 端到端测试通过
- ✅ 文档完整准确
- ✅ 性能无回退

---

### 阶段 5: 优化和推广（Week 7+）

**优先级**: 🟢 低

**任务列表**:
- [ ] 性能优化（缓存、并发）
- [ ] 监控和告警
- [ ] 开发者培训
- [ ] 社区推广

---

## 7. 开发指南

### 7.1 创建新 MCP 服务器

#### 步骤 1: 使用模板

```bash
cd mcp-servers
cp -r document-parser/ my-new-service/
cd my-new-service
```

#### 步骤 2: 修改配置

```json
// package.json
{
  "name": "@bidding/mcp-my-service",
  "description": "我的新服务",
  "main": "dist/index.js"
}
```

#### 步骤 3: 实现工具

```typescript
// src/index.ts
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  switch (name) {
    case "my_tool":
      return await handleMyTool(args);
    default:
      throw new Error(`未知工具: ${name}`);
  }
});
```

#### 步骤 4: Python 后端（可选）

```python
# python/my_service_backend.py
def handle_my_tool(params: dict) -> dict:
    """实际业务逻辑"""
    return {"result": "success"}
```

#### 步骤 5: 测试

```bash
./setup.sh
npm test
python test/test_mcp.py
```

---

### 7.2 创建新 Skill

#### 模板

```python
# backend/skills/my_skill.py

from typing import Any, Dict
from pydantic import BaseModel, Field

class MySkillInput(BaseModel):
    """输入参数"""
    data: str = Field(..., description="输入数据")

class MySkillOutput(BaseModel):
    """输出结果"""
    result: str
    confidence: float

class MySkill:
    """
    我的技能描述
    
    职责: 单一功能
    依赖: 无外部依赖
    """
    
    def __init__(self):
        pass
    
    def execute(self, input_data: MySkillInput) -> MySkillOutput:
        """执行主逻辑"""
        # 实现功能
        return MySkillOutput(
            result="处理结果",
            confidence=0.95
        )
```

#### 测试

```python
# backend/tests/test_skills/test_my_skill.py

import pytest
from skills.my_skill import MySkill, MySkillInput

def test_my_skill_basic():
    skill = MySkill()
    input_data = MySkillInput(data="测试数据")
    output = skill.execute(input_data)
    
    assert output.result is not None
    assert output.confidence > 0.0
```

---

### 7.3 集成到引擎

```python
# backend/engines/my_engine.py

from skills.my_skill import MySkill, MySkillInput

class MyEngine:
    def __init__(self):
        self.skill = MySkill()
    
    def process(self, data: str) -> dict:
        """调用 Skill 处理数据"""
        input_data = MySkillInput(data=data)
        result = self.skill.execute(input_data)
        return result.dict()
```

---

### 7.4 代码保护规则

⚠️ **修改前必读**:

1. **运行端口检查**:
   ```bash
   ./check_ports.sh
   ```

2. **检查受保护文件**:
   - 阅读 `CODE_PROTECTION.md`
   - 验证文件是否在保护列表

3. **创建分支**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

4. **编写测试**:
   - 先写测试，后写实现（TDD）
   - 确保覆盖率 > 80%

5. **运行验证**:
   ```bash
   python verify_knowledge_display.py
   pytest tests/
   ```

---

## 8. 质量保障

### 8.1 测试要求

#### 单元测试
- **覆盖率**: > 80%
- **工具**: `pytest`
- **位置**: `backend/tests/test_skills/`

```bash
pytest tests/test_skills/ --cov=skills --cov-report=html
```

#### 集成测试
- **范围**: MCP 服务器 + HTTP API
- **位置**: `backend/tests/test_mcp/`

```bash
pytest tests/test_mcp/ -v
```

#### 端到端测试
- **范围**: 完整业务流程
- **工具**: `test_final_verification.py`

```bash
python test_final_verification.py
```

---

### 8.2 性能要求

| 指标 | 目标 | 测试方法 |
|------|------|---------|
| **API 响应时间** | < 500ms (P95) | `pytest-benchmark` |
| **MCP 启动时间** | < 2s | 手动测试 |
| **内存占用** | < 500MB (单进程) | `memory_profiler` |
| **并发处理** | > 10 req/s | `locust` 负载测试 |

---

### 8.3 代码质量

#### 静态检查
```bash
# 类型检查
mypy backend/skills/

# 代码风格
black backend/skills/
flake8 backend/skills/
```

#### 安全检查
```bash
# 依赖漏洞扫描
pip-audit

# 代码安全扫描
bandit -r backend/
```

---

## 9. 常见问题

### Q1: 什么时候用 MCP，什么时候用 Skill？

**判断标准**:
- AI 需要直接调用 → **MCP**
- 后端内部调用 → **Skill**
- 两者都需要 → **混合模式**（如 knowledge-base）

### Q2: 如何处理现有代码迁移？

**原则**:
1. **不破坏现有功能** - 先创建新实现，后替换
2. **保持 API 兼容** - 旧接口继续工作
3. **渐进式迁移** - 一次只迁移一个模块
4. **充分测试** - 迁移前后功能一致

### Q3: MCP 服务器启动失败怎么办？

**排查步骤**:
```bash
# 1. 检查编译
cd mcp-servers/<service-name>
npm run build

# 2. 检查依赖
npm install

# 3. 查看日志
node dist/index.js  # 直接运行看错误

# 4. 测试 Python 后端
python python/<backend>.py
```

### Q4: 如何调试 MCP 通信？

**方法**:
```python
# backend/debug_mcp.py
import asyncio
from core.mcp_client import get_knowledge_base_client

async def debug():
    client = get_knowledge_base_client()
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    result = await client.call_tool("search_knowledge", {
        "query": "测试"
    })
    print(result)

asyncio.run(debug())
```

---

## 10. 参考资源

### 内部文档
- [CODE_PROTECTION.md](./CODE_PROTECTION.md) - 代码保护规范
- [DOCKER_PRINCIPLES.md](./DOCKER_PRINCIPLES.md) - Docker 使用原则
- [PORT_CONSISTENCY.md](./PORT_CONSISTENCY.md) - 端口一致性原则
- [mcp-servers/README.md](./mcp-servers/README.md) - MCP 服务器总览

### 外部资源
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 官方文档
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/) - FastAPI 指南
- [Pydantic Documentation](https://docs.pydantic.dev/) - 数据验证

---

## 11. 更新日志

| 日期 | 版本 | 变更内容 |
|------|------|---------|
| 2025-12-16 | 1.0.0 | 初始版本，定义架构规范 |

---

**维护者**: Copilot + 开发团队  
**联系方式**: 见项目 README.md
