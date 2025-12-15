# 统一规则数据库框架 - 快速检查清单

## ✅ 已完成的工作

### 共享框架（三MCP通信契约）
- [x] **rule_schema.py** (79行)
  - Rule Pydantic模型（17个字段）
  - RuleType/RulePriority/RuleSource/RuleSeverity枚举
  - RulePackage集合类
  - MergeResult合并结果类

- [x] **kb_interface.py** (134行)
  - ChapterData/FileMetadata数据模型
  - KBClient异步接口定义
  - KBResponse响应格式

- [x] **report_schema.py** (156行)
  - ViolationType/Severity枚举
  - Violation/CheckResult/CheckReport模型
  - LearningFeedback反馈模型

### 知识库客户端
- [x] **backend/core/kb_client.py** (509行)
  - 8个异步方法完全实现
  - 6个辅助方法（提取、搜索、对比）
  - 全局单例 `get_kb_client()`

**验证方法**:
```bash
cd backend
python -c "from core.kb_client import get_kb_client; kb = get_kb_client(); print(type(kb))"
```

### 统一规则数据库表
- [x] **logic_database** 表已创建
  - 19个字段完整
  - 5个性能索引
  - 3个CHECK约束
  - JSONB支持

**验证方法**:
```bash
docker exec bidding_postgres psql -U postgres -d bidding_db -c "\d logic_database"
```

### 数据访问层
- [x] **backend/core/logic_db.py** (384行)
  - 12个CRUD方法完全实现
  - 自动Row↔Rule转换
  - 全局单例 `logic_db`

**验证方法**:
```bash
cd backend
python -c "from core.logic_db import logic_db; print(type(logic_db))"
```

### 学习MCP改进
- [x] **imports更新** - KB和logic_db导入
- [x] **__init__更新** - 初始化KB和logic_db
- [x] **_run_async方法** - 同步运行异步方法
- [x] **_convert_engine_rule_to_unified_rule方法** - 规则转换
- [x] **_chapter_learning改进** - 规则保存到logic_database
- [x] **_global_learning改进** - 规则保存到logic_database

**验证方法**:
```bash
cd mcp-servers/logic-learning/python
python -c "from logic_learning import LogicLearningMCP; mcp = LogicLearningMCP(); print('Logic DB:', type(mcp.logic_db))"
```

### Git提交
- [x] Commit 1: "Feature: 创建统一的规则数据库与DAL层" (9 files changed, 1832 insertions)
- [x] Commit 2: "Refactor: 统一_global_learning规则保存逻辑到logic_database" (1 file changed, 91 insertions)

---

## 🔄 需要继续的工作

### 第三周：检查MCP重构

**文件**: `mcp-servers/logic-checking/python/logic_checking.py`

**待办任务**:
```
□ 1. 添加导入
    from core.logic_db import logic_db
    from rule_schema import Rule, RuleType, RulePackage
    from core.kb_client import get_kb_client

□ 2. 修改 __init__ 方法
    self.logic_db = logic_db
    self.kb = get_kb_client()

□ 3. 修改规则获取逻辑
    原: 从多个分散的表查询
    新: logic_db.get_rules_by_type() / get_all_rules()

□ 4. 修改规则验证流程
    原: 对比dict格式的规则
    新: 对比Rule对象的属性

□ 5. 测试规则读取是否正确

□ 6. Commit: "Refactor: 检查MCP使用统一规则库"
```

**参考代码**:
```python
# 替换原来的多表查询
mandatory_rules = self.logic_db.get_rules_by_type(RuleType.MANDATORY)
scoring_rules = self.logic_db.get_rules_by_type(RuleType.SCORING)

# 使用统一的规则格式验证
for rule in mandatory_rules:
    # rule.condition, rule.pattern, rule.scope 等字段
    if self._match_rule(content, rule):
        violations.append(...)
```

### 第三周：生成MCP重构

