# 🚀 Ollama 向量搜索 - 快速启动指南

## 一键安装和测试（5 分钟）

### 步骤 1: 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# 或访问 https://ollama.com 下载安装程序（Windows）
```

### 步骤 2: 启动 Ollama 服务

```bash
# 在新终端窗口运行（保持运行）
ollama serve
```

### 步骤 3: 运行自动化配置

```bash
# 给脚本添加执行权限
chmod +x setup_ollama.sh
chmod +x test_ollama.py

# 运行配置脚本（自动下载模型和配置）
./setup_ollama.sh
```

**该脚本会自动**:
- ✅ 检查 Ollama 安装
- ✅ 验证服务状态
- ✅ 下载 nomic-embed-text 模型（274MB）
- ✅ 测试 embedding 生成
- ✅ 验证 Python 客户端
- ✅ 检查 pgvector 扩展

### 步骤 4: 运行测试套件

```bash
# 运行完整测试
python test_ollama.py
```

**测试内容**:
- ✅ Ollama 连接测试
- ✅ Embedding 生成测试
- ✅ 语义相似度计算
- ✅ 知识库集成验证

### 步骤 5: 启动后端服务

```bash
cd backend
python main.py
```

### 步骤 6: 测试语义搜索 API

```bash
# 语义搜索
curl -X POST http://localhost:8000/api/knowledge/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "项目经理需要什么资质？",
    "limit": 5,
    "min_similarity": 0.7
  }'

# 重建索引（如果有现有数据）
curl -X POST http://localhost:8000/api/knowledge/reindex \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 10}'
```

---

## 常用命令

### Ollama 管理

```bash
# 启动服务
ollama serve

# 列出已安装模型
ollama list

# 下载模型
ollama pull nomic-embed-text

# 测试模型
ollama run nomic-embed-text

# 删除模型
ollama rm nomic-embed-text
```

### API 测试

```bash
# 健康检查
curl http://localhost:8000/api/knowledge/health

# 关键词搜索（旧方法）
curl -X POST http://localhost:8000/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "投标", "limit": 5}'

# 语义搜索（新方法，推荐）
curl -X POST http://localhost:8000/api/knowledge/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "投标要求", "limit": 5}'

# 添加知识条目（自动生成 embedding）
curl -X POST http://localhost:8000/api/knowledge/entries \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "test-001",
    "category": "tender",
    "title": "测试条目",
    "content": "这是一个测试内容",
    "keywords": ["测试"],
    "importance_score": 80
  }'

# 获取统计信息
curl http://localhost:8000/api/knowledge/statistics

# 批量重建索引
curl -X POST http://localhost:8000/api/knowledge/reindex \
  -d '{"batch_size": 10}'
```

---

## 配置说明

### 环境变量（.env）

```bash
# Ollama 配置（已自动配置）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
USE_OLLAMA_FOR_EMBEDDINGS=True
```

### 修改配置

```python
# backend/core/config.py

# 更换 embedding 模型
OLLAMA_EMBEDDING_MODEL: str = "mxbai-embed-large"  # 更高精度

# 调整相似度阈值
# 在 API 调用中设置 min_similarity
# 0.9+ : 几乎相同
# 0.7-0.9 : 高度相关（推荐）
# 0.5-0.7 : 相关
# <0.5 : 弱相关
```

---

## 故障排查

### 问题 1: 连接失败

**错误**: `Failed to connect to http://localhost:11434`

**解决**:
```bash
# 确保 Ollama 正在运行
ollama serve

# 在另一个终端测试
curl http://localhost:11434/api/tags
```

### 问题 2: 模型未找到

**错误**: `model 'nomic-embed-text' not found`

**解决**:
```bash
ollama pull nomic-embed-text
ollama list  # 验证
```

### 问题 3: 向量类型错误

**错误**: `type "vector" does not exist`

**解决**:
```bash
psql -h localhost -U postgres -d bidding_db -c "CREATE EXTENSION vector;"
```

### 问题 4: 搜索无结果

**检查**:
```sql
-- 查看索引状态
SELECT 
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as indexed,
    COUNT(*) FILTER (WHERE embedding IS NULL) as not_indexed
FROM knowledge_base;

-- 如果 indexed = 0，需要重建索引
```

**重建索引**:
```bash
curl -X POST http://localhost:8000/api/knowledge/reindex
```

---

## 性能优化

### 1. GPU 加速（自动）

Ollama 自动检测并使用 GPU:
- macOS: Metal
- Linux: CUDA / ROCm  
- Windows: CUDA

### 2. 批量处理

```bash
# 小内存设备
curl ... -d '{"batch_size": 5}'

# 高性能设备
curl ... -d '{"batch_size": 50}'
```

### 3. 调整阈值

```python
# 高精度（结果少但准确）
min_similarity = 0.85

# 平衡（推荐）
min_similarity = 0.70

# 高召回（结果多但可能不太相关）
min_similarity = 0.50
```

---

## 下一步

1. ✅ **基础功能已完成**
   - Ollama 集成
   - 语义搜索
   - 自动 embedding
   - 批量索引

2. 🔄 **可选增强**（见 `KNOWLEDGE_BASE_ENHANCEMENT_PROPOSAL.md`）
   - AI 智能分类
   - 知识图谱集成
   - 向量聚类分析

3. 🎨 **前端开发**
   - 语义搜索 UI
   - 索引管理面板
   - 相似度可视化

---

## 文档索引

- **完整实施报告**: `OLLAMA_IMPLEMENTATION_COMPLETE.md`
- **使用指南**: `OLLAMA_VECTOR_SEARCH.md`
- **增强方案**: `KNOWLEDGE_BASE_ENHANCEMENT_PROPOSAL.md`
- **MCP 文档**: `KNOWLEDGE_BASE_MCP_COMPLETE.md`

---

## 技术支持

- **测试脚本**: `python test_ollama.py`
- **配置脚本**: `./setup_ollama.sh`
- **日志文件**: `backend/logs/app.log`
- **Ollama 文档**: https://ollama.com/docs

---

**准备就绪！开始使用 Ollama 向量搜索吧！** 🎉
