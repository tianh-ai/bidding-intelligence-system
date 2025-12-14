# MCP 服务器快速参考卡

> **一页搞定 MCP 服务器的所有操作**

---

## 🚀 一键提交到 Git

```bash
# 方法 1: 使用提交脚本（推荐）
./commit_mcp.sh

# 方法 2: 手动提交
git add .
git commit -m "feat(mcp): 添加 MCP 服务器模块化架构"
git push origin main
```

---

## 📁 目录结构

```
mcp-servers/
├── README.md                    # MCP 服务器索引
└── document-parser/             # 文档解析 MCP
    ├── src/index.ts            # TypeScript 服务器
    ├── python/document_parser.py  # Python 后端
    ├── test/test_parser.py     # 测试套件
    ├── package.json            # Node.js 配置
    └── setup.sh                # 一键安装
```

---

## 🔧 快速安装

```bash
cd mcp-servers/document-parser
./setup.sh
```

---

## 🧪 测试

```bash
# Python CLI 测试
cd mcp-servers/document-parser
python python/document_parser.py parse /path/to/doc.pdf

# 集成测试
python test/test_parser.py
```

---

## ⚙️ 配置到 Claude Desktop

**配置文件**: `~/Library/Application Support/Claude/claude_desktop_config.json`

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

**重启 Claude Desktop** 即可使用！

---

## 🛠️ 可用工具

| 工具 | 功能 | 参数 |
|------|------|------|
| `parse_document` | 完整文档解析 | file_path, extract_chapters?, extract_images? |
| `extract_chapters` | 章节提取 | content, patterns? |
| `extract_images` | 图片提取 | file_path, output_dir, format? |
| `get_document_info` | 文档信息 | file_path |

---

## 📚 文档快速链接

| 文档 | 描述 |
|------|------|
| [README.md](README.md) | 项目主文档（包含 MCP 章节） |
| [mcp-servers/README.md](mcp-servers/README.md) | MCP 服务器索引 |
| [MCP_PARSER_SETUP.md](MCP_PARSER_SETUP.md) | 详细设置指南 |
| [GIT_COMMIT_GUIDE_MCP.md](GIT_COMMIT_GUIDE_MCP.md) | Git 提交指南 |
| [MCP_MIGRATION_COMPLETE.md](MCP_MIGRATION_COMPLETE.md) | 迁移完成总结 |

---

## 🔍 常见问题

### Q: MCP 服务器在哪里？
**A**: `mcp-servers/document-parser/`

### Q: 如何安装？
**A**: `cd mcp-servers/document-parser && ./setup.sh`

### Q: 如何测试？
**A**: `python test/test_parser.py`

### Q: 如何在 Claude 中使用？
**A**: 配置 `claude_desktop_config.json` 后重启 Claude

### Q: 提供哪些工具？
**A**: 4个工具 - 文档解析、章节提取、图片提取、信息获取

---

## ✅ 验证清单

- [ ] `mcp-servers/` 目录存在
- [ ] `commit_mcp.sh` 有执行权限
- [ ] 所有关键文件完整
- [ ] Git 状态正常
- [ ] 无敏感文件被追踪

---

## 🎯 快速命令

```bash
# 提交到 Git
./commit_mcp.sh

# 安装 MCP
cd mcp-servers/document-parser && ./setup.sh

# 测试
python test/test_parser.py

# 查看文档
cat mcp-servers/README.md
cat MCP_PARSER_SETUP.md
```

---

**最后更新**: 2025-12-14  
**作者**: GitHub Copilot  
**仓库**: github.com/tianh-ai/bidding-intelligence-system
