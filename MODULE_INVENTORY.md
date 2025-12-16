# 📦 功能模块清单

> **目的**: 梳理所有现有功能模块，分类并标注迁移策略  
> **更新日期**: 2025-12-16

---

## 📊 统计概览

| 类别 | 数量 | 状态 |
|------|------|------|
| **已实现 MCP** | 2 | ✅ 可用 |
| **待完善 MCP** | 2 | 🟡 进行中 |
| **计划新增 MCP** | 3 | 🆕 未开始 |
| **适合 Skill** | 8 | 🎯 待创建 |
| **保持现状** | 15+ | ✋ 不迁移 |

---

## 1️⃣ 已实现的 MCP 服务器 ✅

### 1.1 Document Parser
**路径**: `mcp-servers/document-parser/`  
**状态**: ✅ 已完成并测试  
**功能**: 文档解析（PDF、DOCX）

#### 提供的工具
- `parse_document` - 完整文档解析
- `extract_chapters` - 章节提取
- `extract_images` - 图片提取
- `get_document_info` - 元数据获取

#### 调用方式
```typescript
// AI 助手（Claude Desktop）
在 Claude 中：请解析这个 PDF 文件
```

```bash
# 命令行测试
cd mcp-servers/document-parser
node dist/index.js
```

#### 依赖的 Python 模块
- `engines/parse_engine.py`
- `agents/preprocessor.py`

---

### 1.2 Knowledge Base
**路径**: `mcp-servers/knowledge-base/`  
**状态**: ✅ 已完成并集成  
**功能**: 知识库检索和管理

#### 提供的工具
- `search_knowledge` - 搜索知识
- `add_knowledge` - 添加知识
- `get_statistics` - 统计信息
- `search_by_category` - 分类搜索

#### 调用方式（混合模式）

**方式 1: AI 助手调用（MCP）**
```typescript
在 Claude 中：搜索知识库中关于"投标资质"的内容
```

**方式 2: HTTP API 调用**
```bash
curl -X POST http://localhost:18888/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "投标", "category": "tender"}'
```

**方式 3: Python SDK 调用**
```python
from core.mcp_client import get_knowledge_base_client

client = get_knowledge_base_client()
results = await client.search_knowledge("投标要求")
```

#### 依赖的 Python 模块
- `routers/knowledge.py`
- `core/mcp_client.py`
- `db/` (PostgreSQL)

---

## 2️⃣ 待完善的 MCP 服务器 🟡

### 2.1 Logic Checking
**路径**: `mcp-servers/logic-checking/`  
**状态**: 🟡 部分实现  
**功能**: 逻辑一致性验证

#### 当前问题
- [ ] TypeScript 端未完整实现
- [ ] 缺少测试套件
- [ ] Python 后端分散在多个文件

#### 计划工具
- `check_chapter_logic` - 检查章节逻辑
- `validate_constraints` - 验证约束
- `find_inconsistencies` - 发现不一致

#### 需要整合的模块
- `engines/chapter_logic_engine.py`
- `agents/constraint_extractor.py`

#### 优先级
🔴 高 - 核心功能，需要尽快完善

---

### 2.2 Logic Learning
**路径**: `mcp-servers/logic-learning/`  
**状态**: 🟡 部分实现  
**功能**: 逻辑规则学习

#### 当前问题
- [ ] 学习流程未标准化
- [ ] 缺少增量学习支持
- [ ] 结果存储方式不统一

#### 计划工具
- `learn_from_chapter` - 从章节学习
- `learn_global_rules` - 学习全局规则
- `get_learned_rules` - 获取已学习规则
- `update_rules` - 更新规则

#### 需要整合的模块
- `engines/logic_learning_engine.py`
- `routers/learning.py`

#### 优先级
🔴 高 - 核心功能

---

## 3️⃣ 计划新增的 MCP 服务器 🆕

