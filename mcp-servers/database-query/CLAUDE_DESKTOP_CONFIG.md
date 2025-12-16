# Claude Desktop 配置说明

## 添加数据库查询MCP到Claude Desktop

编辑 Claude Desktop 配置文件，添加以下内容：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bidding-database": {
      "command": "python3",
      "args": [
        "/Users/tianmac/vscode/zhaobiao/bidding-intelligence-system/mcp-servers/database-query/python/database_query.py"
      ],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5433",
        "DB_NAME": "bidding_db",
        "DB_USER": "postgres",
        "DB_PASSWORD": "postgres123"
      }
    }
  }
}
```

## 重启Claude Desktop

配置后需要完全退出并重启Claude Desktop。

## 使用示例

在Claude Desktop中，你可以使用以下命令：

### 1. 查询文件信息
```
请查询文件ID为 c230a55a-1180-4175-9b1b-46b622123090 的文件信息
```

### 2. 搜索投标文件
```
搜索最近的投标文件（proposal类别）
```

### 3. 获取统计信息
```
显示数据库中的文件统计信息
```

### 4. 列出最近文件
```
列出最近上传的20个文件
```

## 路径说明

- **返回宿主机路径** (`return_host_path=true`): 返回 `/Volumes/ssd/bidding-data/...`，可直接访问
- **返回容器路径** (`return_host_path=false`): 返回 `/app/data/...`，用于容器内部

默认返回宿主机路径，便于外部程序直接访问文件。
