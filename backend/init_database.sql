-- 标书智能系统数据库初始化脚本
-- 包含24个核心表结构

-- 1. 启用vector扩展(用于向量存储)
CREATE EXTENSION IF NOT EXISTS vector;

-- ========== 基础表 ==========

-- 2. 文件表
CREATE TABLE IF NOT EXISTS files (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    filename text NOT NULL,
    filepath text NOT NULL,
    filetype text NOT NULL,
    doc_type text NOT NULL CHECK (doc_type IN ('tender', 'proposal', 'reference')),
    content text,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_files_doc_type ON files(doc_type);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at DESC);

-- 3. 章节表
CREATE TABLE IF NOT EXISTS chapters (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id uuid NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    chapter_number text NOT NULL,
    chapter_title text NOT NULL,
    chapter_level int NOT NULL DEFAULT 1,
    content text,
    position_order int NOT NULL,
    structure_data jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chapters_file_id ON chapters(file_id);
CREATE INDEX IF NOT EXISTS idx_chapters_position ON chapters(file_id, position_order);

-- 4. 向量知识库
CREATE TABLE IF NOT EXISTS vectors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id uuid REFERENCES files(id) ON DELETE CASCADE,
    chapter_id uuid REFERENCES chapters(id) ON DELETE CASCADE,
    chunk_type text NOT NULL,
    chunk text NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vectors_file_id ON vectors(file_id);
CREATE INDEX IF NOT EXISTS idx_vectors_chapter_id ON vectors(chapter_id);
CREATE INDEX IF NOT EXISTS idx_vectors_embedding ON vectors 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ========== 章节级逻辑规则表 ==========

-- 5. 章节结构规则
CREATE TABLE IF NOT EXISTS chapter_structure_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    rule_type text NOT NULL,
    rule_content text,
    parameters jsonb DEFAULT '{}',
    priority decimal DEFAULT 1.0,
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chapter_structure_rules_chapter ON chapter_structure_rules(chapter_id);

-- 6. 章节内容规则
CREATE TABLE IF NOT EXISTS chapter_content_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    rule_type text NOT NULL,
    rule_content text,
    keywords jsonb DEFAULT '[]',
    constraints jsonb DEFAULT '{}',
    priority decimal DEFAULT 1.0,
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chapter_content_rules_chapter ON chapter_content_rules(chapter_id);

-- 7. 章节自定义规则
CREATE TABLE IF NOT EXISTS chapter_custom_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    rule_name text NOT NULL,
    rule_type text NOT NULL,
    rule_content text,
    parameters jsonb DEFAULT '{}',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

-- 8. 工程量清单规则
CREATE TABLE IF NOT EXISTS chapter_boq_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    item_code text,
    item_name text NOT NULL,
    unit text,
    quantity decimal,
    unit_price decimal,
    total_price decimal,
    description text,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chapter_boq_rules_chapter ON chapter_boq_rules(chapter_id);

-- 9. 强制要求规则
CREATE TABLE IF NOT EXISTS chapter_mandatory_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    requirement_type text NOT NULL,
    keyword text NOT NULL,
    description text NOT NULL,
    is_negative boolean DEFAULT FALSE,
    priority text DEFAULT 'medium',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chapter_mandatory_rules_chapter ON chapter_mandatory_rules(chapter_id);

-- 10. 章节评分规则
CREATE TABLE IF NOT EXISTS chapter_scoring_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    criterion text NOT NULL,
    max_score decimal NOT NULL,
    description text,
    category text,
    weight decimal DEFAULT 1.0,
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chapter_scoring_rules_chapter ON chapter_scoring_rules(chapter_id);

-- ========== 全局级逻辑规则表 ==========

-- 11. 全局结构规则
CREATE TABLE IF NOT EXISTS global_structure_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_file_id uuid NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    rule_type text NOT NULL,
    rule_content text,
    parameters jsonb DEFAULT '{}',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_global_structure_rules_file ON global_structure_rules(tender_file_id);

-- 12. 全局内容规则
CREATE TABLE IF NOT EXISTS global_content_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_file_id uuid NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    rule_type text NOT NULL,
    rule_content text,
    style_guide jsonb DEFAULT '{}',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_global_content_rules_file ON global_content_rules(tender_file_id);

-- 13. 全局一致性规则
CREATE TABLE IF NOT EXISTS global_consistency_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_file_id uuid NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    rule_type text NOT NULL,
    rule_content text,
    validation_logic jsonb DEFAULT '{}',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_global_consistency_rules_file ON global_consistency_rules(tender_file_id);

-- 14. 全局评分规则
CREATE TABLE IF NOT EXISTS global_scoring_rules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_file_id uuid NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    dimension text NOT NULL,
    weight decimal NOT NULL,
    max_score decimal NOT NULL,
    parameters jsonb DEFAULT '{}',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_global_scoring_rules_file ON global_scoring_rules(tender_file_id);

-- ========== 章节映射表 ==========

-- 15. 章节映射关系
CREATE TABLE IF NOT EXISTS chapter_mappings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    proposal_chapter_id uuid NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    mapping_type text DEFAULT 'direct',
    similarity_score decimal,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chapter_mappings_tender ON chapter_mappings(tender_chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapter_mappings_proposal ON chapter_mappings(proposal_chapter_id);

-- ========== 负面清单与错误库 ==========

-- 16. 负面清单
CREATE TABLE IF NOT EXISTS negative_list (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    error_type text NOT NULL,
    error_pattern text NOT NULL,
    description text,
    severity text DEFAULT 'medium',
    parameters jsonb DEFAULT '{}',
    is_active boolean DEFAULT TRUE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_negative_list_type ON negative_list(error_type);

-- 17. 错误历史记录
CREATE TABLE IF NOT EXISTS error_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id uuid REFERENCES files(id) ON DELETE CASCADE,
    chapter_id uuid REFERENCES chapters(id) ON DELETE CASCADE,
    error_type text NOT NULL,
    error_content text,
    context jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_error_history_file ON error_history(file_id);
CREATE INDEX IF NOT EXISTS idx_error_history_type ON error_history(error_type);

-- ========== 生成与评分 ==========

-- 18. 生成记录
CREATE TABLE IF NOT EXISTS generation_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_file_id uuid NOT NULL REFERENCES files(id),
    generated_file_id uuid REFERENCES files(id),
    mode text NOT NULL,
    parameters jsonb DEFAULT '{}',
    status text DEFAULT 'pending',
    result_summary jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_generation_history_tender ON generation_history(tender_file_id);
CREATE INDEX IF NOT EXISTS idx_generation_history_status ON generation_history(status);

-- 19. 评分记录
CREATE TABLE IF NOT EXISTS scoring_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id uuid NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    score_type text NOT NULL,
    total_score decimal NOT NULL,
    dimension_scores jsonb DEFAULT '{}',
    chapter_scores jsonb DEFAULT '{}',
    details jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scoring_history_file ON scoring_history(file_id);
CREATE INDEX IF NOT EXISTS idx_scoring_history_type ON scoring_history(score_type);

-- 20. 对比分析记录
CREATE TABLE IF NOT EXISTS comparison_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    file_a_id uuid NOT NULL REFERENCES files(id),
    file_b_id uuid NOT NULL REFERENCES files(id),
    comparison_type text NOT NULL,
    result jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comparison_history_files ON comparison_history(file_a_id, file_b_id);

-- ========== 强化学习相关 ==========

-- 21. 训练样本
CREATE TABLE IF NOT EXISTS training_samples (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tender_file_id uuid NOT NULL REFERENCES files(id),
    proposal_file_id uuid NOT NULL REFERENCES files(id),
    ai_score decimal,
    human_score decimal,
    feedback jsonb DEFAULT '{}',
    is_positive boolean,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_training_samples_tender ON training_samples(tender_file_id);
CREATE INDEX IF NOT EXISTS idx_training_samples_is_positive ON training_samples(is_positive);

-- 22. 训练任务
CREATE TABLE IF NOT EXISTS training_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name text NOT NULL,
    target_tender_id uuid REFERENCES files(id),
    config jsonb DEFAULT '{}',
    status text DEFAULT 'pending',
    progress decimal DEFAULT 0,
    result jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    started_at timestamptz,
    completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_training_tasks_status ON training_tasks(status);

-- 23. 逻辑版本管理
CREATE TABLE IF NOT EXISTS logic_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    version_name text NOT NULL,
    tender_file_id uuid REFERENCES files(id),
    version_type text NOT NULL,
    snapshot_data jsonb NOT NULL,
    performance_metrics jsonb DEFAULT '{}',
    is_active boolean DEFAULT FALSE,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_logic_versions_tender ON logic_versions(tender_file_id);
CREATE INDEX IF NOT EXISTS idx_logic_versions_active ON logic_versions(is_active);

-- 24. 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key text NOT NULL UNIQUE,
    config_value jsonb NOT NULL,
    description text,
    updated_at timestamptz DEFAULT now()
);

-- 初始化系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
    ('ai_model', '{"provider": "openai", "model": "gpt-4"}', 'AI模型配置'),
    ('vector_dim', '1536', '向量维度'),
    ('max_file_size', '52428800', '最大文件大小(50MB)')
ON CONFLICT (config_key) DO NOTHING;

-- 成功提示
SELECT 'Database initialization completed successfully!' AS result;
