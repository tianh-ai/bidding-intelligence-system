# 知识库 MCP 增强方案

## 📋 现状分析

### ✅ 已有基础设施

| 组件 | 状态 | 位置 |
|------|------|------|
| **OpenAI 配置** | ✅ 已配置 | `backend/core/config.py` |
| **向量数据库** | ✅ 已启用 | PostgreSQL + pgvector |
| **知识图谱** | ✅ 已实现 | `backend/db/ontology.py` |
| **Embedding 字段** | ✅ 已创建 | `knowledge_base.embedding VECTOR(1536)` |

### ❌ 缺少的核心功能

| 功能 | 当前状态 | 问题 |
|------|---------|------|
| **向量搜索** | ❌ 未使用 | 只有 LIKE 模糊匹配，无语义搜索 |
| **知识图谱集成** | ❌ 未关联 | ontology 与 knowledge_base 分离 |
| **AI 增强** | ❌ 未实现 | 无自动分类、关键词提取、摘要生成 |

---

## 🎯 建议增强方案

### 方案 1: AI 向量搜索（高优先级）⭐️⭐️⭐️⭐️⭐️

#### 功能描述
使用 OpenAI Embeddings 实现语义搜索，替代简单的 LIKE 匹配。

#### 实现内容
```python
# 1. 添加到 knowledge_base.py
def search_knowledge_semantic(self, query: str, category=None, limit=10):
    """语义向量搜索"""
    # 生成查询向量
    query_embedding = openai.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    ).data[0].embedding
    
    # 向量相似度搜索（余弦距离）
    results = self.db.query("""
        SELECT 
            id, title, content, category,
            1 - (embedding <=> %s::vector) as similarity
        FROM knowledge_base
        WHERE embedding IS NOT NULL
            AND (category = %s OR %s IS NULL)
            AND 1 - (embedding <=> %s::vector) > 0.7
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (query_embedding, category, category, 
          query_embedding, query_embedding, limit))
    
    return results

# 2. 自动生成 embedding
def add_knowledge_entry(self, ..., auto_embed=True):
    """添加时自动生成向量"""
    if auto_embed:
        embedding = openai.embeddings.create(
            input=f"{title}\n{content}",
            model="text-embedding-3-small"
        ).data[0].embedding
    
    self.db.execute("""
        INSERT INTO knowledge_base (...)
        VALUES (..., %s)
    """, (..., embedding))
```

#### 优势
- ✅ 语义理解（"投标资质" = "投标人资格要求"）
- ✅ 跨语言搜索
- ✅ 模糊概念匹配
- ✅ 准确率提升 30-50%

#### 新增 MCP 工具
- `search_knowledge_semantic` - 语义搜索
- `reindex_embeddings` - 批量重建向量索引

---

### 方案 2: 知识图谱混合架构（中优先级）⭐️⭐️⭐️⭐️

#### 功能描述
将 `knowledge_base` 表与 `ontology` 知识图谱关联，实现结构化 + 非结构化混合存储。

#### 实现内容

##### 2.1 数据库架构扩展
```sql
-- 添加知识条目与本体节点的关联表
CREATE TABLE knowledge_ontology_mapping (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_id UUID REFERENCES knowledge_base(id) ON DELETE CASCADE,
    ontology_node_id UUID REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    relation_type TEXT CHECK (relation_type IN (
        'describes',      -- 描述
        'supports',       -- 支持
        'contradicts',    -- 矛盾
        'explains'        -- 解释
    )),
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(knowledge_id, ontology_node_id, relation_type)
);

-- 索引优化
CREATE INDEX idx_ko_mapping_knowledge ON knowledge_ontology_mapping(knowledge_id);
CREATE INDEX idx_ko_mapping_ontology ON knowledge_ontology_mapping(ontology_node_id);
```

