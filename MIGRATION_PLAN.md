# 🚀 模块化迁移实施计划

> **目标**: 6周内完成核心功能的 MCP + Skills 架构转型  
> **原则**: 渐进式迁移，零功能破坏，充分测试  
> **更新日期**: 2025-12-16

---

## 📅 总体时间线

```
Week 1: 基础准备 + 第一个 Skill
Week 2-3: 核心 Skills 实现
Week 4-5: MCP 服务器完善
Week 6: 测试与文档
Week 7+: 优化与推广
```

---

## 🎯 阶段 1: 基础设施准备（Week 1）

### 目标
建立开发规范、目录结构和模板

### 任务清单

#### 1.1 规范文档（已完成）
- [x] `MODULAR_ARCHITECTURE.md` - 架构设计
- [x] `MODULE_INVENTORY.md` - 功能清单
- [x] `MIGRATION_PLAN.md` - 本文件
- [ ] `docs/API_STANDARDS.md` - API 接口规范
- [ ] `docs/TESTING_GUIDE.md` - 测试指南

#### 1.2 目录结构
```bash
# 创建 Skills 目录
mkdir -p backend/skills
touch backend/skills/__init__.py

# 创建测试目录
mkdir -p backend/tests/test_skills
mkdir -p backend/tests/test_mcp

# 创建 docs 目录
mkdir -p docs
```

#### 1.3 模板文件
**创建**: `backend/skills/_template_skill.py`
```python
"""
Skill 模板文件
复制此文件开始创建新 Skill
"""
from typing import Any, Dict
from pydantic import BaseModel, Field

class TemplateSkillInput(BaseModel):
    """输入参数"""
    data: str = Field(..., description="输入数据")

class TemplateSkillOutput(BaseModel):
    """输出结果"""
    result: str
    confidence: float = 1.0

class TemplateSkill:
    """
    Skill 功能描述
    
    职责:
        - 单一功能
        - 无外部依赖
    
    示例:
        >>> skill = TemplateSkill()
        >>> output = skill.execute(TemplateSkillInput(data="test"))
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def execute(self, input_data: TemplateSkillInput) -> TemplateSkillOutput:
        """执行主逻辑"""
        # TODO: 实现功能
        return TemplateSkillOutput(result="success", confidence=1.0)
    
    def validate(self, input_data: TemplateSkillInput) -> bool:
        """验证输入"""
        return True
```

**创建**: `backend/tests/test_skills/_template_test.py`
```python
"""
Skill 测试模板
"""
import pytest
from skills._template_skill import TemplateSkill, TemplateSkillInput

def test_skill_basic():
    skill = TemplateSkill()
    input_data = TemplateSkillInput(data="test")
    output = skill.execute(input_data)
    
    assert output.result is not None
    assert output.confidence > 0.0

def test_skill_validation():
    skill = TemplateSkill()
    input_data = TemplateSkillInput(data="test")
    assert skill.validate(input_data) == True
```

#### 1.4 第一个真实 Skill: 表格提取
**文件**: `backend/skills/table_extractor.py`

**实现步骤**:
1. 从 `agents/preprocessor.py` 提取 `pdfplumber` 逻辑
2. 创建 Pydantic 输入输出模型
3. 编写单元测试
4. 更新 `engines/parse_engine.py` 调用新 Skill

**预计工时**: 2天

### 验收标准
- [x] 所有规范文档完成
- [ ] 目录结构就绪
- [ ] 模板文件可用
- [ ] 第一个 Skill 实现并测试通过
- [ ] 原有功能零破坏

---

## 🎯 阶段 2: 核心 Skills 实现（Week 2-3）

### 优先级排序

| Skill | 工时 | 依赖 | Week |
|-------|------|------|------|
| 表格提取 | 2天 | 无 | Week 1 ✅ |
| 图像处理 | 1天 | 无 | Week 2 |
| 章节提取 | 3天 | 无 | Week 2 |
| 缓存管理 | 1天 | 无 | Week 2 |
| 文档匹配 | 2天 | 无 | Week 3 |
| OCR 处理 | 2天 | Tesseract | Week 3 |

### 2.1 图像处理 Skill（Week 2, Day 1）

**文件**: `backend/skills/image_processor.py`

**源代码**: `engines/image_extractor.py`

**功能**:
- 从 PDF 提取图像
- 图像压缩
- 格式转换

**接口**:
```python
class ImageProcessorInput(BaseModel):
    pdf_path: str
    output_dir: str
    compress: bool = True
    quality: int = 85

class ImageProcessorOutput(BaseModel):
    images: List[ImageInfo]
    total_count: int
    total_size_mb: float

class ImageProcessorSkill:
    def extract(self, input_data: ImageProcessorInput) -> ImageProcessorOutput:
        """提取图像"""
        pass
```