**文件**: `mcp-servers/content-generation/python/content_generation.py`

**待办任务**:
```
□ 1. 添加导入
    from core.logic_db import logic_db
    from rule_schema import Rule, RuleType
    from core.kb_client import get_kb_client

□ 2. 修改 __init__ 方法
    self.logic_db = logic_db
    self.kb = get_kb_client()

□ 3. 修改规则应用逻辑
    原: 从多个表读取规则
    新: logic_db.create_rule_package() / get_rules_by_priority()

□ 4. 修改内容生成流程
    原: 手动验证各种约束
    新: 使用Rule对象的constraints字段

□ 5. 测试生成内容是否符合规则

□ 6. Commit: "Refactor: 生成MCP使用统一规则库"
```

**参考代码**:
```python
# 获取所有相关规则
rule_package = self.logic_db.create_rule_package(rule_type=RuleType.CONTENT)

# 应用规则生成内容
for rule in rule_package.content_rules:
    content = self._apply_rule(content, rule)
    # 检查 rule.constraints 是否满足
    if not self._validate_constraints(content, rule.constraints):
        content = self._fix_constraints(content, rule)
```

### 第四周：集成测试

**待办任务**:
```
□ 1. 单元测试
    - test_rule_conversion.py: 验证Rule转换
    - test_logic_db.py: 验证CRUD操作
    - test_kb_client.py: 验证KB接口

□ 2. 集成测试
    - test_learning_to_checking.py: 学习→检查流程
    - test_learning_to_generation.py: 学习→生成流程
    - test_end_to_end.py: 完整流程

□ 3. 性能测试
    - 规则查询性能
    - 规则转换性能
    - 数据库索引效果

□ 4. 压力测试
    - 1000+规则下的查询
    - 并发访问logic_db
```

---

## 📋 核心文件清单

### 共享框架（3个文件，369行）
```
mcp-servers/shared/
├── __init__.py
├── rule_schema.py           ✅ 79行 - Rule模型定义
├── kb_interface.py          ✅ 134行 - KB接口定义  
└── report_schema.py         ✅ 156行 - 检查报告格式
```

### 后端核心（3个文件，1,302行）
```
backend/core/
├── kb_client.py             ✅ 509行 - 知识库客户端
├── logic_db.py              ✅ 384行 - 规则库DAL
└── ... (其他已有文件)

backend/
└── init_database.sql        ✅ logic_database表已创建
```

### 学习MCP（1个文件，545行）
```
mcp-servers/logic-learning/python/
└── logic_learning.py        ✅ 545行 - 已改进
```

### 待改进MCP（2个文件）
```
mcp-servers/logic-checking/python/
└── logic_checking.py        🔄 需要重构使用logic_db

mcp-servers/content-generation/python/
└── content_generation.py    🔄 需要重构使用logic_db
```

---

## 🔍 验证命令

### 1. 验证文件是否存在
```bash
# 检查共享框架
ls -la mcp-servers/shared/

# 检查后端核心
ls -la backend/core/kb_client.py
ls -la backend/core/logic_db.py

# 检查学习MCP
ls -la mcp-servers/logic-learning/python/logic_learning.py
```

### 2. 验证数据库表
```bash
# 连接PostgreSQL
docker exec -it bidding_postgres psql -U postgres -d bidding_db

# 查看logic_database表结构
\d logic_database

# 查看索引
\d+ logic_database

# 检查是否有数据
SELECT COUNT(*) FROM logic_database;
```

