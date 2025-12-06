-- 数据库性能优化脚本
-- 基于深度优化建议添加的索引和配置

-- ========== 性能索引优化 ==========

-- 1. 复合索引：章节+层级（用于层级查询）
CREATE INDEX IF NOT EXISTS idx_chapters_file_level ON chapters(file_id, chapter_level);

-- 2. 向量相似度搜索优化（IVFFlat索引）
CREATE INDEX IF NOT EXISTS idx_vectors_embedding ON vectors 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 3. JSONB字段GIN索引（加速JSON查询）
CREATE INDEX IF NOT EXISTS idx_files_metadata_gin ON files USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_chapters_structure_gin ON chapters USING GIN (structure_data);

-- 4. 逻辑模式表索引
CREATE INDEX IF NOT EXISTS idx_chapter_patterns_chapter ON chapter_logic_patterns(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapter_patterns_type ON chapter_logic_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_chapter_patterns_confidence ON chapter_logic_patterns(confidence DESC);

CREATE INDEX IF NOT EXISTS idx_global_patterns_tender ON global_logic_patterns(tender_id);
CREATE INDEX IF NOT EXISTS idx_global_patterns_type ON global_logic_patterns(pattern_type);

-- 5. 生成记录索引
CREATE INDEX IF NOT EXISTS idx_generation_file_created ON generation_records(source_file_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generation_status ON generation_records(generation_status);

-- 6. 评分记录索引
CREATE INDEX IF NOT EXISTS idx_evaluations_file ON evaluations(file_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_score ON evaluations(total_score DESC);

-- ========== 查询性能优化视图 ==========

-- 文件章节统计视图（避免重复COUNT查询）
CREATE OR REPLACE VIEW file_statistics AS
SELECT 
    f.id,
    f.filename,
    f.doc_type,
    COUNT(c.id) as chapter_count,
    SUM(LENGTH(c.content)) as total_content_length,
    COUNT(DISTINCT clp.id) as pattern_count,
    MAX(c.created_at) as last_chapter_time
FROM files f
LEFT JOIN chapters c ON f.id = c.file_id
LEFT JOIN chapter_logic_patterns clp ON c.id = clp.chapter_id
GROUP BY f.id, f.filename, f.doc_type;

-- 章节逻辑摘要视图
CREATE OR REPLACE VIEW chapter_logic_summary AS
SELECT 
    c.id as chapter_id,
    c.file_id,
    c.chapter_number,
    c.chapter_title,
    COUNT(clp.id) as pattern_count,
    AVG(clp.confidence) as avg_confidence,
    jsonb_agg(DISTINCT clp.pattern_type) as pattern_types
FROM chapters c
LEFT JOIN chapter_logic_patterns clp ON c.id = clp.chapter_id
GROUP BY c.id, c.file_id, c.chapter_number, c.chapter_title;

-- ========== 数据库配置优化 ==========

-- 启用自动vacuum（清理死元组）
ALTER TABLE files SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE chapters SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE vectors SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- ========== 分区表优化（可选，数据量大时启用）==========

-- 示例：按月份分区文件表（数据量>100万时考虑）
-- CREATE TABLE files_y2025m01 PARTITION OF files
-- FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- ========== 性能监控函数 ==========

-- 慢查询分析函数
CREATE OR REPLACE FUNCTION get_slow_queries(min_duration interval DEFAULT '100 milliseconds')
RETURNS TABLE (
    query text,
    calls bigint,
    total_time numeric,
    mean_time numeric,
    max_time numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        SUBSTRING(query, 1, 100) as query,
        calls,
        ROUND((total_exec_time / 1000)::numeric, 2) as total_time,
        ROUND((mean_exec_time / 1000)::numeric, 2) as mean_time,
        ROUND((max_exec_time / 1000)::numeric, 2) as max_time
    FROM pg_stat_statements
    WHERE mean_exec_time > EXTRACT(EPOCH FROM min_duration) * 1000
    ORDER BY total_exec_time DESC
    LIMIT 20;
END;
$$ LANGUAGE plpgsql;

-- 表膨胀检查函数
CREATE OR REPLACE FUNCTION check_table_bloat()
RETURNS TABLE (
    table_name text,
    size_mb numeric,
    dead_tuple_percent numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname || '.' || tablename as table_name,
        ROUND((pg_total_relation_size(schemaname||'.'||tablename) / 1024.0 / 1024.0)::numeric, 2) as size_mb,
        ROUND((n_dead_tup::numeric / NULLIF(n_live_tup + n_dead_tup, 0) * 100)::numeric, 2) as dead_tuple_percent
    FROM pg_stat_user_tables
    WHERE n_dead_tup > 1000
    ORDER BY dead_tuple_percent DESC;
END;
$$ LANGUAGE plpgsql;

-- ========== 使用说明 ==========

COMMENT ON INDEX idx_vectors_embedding IS '向量相似度搜索索引，使用IVFFlat算法加速';
COMMENT ON VIEW file_statistics IS '文件统计视图，避免重复COUNT查询';
COMMENT ON FUNCTION get_slow_queries IS '慢查询分析，默认显示>100ms的查询';
COMMENT ON FUNCTION check_table_bloat IS '检查表膨胀情况，建议定期执行VACUUM';

-- 执行完成提示
SELECT '✅ 数据库性能优化完成' as status,
       '建议定期执行: ANALYZE; VACUUM ANALYZE;' as recommendation;