**测试**:
- 测试 PDF 图像提取
- 测试压缩质量
- 测试多格式支持

**集成**:
- 更新 `routers/images.py`
- 更新 `engines/parse_engine.py`

---

### 2.2 章节提取 Skill（Week 2, Day 2-4）

**文件**: `backend/skills/chapter_extractor.py`

**源代码**: `engines/chapter_content_extractor.py`

**功能**:
- 智能识别章节标题
- 构建章节树
- 提取章节内容

**接口**:
```python
class ChapterExtractorInput(BaseModel):
    text: str
    detect_numbering: bool = True
    min_level: int = 1
    max_level: int = 6

class ChapterNode(BaseModel):
    level: int
    title: str
    content: str
    children: List['ChapterNode'] = []

class ChapterExtractorOutput(BaseModel):
    chapters: List[ChapterNode]
    total_count: int

class ChapterExtractorSkill:
    def extract(self, input_data: ChapterExtractorInput) -> ChapterExtractorOutput:
        """提取章节结构"""
        pass
```

**测试**:
- 测试多种章节编号格式
- 测试嵌套章节
- 测试边界情况

**集成**:
- 更新 `engines/parse_engine.py`
- 为 Logic Checking MCP 提供基础

---

### 2.3 缓存管理 Skill（Week 2, Day 5）

**文件**: `backend/skills/cache_manager.py`

**源代码**: `core/cache.py` (重构)

**功能**:
- Redis 缓存封装
- 键命名规范
- TTL 管理
- 批量操作

**接口**:
```python
class CacheManagerSkill:
    def get(self, key: str) -> Any:
        """获取缓存"""
        pass
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        pass
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取"""
        pass
    
    def invalidate(self, pattern: str):
        """清除缓存"""
        pass
```

**测试**:
- 测试基本读写
- 测试 TTL 过期
- 测试批量操作

---

### 2.4 文档匹配 Skill（Week 3, Day 1-2）

**文件**: `backend/skills/document_matcher.py`

**源代码**: `engines/document_matcher.py`

**功能**:
- 计算文档相似度
- TF-IDF 向量化
- 余弦相似度

**接口**:
```python
class DocumentMatcherInput(BaseModel):
    query_text: str
    candidate_texts: List[str]
    threshold: float = 0.7

class MatchResult(BaseModel):
    index: int
    text: str
    score: float

class DocumentMatcherOutput(BaseModel):
    matches: List[MatchResult]
    best_match: Optional[MatchResult]

class DocumentMatcherSkill:
    def match(self, input_data: DocumentMatcherInput) -> DocumentMatcherOutput:
        """匹配文档"""
        pass
```

**集成**:
- 更新 `engines/smart_router.py`

---

### 2.5 OCR 处理 Skill（Week 3, Day 3-4）

**文件**: `backend/skills/ocr_processor.py`

**源代码**: `engines/ocr_extractor.py`

**依赖**: Tesseract OCR

**功能**:
- 图像文字识别
- 多语言支持
- 结果后处理

**接口**:
```python
class OCRProcessorInput(BaseModel):
    image_path: str
    language: str = "chi_sim+eng"
    preprocess: bool = True

class OCRProcessorOutput(BaseModel):
    text: str
    confidence: float
    words: List[Dict[str, Any]]

class OCRProcessorSkill:
    def recognize(self, input_data: OCRProcessorInput) -> OCRProcessorOutput:
        """识别文字"""
        pass
```

**测试**:
- 测试中英文识别
- 测试低质量图像
- 测试性能

---

### 阶段 2 验收标准
- [ ] 所有 6 个核心 Skill 实现完成
- [ ] 单元测试覆盖率 > 80%
- [ ] 原有引擎成功调用新 Skill
- [ ] 性能基准测试通过
- [ ] 文档完整

---

## 🎯 阶段 3: MCP 服务器完善（Week 4-5）

### 3.1 Logic Checking MCP（Week 4）

**路径**: `mcp-servers/logic-checking/`

**当前状态**: 🟡 部分实现

**完善任务**:

#### Day 1-2: TypeScript 端实现
```typescript
// src/index.ts
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "check_chapter_logic",
      description: "检查章节内部逻辑一致性",
      inputSchema: {
        type: "object",
        properties: {
          chapter_id: { type: "number" },
          check_constraints: { type: "boolean" }
        },
        required: ["chapter_id"]
      }
    },
    {
      name: "validate_constraints",
      description: "验证约束条件",
      inputSchema: {
        type: "object",
        properties: {
          content: { type: "string" },
          constraints: { type: "array", items: { type: "object" } }
        },
        required: ["content", "constraints"]
      }
    }
  ]
}));
```