### 3.1 Expert Advisor
**路径**: `mcp-servers/expert-advisor/` (待创建)  
**功能**: 专家系统评审建议

#### 计划工具
- `evaluate_content` - 评估内容质量
- `suggest_improvements` - 提供改进建议
- `check_compliance` - 合规性检查

#### 需要封装的模块
- `engines/multi_agent_evaluator.py`
- `engines/scoring_engine.py`

#### 优先级
🟡 中 - 可选增强功能

---

### 3.2 Document Classifier
**路径**: `mcp-servers/document-classifier/` (待创建)  
**功能**: 智能文档分类

#### 计划工具
- `classify_document` - 分类文档
- `detect_document_type` - 检测文档类型
- `extract_metadata` - 提取元数据

#### 需要封装的模块
- `engines/smart_document_classifier.py`
- `engines/document_classifier.py`

#### 优先级
🟢 低 - 辅助功能

---

### 3.3 Content Generator
**路径**: `mcp-servers/content-generator/` (待创建)  
**功能**: 智能内容生成

#### 计划工具
- `generate_content` - 生成内容
- `adapt_template` - 适配模板
- `rewrite_section` - 重写章节

#### 需要封装的模块
- `engines/intelligent_generator.py`
- `engines/generation_engine.py`

#### 优先级
🟡 中 - 核心生成功能

---

## 4️⃣ 适合作为 Skill 的功能 🎯

### 4.1 表格提取 Skill
**新文件**: `backend/skills/table_extractor.py`  
**当前实现**: `agents/preprocessor.py` (部分)  
**功能**: 使用 pdfplumber 提取表格

#### 接口设计
```python
class TableExtractorSkill:
    def extract(self, pdf_path: str) -> List[Table]:
        """提取 PDF 中的所有表格"""
        pass
```

#### 调用者
- `engines/parse_engine.py`
- `engines/parse_engine_v2.py`

#### 优先级
🔴 高 - 核心功能，多处使用

---

### 4.2 OCR 处理 Skill
**新文件**: `backend/skills/ocr_processor.py`  
**当前实现**: `engines/ocr_extractor.py`  
**功能**: 图像文字识别

#### 接口设计
```python
class OCRProcessorSkill:
    def recognize(self, image_path: str) -> str:
        """识别图像中的文字"""
        pass
```

#### 依赖
- Tesseract OCR
- PIL/Pillow

#### 优先级
🟡 中 - 增强功能

---

### 4.3 图像处理 Skill
**新文件**: `backend/skills/image_processor.py`  
**当前实现**: `engines/image_extractor.py`  
**功能**: 图像提取、压缩、转换

#### 接口设计
```python
class ImageProcessorSkill:
    def extract(self, pdf_path: str, output_dir: str) -> List[Image]:
        """提取 PDF 中的图像"""
        pass
    
    def compress(self, image_path: str, quality: int = 85) -> str:
        """压缩图像"""
        pass
```

#### 调用者
- `routers/images.py`
- `engines/parse_engine.py`

#### 优先级
🔴 高 - 已有 API 使用

---

### 4.4 格式转换 Skill
**新文件**: `backend/skills/format_converter.py`  
**当前实现**: 分散在多个文件  
**功能**: PDF/DOCX/TXT 格式转换

#### 接口设计
```python
class FormatConverterSkill:
    def to_pdf(self, source_path: str) -> str:
        """转换为 PDF"""
        pass
    
    def to_docx(self, source_path: str) -> str:
        """转换为 DOCX"""
        pass
    
    def to_text(self, source_path: str) -> str:
        """提取纯文本"""
        pass
```

#### 依赖
- `python-docx`
- `pypdf`

#### 优先级
🟢 低 - 辅助功能

---

### 4.5 缓存管理 Skill
**新文件**: `backend/skills/cache_manager.py`  
**当前实现**: `core/cache.py`  
**功能**: Redis 缓存封装

