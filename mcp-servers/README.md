# MCP Servers

本目录包含项目的所有 **Model Context Protocol (MCP)** 服务器实现。

## 📁 目录结构

```
mcp-servers/
├── README.md              # 本文件
└── document-parser/       # 文档解析 MCP 服务器
    ├── src/               # TypeScript 源码
    ├── python/            # Python 后端
    ├── test/              # 测试套件
    └── README.md          # 详细文档
```

## 🚀 可用的 MCP 服务器

### 1. Document Parser

**路径**: `document-parser/`  
**功能**: 提供文档解析能力（PDF、DOCX）  
**工具数量**: 4 个

#### 核心功能
- ✅ `parse_document` - 完整文档解析（文本 + 章节 + 图片）
- ✅ `extract_chapters` - 智能章节结构提取
- ✅ `extract_images` - 图片提取和保存
- ✅ `get_document_info` - 文档元数据获取

#### 快速启动
```bash
cd document-parser
./setup.sh
```

详细文档: [document-parser/README.md](./document-parser/README.md)

---

## 🔧 通用配置

### Claude Desktop 配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "document-parser": {
      "command": "node",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/document-parser/dist/index.js"
      ]
    }
  }
}
```

### VS Code 配置

在项目根目录的 `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "document-parser": {
      "command": "node",
      "args": ["./mcp-servers/document-parser/dist/index.js"]
    }
  }
}
```

---

## 📚 MCP 协议

所有服务器遵循 [Model Context Protocol](https://modelcontextprotocol.io/) 标准：

- **Transport**: stdio (标准输入/输出)
- **Schema**: JSON Schema 参数验证
- **Tools**: 标准化工具定义
- **Errors**: 统一错误处理

---

## 🛠️ 开发指南

### 添加新 MCP 服务器

1. **创建目录**
   ```bash
   cd mcp-servers
   mkdir my-new-server
   ```

2. **基本结构**
   ```
   my-new-server/
   ├── package.json
   ├── tsconfig.json
   ├── src/
   │   └── index.ts
   ├── python/           # 可选：Python 后端
   │   └── backend.py
   └── README.md
   ```

3. **实现 MCP 协议**
   ```typescript
   import { Server } from '@modelcontextprotocol/sdk/server/index.js';
   import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
   
   const server = new Server({
     name: 'my-server',
     version: '1.0.0'
   }, { capabilities: { tools: {} } });
   
   // 定义工具...
   ```

4. **更新本 README**
   - 添加服务器到列表
   - 更新配置示例

---

## 🧪 测试

### 测试单个服务器
```bash
cd document-parser
python test/test_parser.py
```

### 测试所有服务器
```bash
# 从项目根目录
cd mcp-servers
for dir in */; do
  if [ -d "$dir/test" ]; then
    echo "Testing $dir..."
    cd "$dir" && python test/*.py && cd ..
  fi
done
```

---

## 📖 相关文档

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [主项目 README](../README.md)
- [MCP_PARSER_SETUP.md](../MCP_PARSER_SETUP.md) - Document Parser 设置指南

---

## ⚙️ 技术栈

| 组件 | 技术 |
|------|------|
| **协议** | Model Context Protocol (MCP) |
| **前端** | TypeScript + Node.js |
| **后端** | Python 3.12+ |
| **通信** | stdio / WebSocket |
| **验证** | JSON Schema |

---

**最后更新**: 2025-12-14  
**维护者**: bidding-intelligence-system 团队
