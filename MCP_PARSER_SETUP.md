# Document Parser MCP 创建总结

**创建时间**: 2025-12-14  
**状态**: ✅ 完成，可测试

---

## 🎯 功能概述

已成功将文档解析功能提取为独立的 **MCP (Model Context Protocol) Server**，提供标准化的文档处理能力。

### 核心功能

1. **文档解析** (`parse_document`)
   - 支持 PDF 和 DOCX 格式
   - 提取完整文本内容
   - 可选章节结构提取
   - 可选图片提取
   - 支持 OCR（扫描文档）

2. **章节提取** (`extract_chapters`)
   - 智能识别章节结构
   - 支持多级标题（1-4级）
   - 自定义正则模式

3. **图片提取** (`extract_images`)
   - 从 PDF/DOCX 提取所有图片
   - 支持多种输出格式（PNG/JPEG）
   - 保留图片元数据

4. **文档信息** (`get_document_info`)
   - 获取文件元数据
   - PDF 页数统计
   - 文件大小、修改时间等

---

## 📁 项目结构

```
mcp-document-parser/
├── package.json              # Node.js 配置
├── tsconfig.json             # TypeScript 配置
├── setup.sh                  # 一键安装脚本
├── mcp-config.example.json   # MCP 配置示例
├── .gitignore
├── README.md                 # 完整文档
│
├── src/
│   └── index.ts              # MCP 服务器（TypeScript）
│                             # - 实现 MCP 协议
│                             # - 定义 4 个工具
│                             # - 调用 Python 后端
│
├── python/
│   └── document_parser.py    # Python 解析后端
│                             # - 复用现有引擎
│                             # - ParseEngine
│                             # - EnhancedChapterExtractor
│                             # - ImageExtractor
│
└── test/
    └── test_parser.py        # 测试套件
                              # - 3 个集成测试
                              # - 使用实际文件测试
```

---

## 🔧 技术架构

### 分层设计

```
┌─────────────────────────────────────────────┐
│  MCP Client (Claude Desktop / VS Code)      │
│  通过 MCP 协议调用工具                       │
└─────────────────┬───────────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────────┐
│  TypeScript MCP Server (src/index.ts)       │
│  - ListTools: 列出 4 个可用工具              │
│  - CallTool: 处理工具调用                    │
│  - 参数验证和错误处理                        │
└─────────────────┬───────────────────────────┘
                  │ exec() Python
┌─────────────────▼───────────────────────────┐
│  Python Backend (python/document_parser.py) │
│  - DocumentParser 类                        │
│  - 4 个核心方法                              │
└─────────────────┬───────────────────────────┘
                  │ Import
┌─────────────────▼───────────────────────────┐
│  Existing Engines (backend/engines/)        │
│  - ParseEngine (PDF/DOCX 解析)              │
│  - EnhancedChapterExtractor (章节提取)      │
│  - ImageExtractor (图片提取)                │
│  - HybridTextExtractor (OCR)                │
└─────────────────────────────────────────────┘
```

### 工具定义

每个工具都遵循 MCP 标准：

```typescript
{
  name: 'parse_document',
  description: '...',
  inputSchema: {
    type: 'object',
    properties: {
      file_path: { type: 'string', description: '...' },
      extract_chapters: { type: 'boolean', default: true },
      // ...
    },
    required: ['file_path']
  }
}
```

---

## 🚀 安装和使用

### 1. 安装

```bash
cd mcp-document-parser
chmod +x setup.sh
./setup.sh
```

这会：
- ✅ 安装 Node.js 依赖
- ✅ 编译 TypeScript
- ✅ 验证 Python 依赖
- ✅ 生成可执行文件

### 2. 配置 MCP 客户端

#### Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "document-parser": {
      "command": "node",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-document-parser/dist/index.js"
      ]
    }
  }
}
```

#### VS Code 配置

在 `.vscode/settings.json` 中：

```json
{
  "mcp.servers": {
    "document-parser": {
      "command": "node",
      "args": ["./mcp-document-parser/dist/index.js"]
    }
  }
}
```

### 3. 测试

#### Python CLI 测试

```bash
# 解析文档
python python/document_parser.py parse /path/to/doc.pdf

# 提取章节
python python/document_parser.py chapters /path/to/doc.pdf

# 提取图片
python python/document_parser.py images /path/to/doc.pdf --output-dir ./output