### 3. 验证Python导入
```bash
cd backend

# 测试KB客户端
python -c "
from core.kb_client import get_kb_client
kb = get_kb_client()
print(f'KB Client type: {type(kb)}')
print(f'KB Client methods: {[m for m in dir(kb) if not m.startswith(\"_\")]}')
"

# 测试Logic DB
python -c "
from core.logic_db import logic_db
print(f'Logic DB type: {type(logic_db)}')
print(f'Logic DB methods: {[m for m in dir(logic_db) if not m.startswith(\"_\")]}')
"

# 测试Rule模型
cd ../mcp-servers/logic-learning/python
python -c "
from rule_schema import Rule, RuleType, RulePriority
rule = Rule(
    type=RuleType.MANDATORY,
    priority=RulePriority.HIGH,
    description='Test rule'
)
print(f'Rule created: {rule}')
"
```

### 4. 验证学习MCP改进
```bash
cd mcp-servers/logic-learning/python

python -c "
from logic_learning import LogicLearningMCP
mcp = LogicLearningMCP()
print(f'Logic DB available: {hasattr(mcp, \"logic_db\")}')
print(f'KB available: {hasattr(mcp, \"kb\")}')
print(f'Converter available: {hasattr(mcp, \"_convert_engine_rule_to_unified_rule\")}')
"
```

### 5. 查看Git历史
```bash
git log --oneline -5

# 查看最近的两个commit
git show HEAD
git show HEAD~1

# 查看修改的文件
git diff HEAD~2 HEAD --name-status
```

---

## 💡 使用指南

### 当添加新的学习方法时

1. **遵循规则转换模式**:
   ```python
   # 引擎返回原始规则
   engine_rules = self.some_engine.learn(...)
   
   # 逐一转换并保存
   for engine_rule in engine_rules:
       unified_rule = self._convert_engine_rule_to_unified_rule(
           engine_rule=engine_rule,
           rule_type=RuleType.MANDATORY,  # 根据规则类型
           chapter_id=...  # 如果是章节级
       )
       self.logic_db.add_rule(unified_rule)
   ```

2. **遵循错误处理模式**:
   ```python
   try:
       rule_id = self.logic_db.add_rule(unified_rule)
       logger.info(f"Rule saved: {rule_id}")
   except Exception as e:
       logger.error(f"Failed to save rule: {e}", exc_info=True)
   ```

3. **遵循知识库访问模式**:
   ```python
   # 不要直接db.query()
   # 要使用KB客户端
   chapters = self._run_async(self.kb.get_chapters(file_id))
   metadata = self._run_async(self.kb.get_file_metadata(file_id))
   ```

### 当访问规则时（在检查/生成MCP中）

1. **按类型获取**:
   ```python
   rules = self.logic_db.get_rules_by_type(RuleType.MANDATORY)
   ```

2. **按优先级获取**:
   ```python
   high_priority = self.logic_db.get_rules_by_priority(RulePriority.HIGH)
   ```

3. **按来源获取**:
   ```python
   learned_rules = self.logic_db.get_rules_by_source(RuleSource.CHAPTER_LEARNING)
   ```

4. **搜索特定规则**:
   ```python
   matching = self.logic_db.search_rules("项目名称", RuleType.MANDATORY)
   ```

5. **获取规则包**:
   ```python
   package = self.logic_db.create_rule_package(
       rule_type=RuleType.CONTENT,
       priority=RulePriority.HIGH
   )
   # 返回 RulePackage，包含按类型分类的规则列表
   ```

---

## 📊 进度统计

### 代码完成度
```
共享框架:     ████████████████████ 100% (3/3文件)
后端核心:     ████████████████████ 100% (2/2文件)
学习MCP:      ████████████████████ 100% (1/1文件改进)
检查MCP:      ░░░░░░░░░░░░░░░░░░░░   0% (待改进)
生成MCP:      ░░░░░░░░░░░░░░░░░░░░   0% (待改进)
集成测试:     ░░░░░░░░░░░░░░░░░░░░   0% (待进行)
```

