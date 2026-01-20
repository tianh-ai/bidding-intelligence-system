# Dev Container 配置

此目录包含用于 GitHub Codespaces 和 VSCode Remote Containers 的开发容器配置。

## 📋 功能特性

### 预装工具
- Python 3.11
- Node.js 18
- Docker-in-Docker
- Git

### 预装扩展
- Python 开发工具（Pylance, Black, Ruff）
- JavaScript/TypeScript 工具（ESLint, Prettier）
- Docker 支持
- GitLens
- GitHub Copilot（需要订阅）

### 自动配置
- 安装 Python 依赖（backend/requirements.txt）
- 安装 Node.js 依赖（frontend/package.json）
- 端口自动转发（18888, 13000, 5433, 6380）
- 格式化和代码检查

## 🚀 使用方法

### 在 GitHub Codespaces 中使用

1. 访问仓库页面
2. 点击 "Code" → "Codespaces" → "Create codespace on main"
3. 等待容器构建完成（首次约 2-3 分钟）
4. 自动安装依赖和配置环境

### 在本地 VSCode 中使用

1. 安装 [Remote - Containers 扩展](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. 打开项目文件夹
3. 按 `F1` → 选择 "Remote-Containers: Reopen in Container"
4. 等待容器构建完成

## ⚙️ 配置说明

### 环境变量

需要在 GitHub Codespaces Secrets 中配置以下变量：

- `OPENAI_API_KEY` - OpenAI API 密钥
- `DEEPSEEK_API_KEY` - DeepSeek API 密钥（可选）
- `DB_PASSWORD` - 数据库密码
- `REDIS_PASSWORD` - Redis 密码（可选）

### 端口映射

| 端口 | 服务 | 说明 |
|------|------|------|
| 18888 | Backend API | FastAPI 后端服务 |
| 13000 | Frontend | React 前端应用 |
| 5433 | PostgreSQL | 数据库 |
| 6380 | Redis | 缓存和任务队列 |

### 资源要求

- **最低**: 2 核 CPU, 8GB 内存
- **推荐**: 4 核 CPU, 16GB 内存
- **存储**: 32GB

## 🛠️ 自定义配置

### 修改 Python 版本

编辑 `devcontainer.json`:
```json
"features": {
  "ghcr.io/devcontainers/features/python:1": {
    "version": "3.12"
  }
}
```

### 添加更多扩展

在 `customizations.vscode.extensions` 中添加扩展 ID:
```json
"extensions": [
  "ms-python.python",
  "your-extension-id-here"
]
```

### 修改启动命令

更改 `postCreateCommand` 或 `postStartCommand`:
```json
"postCreateCommand": "pip install -r backend/requirements.txt",
"postStartCommand": "docker-compose up -d"
```

## 📝 注意事项

1. **Docker-in-Docker**: 启用后可在容器内使用 Docker，但会增加资源消耗
2. **自动保存**: 已启用 `formatOnSave`，保存时自动格式化代码
3. **端口转发**: 公开端口会有安全提示，请确保不暴露敏感信息
4. **Codespace 暂停**: 30 分钟无活动后自动暂停，恢复时环境保留

## 🔧 故障排除

### 容器构建失败
- 检查 Docker 守护进程是否运行
- 查看构建日志找出错误原因
- 尝试重建容器: `F1` → "Remote-Containers: Rebuild Container"

### 依赖安装失败
- 手动运行安装命令: `pip install -r backend/requirements.txt`
- 检查网络连接
- 清除缓存重试

### 端口无法访问
- 确认服务正在运行: `docker-compose ps`
- 检查端口转发状态: VSCode "端口" 面板
- 重启服务: `docker-compose restart`

## 📚 相关文档

- [VSCode Dev Containers 文档](https://code.visualstudio.com/docs/devcontainers/containers)
- [GitHub Codespaces 文档](https://docs.github.com/en/codespaces)
- [开发容器规范](https://containers.dev/)
- [项目 iPad 使用指南](../VSCODE_IPAD_GUIDE.md)