#### Day 3-4: Python 后端整合
**整合模块**:
- `engines/chapter_logic_engine.py`
- `agents/constraint_extractor.py`
- `skills/chapter_extractor.py` (新)

**Python 后端**: `python/logic_checking_backend.py`
```python
def check_chapter_logic(chapter_id: int, check_constraints: bool = True) -> dict:
    """检查章节逻辑"""
    # 1. 获取章节内容
    # 2. 调用 ChapterLogicEngine
    # 3. 返回检查结果
    pass
```

#### Day 5: 测试与集成
- 编写 MCP 协议测试
- 编写 Python 后端测试
- 集成测试脚本

**测试脚本**: `test/test_integration.sh`
```bash
#!/bin/bash
echo "=== 测试 Logic Checking MCP ==="

# 1. 启动 MCP 服务器
node dist/index.js &
MCP_PID=$!

# 2. 测试 Python 调用
python test/test_mcp.py

# 3. 清理
kill $MCP_PID
```

---

### 3.2 Logic Learning MCP（Week 5）

**路径**: `mcp-servers/logic-learning/`

**当前状态**: 🟡 部分实现

**完善任务**:

#### Day 1-2: 工具定义
```typescript
tools: [
  {
    name: "learn_from_chapter",
    description: "从章节学习逻辑规则",
    inputSchema: {
      type: "object",
      properties: {
        chapter_id: { type: "number" },
        learning_mode: { type: "string", enum: ["incremental", "full"] }
      }
    }
  },
  {
    name: "get_learned_rules",
    description: "获取已学习的规则",
    inputSchema: {
      type: "object",
      properties: {
        category: { type: "string" },
        limit: { type: "number", default: 10 }
      }
    }
  }
]
```

#### Day 3-4: Python 后端
**整合模块**:
- `engines/logic_learning_engine.py`
- `routers/learning.py` (部分逻辑)

**实现增量学习**:
```python
def learn_from_chapter(chapter_id: int, learning_mode: str = "incremental") -> dict:
    """从章节学习"""
    engine = LogicLearningEngine()
    
    if learning_mode == "incremental":
        # 增量学习：仅学习新规则
        result = engine.incremental_learn(chapter_id)
    else:
        # 全量学习：重新学习所有规则
        result = engine.full_learn(chapter_id)
    
    return result
```

#### Day 5: HTTP API 同步
**创建**: `routers/logic_learning_mcp.py`
```python
@router.post("/logic-learning/learn")
async def learn_endpoint(request: LearnRequest):
    """HTTP 端点 - 调用 MCP 后端"""
    from core.mcp_client import get_logic_learning_client
    
    client = get_logic_learning_client()
    result = await client.call_tool("learn_from_chapter", {
        "chapter_id": request.chapter_id,
        "learning_mode": request.mode
    })
    return result
```

---

### 3.3 Expert Advisor MCP（可选，Week 5）

**路径**: `mcp-servers/expert-advisor/` (新建)

**优先级**: 🟡 中

**如果时间充足**:
- 创建目录结构
- 封装 `multi_agent_evaluator.py`
- 实现评审建议工具

**如果时间不足**:
- 推迟到阶段 5（优化阶段）

---

### 阶段 3 验收标准
- [ ] Logic Checking MCP 完全可用
- [ ] Logic Learning MCP 完全可用
- [ ] AI 助手可成功调用
- [ ] HTTP API 同步提供
- [ ] 完整测试套件
- [ ] README 文档更新

---

## 🎯 阶段 4: 测试与文档（Week 6）

### 4.1 集成测试（Day 1-2）

#### 端到端测试
**创建**: `tests/test_e2e_modular.py`
```python
"""
端到端测试：完整业务流程
"""
import pytest

@pytest.mark.e2e
async def test_document_upload_and_parse():
    """测试：上传 → 解析 → 提取章节 → 逻辑检查"""
    # 1. 上传文件
    file_id = await upload_file("test.pdf")
    
    # 2. 解析文件（调用 table_extractor Skill）
    parse_result = await parse_document(file_id)
    assert parse_result["status"] == "success"
    
    # 3. 提取章节（调用 chapter_extractor Skill）
    chapters = await extract_chapters(parse_result["text"])
    assert len(chapters) > 0
    
    # 4. 逻辑检查（调用 Logic Checking MCP）
    check_result = await check_logic(chapters[0]["id"])
    assert check_result["valid"] == True

@pytest.mark.e2e
async def test_logic_learning_flow():
    """测试：学习 → 存储 → 检索"""
    # 1. 从章节学习
    learn_result = await learn_from_chapter(chapter_id=1)
    assert learn_result["rules_learned"] > 0
    
    # 2. 检索学到的规则
    rules = await get_learned_rules(category="constraint")
    assert len(rules) > 0
```