##### 2.2 混合查询能力
```python
def search_with_graph_context(self, query: str, depth=2):
    """
    混合搜索：向量搜索 + 图谱扩展
    
    流程：
    1. 向量搜索找到相关知识条目
    2. 通过关联表找到本体节点
    3. 图遍历扩展相关节点（2层深度）
    4. 返回知识条目 + 关联的图谱结构
    """
    # 1. 向量搜索
    knowledge_results = self.search_knowledge_semantic(query, limit=5)
    
    # 2. 获取关联的本体节点
    knowledge_ids = [r['id'] for r in knowledge_results]
    ontology_nodes = self.db.query("""
        SELECT DISTINCT on.id, on.node_type, on.name
        FROM ontology_nodes on
        JOIN knowledge_ontology_mapping kom ON kom.ontology_node_id = on.id
        WHERE kom.knowledge_id = ANY(%s)
    """, (knowledge_ids,))
    
    # 3. 图遍历扩展（递归 CTE）
    expanded_graph = self.db.query("""
        WITH RECURSIVE graph_expansion AS (
            -- 起始节点
            SELECT id, node_type, name, 0 as depth
            FROM ontology_nodes
            WHERE id = ANY(%s)
            
            UNION ALL
            
            -- 递归扩展
            SELECT n.id, n.node_type, n.name, ge.depth + 1
            FROM ontology_nodes n
            JOIN ontology_relations r ON r.to_node_id = n.id
            JOIN graph_expansion ge ON r.from_node_id = ge.id
            WHERE ge.depth < %s
        )
        SELECT * FROM graph_expansion
    """, ([n['id'] for n in ontology_nodes], depth))
    
    return {
        "knowledge_entries": knowledge_results,
        "ontology_context": ontology_nodes,
        "expanded_graph": expanded_graph
    }
```

#### 优势
- ✅ 结构化知识 + 非结构化文本
- ✅ 关系推理能力（A 依赖 B，B 依赖 C → A 间接依赖 C）
- ✅ 冲突检测（发现矛盾的知识条目）
- ✅ 知识网络可视化

#### 新增 MCP 工具
- `search_with_graph` - 图谱增强搜索
- `link_to_ontology` - 将知识条目关联到本体节点
- `detect_conflicts` - 检测知识冲突
- `visualize_graph` - 生成知识图谱可视化数据

---

### 方案 3: AI 智能增强（中优先级）⭐️⭐️⭐️

#### 功能描述
使用 LLM 自动增强知识条目：分类、关键词提取、摘要生成、实体识别。

#### 实现内容
```python
def enhance_knowledge_with_ai(self, knowledge_id: str):
    """
    AI 智能增强知识条目
    
    功能：
    1. 自动分类
    2. 关键词提取
    3. 摘要生成
    4. 实体识别（人名、机构、技术规格等）
    5. 情感分析（重要性评分）
    """
    # 获取原始内容
    entry = self.get_knowledge_entry(knowledge_id)
    
    # 调用 OpenAI 进行增强
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{
            "role": "system",
            "content": """你是知识库智能增强助手。分析给定的知识条目，提取：
1. category: 分类（tender/proposal/reference）
2. keywords: 5-10个关键词
3. summary: 100字摘要
4. entities: 实体列表 {type: "person/org/spec", value: "..."}
5. importance_score: 重要性评分 0-100
6. suggested_tags: 建议标签

以 JSON 格式返回。"""
        }, {
            "role": "user",
            "content": f"标题: {entry['title']}\n内容: {entry['content']}"
        }],
        response_format={"type": "json_object"}
    )
    
    # 解析并更新
    enhancements = json.loads(response.choices[0].message.content)
    
    self.db.execute("""
        UPDATE knowledge_base
        SET 
            category = %s,
            keywords = %s,
            importance_score = %s,
            metadata = metadata || %s::jsonb
        WHERE id = %s
    """, (
        enhancements['category'],
        json.dumps(enhancements['keywords']),
        enhancements['importance_score'],
        json.dumps({
            'summary': enhancements['summary'],
            'entities': enhancements['entities'],
            'tags': enhancements['suggested_tags']
        }),
        knowledge_id
    ))
    
    return enhancements
```

#### 优势
- ✅ 减少手动标注工作量
- ✅ 提高分类准确性
- ✅ 自动发现关键信息
- ✅ 一致性更好

#### 新增 MCP 工具
- `enhance_knowledge_ai` - AI 增强单个条目
- `batch_enhance` - 批量增强
- `extract_entities` - 实体识别
- `generate_summary` - 自动摘要

---

## 📊 三种方案对比

| 方案 | 优先级 | 实现难度 | 效果提升 | 依赖 AI | 备注 |
|------|-------|---------|---------|---------|------|
| **向量搜索** | ⭐️⭐️⭐️⭐️⭐️ | 低 | 高 | 是 | **强烈推荐优先实现** |
| **知识图谱** | ⭐️⭐️⭐️⭐️ | 中 | 中 | 否 | 适合复杂关系场景 |
| **AI 增强** | ⭐️⭐️⭐️ | 低 | 中 | 是 | 减少人工工作 |