#### 接口设计
```python
class CacheManagerSkill:
    def get(self, key: str) -> Any:
        """获取缓存"""
        pass
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        pass
    
    def invalidate(self, pattern: str):
        """清除缓存"""
        pass
```

#### 调用者
- `engines/smart_router.py`
- 所有需要缓存的引擎

#### 优先级
🟡 中 - 性能优化

---

### 4.6 章节提取 Skill
**新文件**: `backend/skills/chapter_extractor.py`  
**当前实现**: `engines/chapter_content_extractor.py`  
**功能**: 智能章节结构提取

#### 接口设计
```python
class ChapterExtractorSkill:
    def extract(self, text: str) -> List[Chapter]:
        """提取章节结构"""
        pass
```

#### 优先级
🔴 高 - 核心功能

---

### 4.7 财务报告分割 Skill
**新文件**: `backend/skills/financial_splitter.py`  
**当前实现**: `engines/financial_report_splitter.py`  
**功能**: 财务报告智能分割

#### 接口设计
```python
class FinancialSplitterSkill:
    def split(self, pdf_path: str) -> List[FinancialSection]:
        """分割财务报告"""
        pass
```

#### 优先级
🟢 低 - 专项功能

---

### 4.8 文档匹配 Skill
**新文件**: `backend/skills/document_matcher.py`  
**当前实现**: `engines/document_matcher.py`  
**功能**: 文档相似度匹配

#### 接口设计
```python
class DocumentMatcherSkill:
    def match(self, doc1: str, doc2: str) -> float:
        """计算文档相似度"""
        pass
```

#### 优先级
🟡 中 - 智能路由使用

---

## 5️⃣ 保持现状的模块 ✋

### 5.1 HTTP 路由层
**位置**: `backend/routers/`

| 文件 | 功能 | 原因 |
|------|------|------|
| `files.py` | 文件上传管理 | FastAPI 标准实现 |
| `learning.py` | 学习接口 | 与前端紧耦合 |
| `generation.py` | 生成接口 | 业务流程编排 |
| `auth.py` | 认证授权 | 安全关键 |
| `metrics.py` | 统计指标 | 数据聚合 |

**决策**: ✋ 不迁移，保持 FastAPI 路由

---

### 5.2 数据库层
**位置**: `backend/db/`

| 文件 | 功能 |
|------|------|
| `ontology.py` | 本体知识图谱 |
| `database.py` | 数据库连接 |
| `models.py` | ORM 模型 |

**决策**: ✋ 不迁移，保持 SQLAlchemy

---

### 5.3 核心基础设施
**位置**: `backend/core/`

| 文件 | 功能 | 决策 |
|------|------|------|
| `config.py` | 配置管理 | ✋ 已标准化 |
| `logger.py` | 日志系统 | ✋ 已标准化 |
| `cache.py` | 缓存装饰器 | 🎯 → Skill |
| `mcp_client.py` | MCP 客户端 | ✋ 保持 |

---

### 5.4 任务队列
**位置**: `backend/`

| 文件 | 功能 |
|------|------|
| `tasks.py` | Celery 任务定义 |
| `worker.py` | Celery Worker |

**决策**: ✋ 不迁移，保持 Celery

---

### 5.5 前端
**位置**: `frontend/`

**决策**: ✋ 完全不迁移，独立 React 应用

---

## 6️⃣ 迁移优先级矩阵