#### 性能基准测试
**创建**: `tests/benchmark_skills.py`
```python
"""
性能基准测试
"""
import pytest
from skills.table_extractor import TableExtractorSkill

@pytest.mark.benchmark
def test_table_extraction_performance(benchmark):
    skill = TableExtractorSkill()
    result = benchmark(skill.extract, "test.pdf")
    
    # 断言：单页 PDF 提取 < 1s
    assert benchmark.stats["mean"] < 1.0
```

---

### 4.2 文档更新（Day 3-4）

#### 更新主 README
**文件**: `README.md`

**新增章节**:
```markdown
## 🏗️ 模块化架构

本项目采用 **MCP 服务器 + 独立技能（Skills）** 的模块化架构。

### 架构概览
- **MCP 服务器**: AI 助手可直接调用的标准化服务
- **独立技能**: 后端引擎调用的纯功能模块
- **统一接口**: 所有模块遵循标准输入输出格式

详见: [MODULAR_ARCHITECTURE.md](./MODULAR_ARCHITECTURE.md)

### 可用的 MCP 服务器
- ✅ document-parser - 文档解析
- ✅ knowledge-base - 知识库管理
- ✅ logic-checking - 逻辑验证
- ✅ logic-learning - 逻辑学习

### 可用的独立技能
- ✅ table_extractor - 表格提取
- ✅ image_processor - 图像处理
- ✅ chapter_extractor - 章节提取
- ✅ cache_manager - 缓存管理
- ✅ document_matcher - 文档匹配
- ✅ ocr_processor - OCR 处理
```

#### 创建新文档
**文件**: `docs/API_STANDARDS.md`
```markdown
# API 接口规范

## Skill 接口规范
...

## MCP 工具规范
...

## HTTP API 规范
...
```

**文件**: `docs/TESTING_GUIDE.md`
```markdown
# 测试指南

## 单元测试
...

## 集成测试
...

## 性能测试
...
```

---

### 4.3 代码质量检查（Day 5）

#### 静态分析
```bash
# 类型检查
mypy backend/skills/ backend/engines/

# 代码风格
black backend/skills/
flake8 backend/skills/ --max-line-length=100

# 安全检查
bandit -r backend/skills/
```

#### 测试覆盖率
```bash
pytest tests/ --cov=backend --cov-report=html --cov-report=term

# 目标：> 80% 覆盖率
```

---

### 阶段 4 验收标准
- [ ] 端到端测试通过
- [ ] 性能基准达标
- [ ] 测试覆盖率 > 80%
- [ ] 所有文档完整
- [ ] 代码质量检查通过
- [ ] 无安全漏洞

---

## 🎯 阶段 5: 优化与推广（Week 7+）

### 5.1 性能优化

#### 缓存优化
- [ ] 热点数据缓存
- [ ] 查询结果缓存
- [ ] MCP 响应缓存

#### 并发优化
- [ ] 异步 I/O
- [ ] 批量处理
- [ ] 连接池

#### 资源优化
- [ ] 内存使用优化
- [ ] MCP 进程复用
- [ ] 数据库索引

---

### 5.2 监控与告警

#### 日志增强
```python
# 为所有 Skill 添加结构化日志
from core.logger import logger

class TableExtractorSkill:
    def extract(self, input_data):
        logger.info("table_extraction_started", extra={
            "file": input_data.pdf_path,
            "skill": "table_extractor"
        })
        
        # ... 执行提取 ...
        
        logger.info("table_extraction_completed", extra={
            "file": input_data.pdf_path,
            "tables_found": len(result.tables),
            "duration_ms": duration
        })
```

#### 性能监控
- [ ] Prometheus 指标导出
- [ ] Grafana 仪表盘
- [ ] 告警规则配置

---

### 5.3 开发者培训

#### 培训材料
- [ ] 录制使用演示视频
- [ ] 编写最佳实践文档
- [ ] 创建示例项目

#### 内部分享
- [ ] 架构设计分享会
- [ ] 代码 Review 会议
- [ ] 问题答疑会

---

### 5.4 社区推广

#### 开源准备
- [ ] 清理敏感信息
- [ ] 许可证选择
- [ ] 贡献指南