# 获取信息
python python/document_parser.py info /path/to/doc.pdf
```

#### 集成测试

```bash
python test/test_parser.py
```

#### MCP 客户端测试

在 Claude Desktop 中：

```
请使用 document-parser 工具解析这个文件：/path/to/document.pdf
```

---

## 📊 使用示例

### 示例 1: 解析标书文件

**请求**:
```json
{
  "tool": "parse_document",
  "arguments": {
    "file_path": "/data/tender_2025.pdf",
    "extract_chapters": true,
    "extract_images": false
  }
}
```

**返回**:
```json
{
  "filename": "tender_2025.pdf",
  "content": "完整的文本内容...",
  "content_length": 45678,
  "chapters": [
    {
      "chapter_number": "1",
      "chapter_title": "招标公告",
      "chapter_level": 1,
      "content": "...",
      "position": 1
    },
    {
      "chapter_number": "1.1",
      "chapter_title": "项目概况",
      "chapter_level": 2,
      "content": "...",
      "position": 2
    }
  ],
  "chapter_count": 25,
  "metadata": {
    "size_mb": 3.2,
    "page_count": 50
  }
}
```

### 示例 2: 批量提取章节

**请求**:
```json
{
  "tool": "extract_chapters",
  "arguments": {
    "content": "第一章 总则\n\n1.1 项目背景\n..."
  }
}
```

**返回**:
```json
[
  {
    "chapter_number": "1",
    "chapter_title": "总则",
    "chapter_level": 1,
    "content": "...",
    "position": 1
  },
  {
    "chapter_number": "1.1",
    "chapter_title": "项目背景",
    "chapter_level": 2,
    "content": "...",
    "position": 2
  }
]
```

---

## ✅ 优势

### 1. **独立性**
- 可脱离主系统独立运行
- 通过 MCP 协议标准化访问
- 支持多个客户端同时使用

### 2. **复用性**
- 完全复用现有解析引擎
- 无需重复开发
- 保持功能一致性

### 3. **扩展性**
- 易于添加新工具
- 支持自定义解析规则
- 可集成更多文档格式

### 4. **标准化**
- 遵循 MCP 协议规范
- JSON Schema 参数验证
- 统一的错误处理

---

## 🔄 与主系统的关系

### 共享组件

MCP Server 直接使用主系统的引擎：

```python
# 导入路径
sys.path.insert(0, 'backend/')

# 使用的引擎
from engines.parse_engine import ParseEngine
from engines.parse_engine_v2 import EnhancedChapterExtractor
from engines.image_extractor import ImageExtractor
```

### 独立运行

- ✅ 不需要数据库连接
- ✅ 不需要 Redis
- ✅ 不需要 FastAPI 服务器
- ✅ 只需要文档处理引擎

### 协同工作

可以与主系统并行运行：
- 主系统: FastAPI 服务 (端口 18888)
- MCP Server: stdio/socket 通信
- 两者共享底层引擎代码

---

## 📋 下一步计划

### 可选增强功能

1. **支持更多格式**
   - [ ] PPT/PPTX 解析
   - [ ] Excel 表格解析
   - [ ] TXT/Markdown 解析

2. **高级功能**
   - [ ] 文档对比工具
   - [ ] 内容摘要生成
   - [ ] 关键信息提取

3. **性能优化**
   - [ ] 大文件分块处理
   - [ ] 缓存解析结果
   - [ ] 并行处理多文件

4. **部署选项**
   - [ ] Docker 容器化
   - [ ] HTTP API 模式
   - [ ] WebSocket 支持

---

## 📚 相关文档

- `README.md` - 完整使用文档
- `mcp-config.example.json` - 配置示例
- `test/test_parser.py` - 测试用例
- MCP 官方文档: https://modelcontextprotocol.io

---

## ✅ 完成检查清单

- [x] TypeScript MCP 服务器实现
- [x] Python 解析后端实现
- [x] 4 个核心工具定义
- [x] 参数验证和错误处理
- [x] 复用现有引擎
- [x] 安装脚本
- [x] 测试套件
- [x] 完整文档
- [x] 配置示例
- [x] CLI 接口

**状态**: ✅ 可立即使用

**下一步**: 
1. 运行 `./setup.sh` 安装
2. 运行 `python test/test_parser.py` 测试
3. 添加到 MCP 客户端配置
4. 开始使用！