### 里程碑完成度
```
✅ 第一周 - 框架设计和实现
  ✓ Rule Schema设计
  ✓ KB接口设计
  ✓ Report Schema设计

✅ 第一周 - 知识库和数据库
  ✓ KB客户端实现
  ✓ logic_database表创建
  ✓ LogicDatabaseDAL实现

✅ 第二周 - 学习MCP改进
  ✓ 导入和初始化更新
  ✓ _chapter_learning改进
  ✓ _global_learning改进

🟡 第三周 - 检查和生成MCP改进
  □ 检查MCP重构
  □ 生成MCP重构
  □ 端到端测试

🟡 第四周 - 测试和优化
  □ 单元测试套件
  □ 集成测试
  □ 性能优化
```

---

## 🎯 快速开始

### 如果你要继续改进检查MCP

```bash
# 1. 进入检查MCP目录
cd mcp-servers/logic-checking/python

# 2. 打开logic_checking.py
code logic_checking.py

# 3. 按照"检查MCP重构"部分的待办任务执行

# 4. 测试
python -m pytest tests/ -v

# 5. 提交
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system
git add -A
git commit -m "Refactor: 检查MCP使用统一规则库"
```

### 如果你要继续改进生成MCP

```bash
# 1. 进入生成MCP目录
cd mcp-servers/content-generation/python

# 2. 打开content_generation.py
code content_generation.py

# 3. 按照"生成MCP重构"部分的待办任务执行

# 4. 测试
python -m pytest tests/ -v

# 5. 提交
cd /Users/tianmac/vscode/zhaobiao/bidding-intelligence-system
git add -A
git commit -m "Refactor: 生成MCP使用统一规则库"
```

### 如果你要进行测试

```bash
# 1. 创建测试文件
mkdir -p backend/tests/test_rule_db

# 2. 创建测试
cat > backend/tests/test_rule_db/test_logic_db.py << 'EOF'
# 测试代码
EOF

# 3. 运行测试
cd backend
python -m pytest tests/test_rule_db/ -v
```

---

## 📞 常见问题

### Q: 为什么要使用KBClient而不是直接db.query()?
**A**: 
- KBClient提供结构化、异步的接口
- 便于未来扩展（如向量搜索）
- 避免MCP直接访问数据库
- 更容易测试和模拟

### Q: Rule对象如何存储到JSONB字段?
**A**: 
- Rule.dict()序列化为字典
- 字典序列化为JSON字符串
- PostgreSQL将JSON字符串存储为JSONB
- 查询时自动反序列化回Rule对象

### Q: 为什么logic_db是全局单例?
**A**:
- 所有MCP共享同一个数据库连接
- 保证数据一致性
- 避免重复的连接开销
- 便于缓存和性能优化

### Q: 如何添加新的规则类型?
**A**:
1. 在`rule_schema.py`的`RuleType`枚举中添加
2. 在`logic_database`表的CHECK约束中添加
3. 在学习MCP的转换函数中添加处理
4. 在检查/生成MCP中添加验证逻辑

### Q: 如何查询特定的规则?
**A**:
```python
# 按类型查询
rules = logic_db.get_rules_by_type(RuleType.MANDATORY)

# 按优先级查询
high = logic_db.get_rules_by_priority(RulePriority.CRITICAL)

# 搜索关键词
matches = logic_db.search_rules("项目名称", RuleType.MANDATORY)

# 自定义查询（需要扩展DAL）
```

---

## 🚀 下一步建议

1. **立即进行** (下一个工作日):
   - [ ] 验证所有文件和数据库是否正确创建
   - [ ] 测试KB客户端和logic_db的基本功能
   - [ ] 审查学习MCP的改进代码

2. **第三周** (本周继续):
   - [ ] 重构检查MCP
   - [ ] 重构生成MCP
   - [ ] 进行端到端测试

3. **第四周**:
   - [ ] 编写完整的单元测试套件
   - [ ] 性能测试和优化
   - [ ] 准备上线部署

---

**文档最后更新**: 2024年  
**维护者**: AI Agent  
**相关文档**: UNIFIED_RULE_DATABASE_COMPLETION.md