#### 文档完善
- [ ] 英文 README
- [ ] 快速开始指南
- [ ] API 参考文档

---

## 📊 进度跟踪

### 完成情况（实时更新）

| 阶段 | 进度 | 状态 | 完成日期 |
|------|------|------|---------|
| **阶段 1: 基础准备** | 60% | 🟡 进行中 | 预计 2025-12-20 |
| **阶段 2: Skills 实现** | 0% | ⏳ 未开始 | 预计 2025-12-27 |
| **阶段 3: MCP 完善** | 0% | ⏳ 未开始 | 预计 2026-01-10 |
| **阶段 4: 测试文档** | 0% | ⏳ 未开始 | 预计 2026-01-17 |
| **阶段 5: 优化推广** | 0% | ⏳ 未开始 | 持续进行 |

### 关键里程碑

- [x] 2025-12-16: 架构设计完成
- [ ] 2025-12-20: 第一个 Skill 上线
- [ ] 2025-12-27: 所有核心 Skills 完成
- [ ] 2026-01-10: MCP 服务器完善
- [ ] 2026-01-17: 测试与文档完成
- [ ] 2026-01-31: 全面上线

---

## ⚠️ 风险管理

### 已识别风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **Skills 提取破坏原有功能** | 🟡 中 | 🔴 高 | 保留旧实现，并行运行，充分测试 |
| **MCP 性能不达标** | 🟡 中 | 🟡 中 | 性能基准测试，优化启动时间 |
| **测试覆盖不足** | 🟢 低 | 🔴 高 | 强制 TDD，自动化 CI/CD |
| **文档不同步** | 🟡 中 | 🟡 中 | 代码审查时检查文档 |
| **团队学习曲线** | 🟡 中 | 🟡 中 | 培训材料，代码示例 |

---

## 🔄 回滚策略

### 如果出现问题

#### Skill 回滚
```python
# 保留旧实现，通过配置切换
USE_NEW_SKILL = os.getenv("USE_TABLE_EXTRACTOR_SKILL", "false") == "true"

if USE_NEW_SKILL:
    from skills.table_extractor import TableExtractorSkill
    extractor = TableExtractorSkill()
else:
    # 旧实现
    from agents.preprocessor import extract_tables_old
    extractor = extract_tables_old
```

#### MCP 回滚
```python
# 如果 MCP 失败，降级到直接调用
try:
    client = get_logic_checking_client()
    result = await client.check_logic(chapter_id)
except Exception as e:
    logger.warning("MCP failed, fallback to direct call", error=str(e))
    # 直接调用 Python 引擎
    from engines.chapter_logic_engine import ChapterLogicEngine
    engine = ChapterLogicEngine()
    result = engine.check(chapter_id)
```

---

## 📝 每周检查清单

### Week 1 Checklist
- [ ] 所有规范文档审查通过
- [ ] 目录结构创建完成
- [ ] 模板文件可用
- [ ] 第一个 Skill 测试通过
- [ ] 原有功能验证通过

### Week 2 Checklist
- [ ] 图像处理 Skill 完成
- [ ] 章节提取 Skill 完成
- [ ] 缓存管理 Skill 完成
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成到引擎成功

### Week 3 Checklist
- [ ] 文档匹配 Skill 完成
- [ ] OCR 处理 Skill 完成
- [ ] 所有 Skills 性能达标
- [ ] 代码审查通过

### Week 4 Checklist
- [ ] Logic Checking MCP TypeScript 端完成
- [ ] Logic Checking MCP Python 端完成
- [ ] 测试套件完整
- [ ] AI 助手可调用

### Week 5 Checklist
- [ ] Logic Learning MCP 完成
- [ ] HTTP API 同步完成
- [ ] MCP 文档更新

### Week 6 Checklist
- [ ] 端到端测试通过
- [ ] 性能基准达标
- [ ] 所有文档更新完成
- [ ] 代码质量检查通过

---

## 🎉 成功标准

### 技术标准
- ✅ 所有 MCP 服务器独立运行
- ✅ 所有 Skills 有独立测试
- ✅ 测试覆盖率 > 80%
- ✅ 性能无回退
- ✅ 原有功能零破坏

### 架构标准
- ✅ 模块职责清晰
- ✅ 接口标准统一
- ✅ 依赖关系简单
- ✅ 易于扩展和替换

### 文档标准
- ✅ 架构文档完整
- ✅ API 文档准确
- ✅ 开发指南可用
- ✅ 示例代码丰富

---

**项目经理**: Copilot  
**技术负责人**: 开发团队  
**审查周期**: 每周五
