# 标书智能系统 - 后端

投标文件智能生成与分析系统的后端服务,基于FastAPI框架。

## 核心功能

- **文件解析**: 支持PDF和Word文档的上传与解析
- **章节分割**: 自动识别文档结构并分割章节
- **逻辑学习**: 
  - 章节级逻辑学习(结构、内容、工程量清单、强制要求、评分规则)
  - 全局级逻辑学习(整体结构、内容风格、一致性约束、评分权重)
- **智能生成**: 基于学习的逻辑生成投标文件(待实现)
- **自动评分**: 多维度评分系统(待实现)
- **对比分析**: 文件差异分析(待实现)

## 技术栈

- **框架**: FastAPI 0.115.0
- **数据库**: PostgreSQL + pgvector扩展
- **文档解析**: pypdf, python-docx
- **数据验证**: Pydantic

## 目录结构

```
backend/
├── database/           # 数据库连接模块
│   ├── __init__.py
│   └── connection.py   # 连接管理类
├── engines/            # 核心引擎
│   ├── __init__.py
│   ├── parse_engine.py          # 文档解析引擎
│   ├── chapter_logic_engine.py  # 章节逻辑学习引擎
│   └── global_logic_engine.py   # 全局逻辑学习引擎
├── routers/            # API路由
│   ├── __init__.py
│   ├── files.py        # 文件管理路由
│   └── learning.py     # 逻辑学习路由
├── main.py             # 主程序入口
├── requirements.txt    # 依赖包
├── init_database.sql   # 数据库初始化脚本
└── .env.example        # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件,配置数据库连接等信息
```

### 3. 初始化数据库

确保Supabase已启动,然后执行:

```bash
psql -h localhost -p 5432 -U postgres -d postgres -f init_database.sql
```

或通过Supabase Studio执行SQL:
- 访问 http://localhost:8000
- 进入SQL Editor
- 粘贴 init_database.sql 内容并执行

### 4. 启动服务

```bash
python main.py
```

服务将在 http://localhost:8000 启动。

### 5. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API接口

### 文件管理

- `POST /api/files/upload` - 上传并解析文件
- `GET /api/files/list` - 获取文件列表
- `GET /api/files/{file_id}` - 获取文件详情
- `GET /api/files/{file_id}/chapters` - 获取文件章节
- `GET /api/files/chapter/{chapter_id}` - 获取章节详情
- `DELETE /api/files/{file_id}` - 删除文件

### 逻辑学习

- `POST /api/learning/chapter/learn` - 学习章节对
- `GET /api/learning/chapter/{chapter_id}/rules` - 获取章节规则
- `POST /api/learning/global/learn` - 学习文件对(全局)
- `GET /api/learning/global/{tender_id}/rules` - 获取全局规则

## 数据库表结构

系统包含24个核心表:

### 基础表
- `files` - 文件表
- `chapters` - 章节表
- `vectors` - 向量知识库

### 章节级规则表(6个)
- `chapter_structure_rules` - 结构规则
- `chapter_content_rules` - 内容规则
- `chapter_custom_rules` - 自定义规则
- `chapter_boq_rules` - 工程量清单规则
- `chapter_mandatory_rules` - 强制要求规则
- `chapter_scoring_rules` - 评分规则

### 全局级规则表(4个)
- `global_structure_rules` - 全局结构规则
- `global_content_rules` - 全局内容规则
- `global_consistency_rules` - 一致性规则
- `global_scoring_rules` - 全局评分规则

### 其他表
- `chapter_mappings` - 章节映射
- `negative_list` - 负面清单
- `error_history` - 错误历史
- `generation_history` - 生成记录
- `scoring_history` - 评分记录
- `comparison_history` - 对比记录
- `training_samples` - 训练样本
- `training_tasks` - 训练任务
- `logic_versions` - 逻辑版本
- `system_config` - 系统配置

## 开发说明

### 添加新引擎

1. 在 `engines/` 目录创建新引擎文件
2. 在 `engines/__init__.py` 中导出
3. 在对应路由中使用

### 添加新路由

1. 在 `routers/` 目录创建新路由文件
2. 在 `routers/__init__.py` 中导出
3. 在 `main.py` 中注册路由

## 待实现功能

- [ ] 逻辑融合引擎
- [ ] 生成引擎
- [ ] 评分引擎
- [ ] 对比分析引擎
- [ ] 错误库管理
- [ ] 强化学习循环
- [ ] AI模型集成
- [ ] 向量化与相似度搜索

## License

MIT