| 模块 | 类型 | 优先级 | 难度 | 预计工时 | 依赖 |
|------|------|-------|------|---------|------|
| **表格提取 Skill** | Skill | 🔴 高 | 低 | 2天 | 无 |
| **图像处理 Skill** | Skill | 🔴 高 | 低 | 1天 | 无 |
| **章节提取 Skill** | Skill | 🔴 高 | 中 | 3天 | 无 |
| **Logic Checking MCP** | MCP | 🔴 高 | 中 | 5天 | 章节提取 |
| **Logic Learning MCP** | MCP | 🔴 高 | 中 | 5天 | Logic Checking |
| **缓存管理 Skill** | Skill | 🟡 中 | 低 | 1天 | 无 |
| **文档匹配 Skill** | Skill | 🟡 中 | 中 | 2天 | 无 |
| **Expert Advisor MCP** | MCP | 🟡 中 | 高 | 7天 | 多个引擎 |
| **Content Generator MCP** | MCP | 🟡 中 | 高 | 7天 | 多个引擎 |
| **OCR 处理 Skill** | Skill | 🟡 中 | 低 | 2天 | Tesseract |
| **格式转换 Skill** | Skill | 🟢 低 | 低 | 1天 | 无 |
| **财务分割 Skill** | Skill | 🟢 低 | 中 | 3天 | 无 |
| **Document Classifier MCP** | MCP | 🟢 低 | 中 | 4天 | 分类引擎 |

---

## 7️⃣ 迁移风险评估

### 高风险模块 ⚠️

| 模块 | 风险 | 缓解措施 |
|------|------|---------|
| **Logic Checking** | 逻辑复杂，多处调用 | 充分测试，保留旧实现 |
| **章节提取** | 核心解析功能 | 并行实现，对比验证 |
| **Expert Advisor** | 多代理系统 | 分阶段迁移 |

### 中风险模块 🟡

| 模块 | 风险 | 缓解措施 |
|------|------|---------|
| **表格提取** | 准确率依赖 pdfplumber | 保持算法不变 |
| **缓存管理** | 性能关键 | 基准测试对比 |

### 低风险模块 ✅

- 格式转换
- OCR 处理
- 财务分割
- 文档分类

---

## 8️⃣ 依赖关系图

```
┌─────────────────────────────────────────┐
│          HTTP 路由层（保持）              │
│  files.py, learning.py, generation.py   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         MCP 服务器（新增/完善）           │
│  logic-checking, logic-learning,        │
│  expert-advisor, content-generator      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         业务引擎层（保持）                │
│  smart_router, parse_engine,            │
│  generation_engine, scoring_engine      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         独立技能层（新增）                │
│  table_extractor, image_processor,      │
│  chapter_extractor, cache_manager       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         基础设施（保持）                  │
│  config, logger, database, redis        │
└─────────────────────────────────────────┘
```

---

## 9️⃣ 验收标准

### 每个 MCP 服务器
- [ ] 独立运行无错误
- [ ] AI 助手可成功调用
- [ ] HTTP API 同步提供（如适用）
- [ ] 完整的测试套件
- [ ] README 文档

### 每个 Skill
- [ ] 独立测试通过
- [ ] 单元测试覆盖率 > 80%
- [ ] 性能无回退
- [ ] 调用者已更新

### 整体系统
- [ ] 端到端测试通过
- [ ] 所有受保护文件功能正常
- [ ] 性能基准无下降
- [ ] 文档完整更新

---

## 🔟 下一步行动

### 立即执行（本周）
1. ✅ 创建 `MODULAR_ARCHITECTURE.md`
2. ✅ 创建 `MODULE_INVENTORY.md`（本文件）
3. [ ] 创建 `backend/skills/` 目录
4. [ ] 实现第一个 Skill: `table_extractor.py`
5. [ ] 编写 Skill 测试模板

### 近期计划（2周内）
1. [ ] 完善 Logic Checking MCP
2. [ ] 完善 Logic Learning MCP
3. [ ] 实现图像处理 Skill
4. [ ] 实现章节提取 Skill

### 中期目标（1个月内）
1. [ ] 所有高优先级 Skill 完成
2. [ ] 核心 MCP 服务器稳定
3. [ ] 完整测试覆盖
4. [ ] 性能基准建立

---

**维护**: 与代码同步更新  
**审查**: 每个迁移完成后更新状态