---

## 🛠️ 推荐实施顺序

### 阶段 1: 向量搜索（立即实施）
```bash
# 1-2 小时可完成
1. 添加 search_knowledge_semantic() 方法
2. 修改 add_knowledge_entry() 自动生成 embedding
3. 添加 MCP 工具定义
4. 更新 TypeScript 路由
5. 测试验证
```

### 阶段 2: AI 智能增强（1-2 天）
```bash
1. 实现 enhance_knowledge_with_ai() 方法
2. 添加批量处理能力
3. 创建后台任务（Celery）
4. 前端展示增强结果
```

### 阶段 3: 知识图谱集成（3-5 天）
```bash
1. 创建 knowledge_ontology_mapping 表
2. 实现混合搜索
3. 添加图谱可视化接口
4. 冲突检测算法
```

---

## 💡 使用场景示例

### 场景 1: 智能搜索
```python
# 用户输入: "项目经理需要什么资质？"

# 当前实现（LIKE 匹配）：
results = search_knowledge("项目经理", "tender")
# 只能匹配包含"项目经理"文本的条目

# 增强后（向量搜索）：
results = search_knowledge_semantic("项目经理需要什么资质？")
# 可以找到：
# - "项目负责人资格要求"（语义相似）
# - "建造师执业资格证书"（关联概念）
# - "项目管理经验证明"（相关内容）
```

### 场景 2: 知识网络
```python
# 查询: "投标保证金"

# 增强后（图谱搜索）：
results = search_with_graph_context("投标保证金", depth=2)

# 返回结构：
{
  "knowledge_entries": [
    {"title": "投标保证金缴纳要求", "content": "..."}
  ],
  "ontology_context": [
    {"type": "requirement", "name": "投标保证金"},
    {"type": "price_item", "name": "保证金金额"},
    {"type": "constraint", "name": "缴纳时限"}
  ],
  "relationships": [
    {"from": "投标保证金", "to": "保证金金额", "type": "requires"},
    {"from": "投标保证金", "to": "缴纳时限", "type": "depends_on"}
  ]
}

# 可视化：
投标保证金 → requires → 保证金金额（项目总价2%）
          ↓ depends_on
        缴纳时限（投标截止前24小时）
```

### 场景 3: 自动增强
```python
# 添加原始知识条目
entry_id = add_knowledge_entry(
    title="资质要求",
    content="投标人须具有建筑工程施工总承包一级及以上资质..."
)

# 自动 AI 增强
enhancements = enhance_knowledge_with_ai(entry_id)

# 结果：
{
  "category": "tender",  # 自动分类
  "keywords": ["资质", "建筑工程", "施工总承包", "一级"],
  "summary": "投标人需持有建筑工程施工总承包一级或以上资质证书",
  "entities": [
    {"type": "qualification", "value": "建筑工程施工总承包一级"},
  ],
  "importance_score": 92,  # 高重要性
  "suggested_tags": ["资质要求", "总承包", "准入门槛"]
}
```

---

## 🚦 决策建议

### 立即实施（今天）
✅ **方案 1: 向量搜索**
- 投入产出比最高
- 实现简单（1-2小时）
- 效果显著（准确率+30-50%）

### 短期规划（本周）
⏳ **方案 3: AI 智能增强**
- 减少手动标注
- 提升数据质量
- 为图谱集成做准备

### 中期规划（下周）
📅 **方案 2: 知识图谱集成**
- 复杂度最高
- 需要前端可视化支持
- 适合已有大量知识条目后实施

---

## ❓ 需要您的决策

请告诉我：

1. **是否实施向量搜索？**（强烈推荐 ✅）
   - [ ] 是，立即实施
   - [ ] 否，暂缓

2. **是否需要知识图谱集成？**
   - [ ] 是，完整实施
   - [ ] 是，但简化版
   - [ ] 否，暂不需要

3. **是否需要 AI 智能增强？**
   - [ ] 是，全部功能
   - [ ] 是，仅自动分类和关键词
   - [ ] 否，手动管理即可

4. **OpenAI API Key 配置？**
   - [ ] 已配置在 .env 文件
   - [ ] 需要我提供配置指导
   - [ ] 使用其他 LLM（请说明）

---

**我的建议**: 先实施向量搜索（方案 1），立竿见影。知识图谱和 AI 增强可以后续迭代添加。
