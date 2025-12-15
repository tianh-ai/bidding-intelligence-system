# Logic Learning MCP Server

逻辑学习 MCP 服务器，为标书智能系统提供章节级和全局级学习功能。

## 架构

```
logic-learning/
├── src/index.ts          # Node.js MCP Server (stdio JSON-RPC)
├── python/logic_learning.py  # Python 逻辑学习实现
├── package.json          # Node.js 依赖
├── tsconfig.json         # TypeScript 配置
└── setup.sh             # 安装和构建脚本
```

## 功能

### 工具列表

1. **start_learning** - 启动学习任务
   - 输入：
     - `file_ids`: 文件ID列表
     - `learning_type`: 学习类型 (chapter/global)
     - `chapter_ids`: 章节ID列表（章节级学习时必填）
   - 输出：`{task_id, status, message}`

2. **get_learning_status** - 查询学习任务状态
   - 输入：`task_id`
   - 输出：`{task_id, status, progress, message, result}`

3. **get_learning_result** - 获取学习任务结果
   - 输入：`task_id`
   - 输出：完整学习结果

4. **get_logic_database** - 获取逻辑数据库统计
   - 输入：`category` (可选)
   - 输出：`{total_rules, category_stats, recent_rules}`

## 安装

```bash
bash setup.sh
```

## 测试

```bash
# 列出工具
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | node dist/index.js

# 启动学习任务
echo '{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "start_learning",
    "arguments": {
      "file_ids": ["file1"],
      "learning_type": "global"
    }
  }
}' | node dist/index.js
```

## 集成

后端通过 `backend/core/mcp_client.py` 的 `LogicLearningMCPClient` 调用此服务。

```python
from core.mcp_client import get_logic_learning_client

client = get_logic_learning_client()
result = await client.start_learning(
    file_ids=["file1"],
    learning_type="global"
)
```

## 学习算法

### 章节级学习
- 提取章节结构规则
- 提取内容匹配规则
- 提取评分标准
- 识别必要条件

### 全局级学习
- 分析文档整体结构
- 提取全局一致性规则
- 识别跨章节依赖
- 生成全局评分模型

## 数据库

学习结果存储在 `logic_database` 表：
- `rule_type`: 规则类型 (chapter/global)
- `condition_text`: 条件描述
- `scoring_logic`: 评分逻辑 (JSON)
- `importance`: 重要性分数 (0-100)
- `confidence`: 置信度 (0.0-1.0)
- `category`: 分类标签

## 日志

- Node.js: 使用 `console.error` 输出到 stderr
- Python: 使用 `backend/core/logger.py` 统一日志

## 开发

```bash
# 开发模式（自动编译）
npm run watch

# 手动编译
npm run build
```
