-- 本体知识图谱数据库表结构
-- PostgreSQL轻量级图实现

-- ========== 本体节点表 ==========

CREATE TABLE IF NOT EXISTS ontology_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type TEXT NOT NULL CHECK (
        node_type IN (
            'requirement', 'qualification', 'technical_spec', 
            'price_item', 'evidence', 'scoring_rule', 
            'template', 'constraint', 'strategy'
        )
    ),
    name TEXT NOT NULL,
    description TEXT,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 节点索引
CREATE INDEX IF NOT EXISTS idx_ontology_nodes_type ON ontology_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_ontology_nodes_name ON ontology_nodes(name);
CREATE INDEX IF NOT EXISTS idx_ontology_nodes_properties ON ontology_nodes USING GIN (properties);
CREATE INDEX IF NOT EXISTS idx_ontology_nodes_created ON ontology_nodes(created_at DESC);

-- ========== 本体关系表 ==========

CREATE TABLE IF NOT EXISTS ontology_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_node_id UUID NOT NULL REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    to_node_id UUID NOT NULL REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN (
            'depends_on', 'satisfies', 'requires', 
            'conflicts_with', 'relates_to', 'derived_from', 'validates'
        )
    ),
    properties JSONB DEFAULT '{}',
    weight DECIMAL(3,2) DEFAULT 1.0 CHECK (weight >= 0.0 AND weight <= 1.0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 防止重复关系
    UNIQUE(from_node_id, to_node_id, relation_type)
);

-- 关系索引
CREATE INDEX IF NOT EXISTS idx_ontology_relations_from ON ontology_relations(from_node_id);
CREATE INDEX IF NOT EXISTS idx_ontology_relations_to ON ontology_relations(to_node_id);
CREATE INDEX IF NOT EXISTS idx_ontology_relations_type ON ontology_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_ontology_relations_both ON ontology_relations(from_node_id, to_node_id);
CREATE INDEX IF NOT EXISTS idx_ontology_relations_weight ON ontology_relations(weight DESC);

-- ========== 视图：节点度数统计 ==========

CREATE OR REPLACE VIEW ontology_node_degrees AS
SELECT 
    n.id,
    n.node_type,
    n.name,
    COUNT(DISTINCT CASE WHEN r.from_node_id = n.id THEN r.id END) as out_degree,
    COUNT(DISTINCT CASE WHEN r.to_node_id = n.id THEN r.id END) as in_degree,
    COUNT(DISTINCT r.id) as total_degree
FROM ontology_nodes n
LEFT JOIN ontology_relations r ON (r.from_node_id = n.id OR r.to_node_id = n.id)
GROUP BY n.id, n.node_type, n.name;

-- ========== 视图：关系统计 ==========

CREATE OR REPLACE VIEW ontology_relation_stats AS
SELECT 
    relation_type,
    COUNT(*) as count,
    AVG(weight) as avg_weight,
    MIN(weight) as min_weight,
    MAX(weight) as max_weight
FROM ontology_relations
GROUP BY relation_type
ORDER BY count DESC;

-- ========== 函数：查找最短路径 ==========

CREATE OR REPLACE FUNCTION find_shortest_path(
    start_node UUID,
    end_node UUID,
    max_depth INT DEFAULT 10
)
RETURNS TABLE (
    node_id UUID,
    node_name TEXT,
    node_type TEXT,
    depth INT,
    path UUID[]
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE path_search AS (
        -- 起始节点
        SELECT 
            n.id as node_id,
            n.name as node_name,
            n.node_type,
            0 as depth,
            ARRAY[n.id] as path
        FROM ontology_nodes n
        WHERE n.id = start_node
        
        UNION ALL
        
        -- 递归查找
        SELECT 
            n.id,
            n.name,
            n.node_type,
            ps.depth + 1,
            ps.path || n.id
        FROM ontology_nodes n
        JOIN ontology_relations r ON r.to_node_id = n.id
        JOIN path_search ps ON r.from_node_id = ps.node_id
        WHERE 
            ps.depth < max_depth
            AND NOT (n.id = ANY(ps.path))  -- 避免循环
            AND (ps.node_id != end_node)   -- 找到目标后停止
    )
    SELECT * FROM path_search
    WHERE node_id = end_node
    ORDER BY depth
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ========== 函数：检测循环依赖 ==========

CREATE OR REPLACE FUNCTION detect_circular_dependencies(
    start_node UUID
)
RETURNS TABLE (
    circular_path UUID[],
    path_length INT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE dep_check AS (
        SELECT 
            n.id,
            ARRAY[n.id] as path,
            0 as depth
        FROM ontology_nodes n
        WHERE n.id = start_node
        
        UNION ALL
        
        SELECT 
            n.id,
            dc.path || n.id,
            dc.depth + 1
        FROM ontology_nodes n
        JOIN ontology_relations r ON r.to_node_id = n.id
        JOIN dep_check dc ON r.from_node_id = dc.id
        WHERE 
            r.relation_type IN ('depends_on', 'requires')
            AND dc.depth < 20
    )
    SELECT path, array_length(path, 1) as path_length
    FROM dep_check
    WHERE id = start_node AND depth > 0;  -- 循环回到起点
END;
$$ LANGUAGE plpgsql;

-- ========== 触发器：自动更新updated_at ==========

CREATE OR REPLACE FUNCTION update_ontology_node_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ontology_node_timestamp
    BEFORE UPDATE ON ontology_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_ontology_node_timestamp();

-- ========== 示例数据（可选） ==========

-- 插入示例节点
INSERT INTO ontology_nodes (node_type, name, description, properties) VALUES
('requirement', 'ISO9001认证', '必须具备ISO9001质量管理体系认证', '{"mandatory": true, "category": "资质要求"}'::jsonb),
('evidence', 'ISO9001证书扫描件', '有效期内的ISO9001认证证书', '{"format": "PDF", "required_fields": ["证书编号", "有效期"]}'::jsonb),
('qualification', '类似业绩', '近3年完成的同类项目', '{"min_count": 3, "min_amount": 1000000}'::jsonb)
ON CONFLICT DO NOTHING;

-- 插入示例关系
INSERT INTO ontology_relations (from_node_id, to_node_id, relation_type, weight)
SELECT 
    n1.id,
    n2.id,
    'requires',
    1.0
FROM ontology_nodes n1, ontology_nodes n2
WHERE n1.name = 'ISO9001认证' AND n2.name = 'ISO9001证书扫描件'
ON CONFLICT DO NOTHING;

-- ========== 性能优化 ==========

-- 分析表统计信息
ANALYZE ontology_nodes;
ANALYZE ontology_relations;

-- ========== 完成提示 ==========

SELECT '✅ 本体知识图谱表结构创建完成' as status,
       COUNT(*) as node_count
FROM ontology_nodes;
