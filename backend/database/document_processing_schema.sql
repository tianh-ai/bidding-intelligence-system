-- =====================================================
-- 文档处理系统数据库表
-- =====================================================

-- 1. 文档分类结果表
CREATE TABLE IF NOT EXISTS document_classifications (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES uploaded_files(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL,
    processing_strategy VARCHAR(50) NOT NULL,
    total_pages INTEGER NOT NULL,
    text_page_ratio FLOAT NOT NULL DEFAULT 0.0,
    scan_page_ratio FLOAT NOT NULL DEFAULT 0.0,
    image_page_ratio FLOAT NOT NULL DEFAULT 0.0,
    is_certificate BOOLEAN DEFAULT FALSE,
    is_financial_report BOOLEAN DEFAULT FALSE,
    detected_years INTEGER[],
    classification_confidence FLOAT DEFAULT 0.0,
    classification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_doc_classifications_file_id ON document_classifications(file_id);
CREATE INDEX idx_doc_classifications_file_type ON document_classifications(file_type);
CREATE INDEX idx_doc_classifications_strategy ON document_classifications(processing_strategy);

-- 2. 提取结果表（存储文本提取的元数据）
CREATE TABLE IF NOT EXISTS extraction_results (
    id SERIAL PRIMARY KEY,
    document_classification_id INTEGER NOT NULL REFERENCES document_classifications(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    extraction_method VARCHAR(20) NOT NULL,  -- 'direct' or 'ocr'
    text_length INTEGER NOT NULL,
    confidence_score FLOAT DEFAULT 0.0,
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_extraction_results_classification_id ON extraction_results(document_classification_id);
CREATE INDEX idx_extraction_results_method ON extraction_results(extraction_method);

-- 3. TOC 学习规则表（用于后续的自学习）
CREATE TABLE IF NOT EXISTS toc_extraction_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(50) NOT NULL,  -- 'chapter_title_pattern', 'attachment_pattern', 'subsection_pattern'
    pattern VARCHAR(500) NOT NULL,
    description VARCHAR(500),
    confidence_score FLOAT DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_toc_rules_type ON toc_extraction_rules(rule_type);
CREATE INDEX idx_toc_rules_confidence ON toc_extraction_rules(confidence_score);

-- 4. LLM 验证日志表
CREATE TABLE IF NOT EXISTS llm_validation_logs (
    id SERIAL PRIMARY KEY,
    document_classification_id INTEGER NOT NULL REFERENCES document_classifications(id) ON DELETE CASCADE,
    validation_type VARCHAR(50) NOT NULL,  -- 'toc_validation', 'content_validation', 'semantic_check'
    input_text TEXT NOT NULL,
    llm_response TEXT NOT NULL,
    validation_score FLOAT DEFAULT 0.0,
    violations JSON,
    recommendations JSON,
    model_name VARCHAR(100) DEFAULT 'gpt-4-turbo',
    tokens_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_llm_validation_logs_classification_id ON llm_validation_logs(document_classification_id);
CREATE INDEX idx_llm_validation_logs_type ON llm_validation_logs(validation_type);

-- 5. 多源可靠性统计表
CREATE TABLE IF NOT EXISTS source_reliability_stats (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,  -- 'direct_text', 'ocr', 'pdf_outline', 'llm_validation'
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0.0,
    total_processed INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name)
);

-- 6. 用户纠正反馈表（用于学习系统改进）
CREATE TABLE IF NOT EXISTS extraction_corrections (
    id SERIAL PRIMARY KEY,
    document_classification_id INTEGER NOT NULL REFERENCES document_classifications(id) ON DELETE CASCADE,
    extracted_item VARCHAR(500) NOT NULL,
    corrected_item VARCHAR(500) NOT NULL,
    correction_type VARCHAR(50) NOT NULL,  -- 'false_positive', 'false_negative', 'title_correction'
    error_description VARCHAR(500),
    rule_id_that_failed INTEGER REFERENCES toc_extraction_rules(id),
    correction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_extraction_corrections_classification_id ON extraction_corrections(document_classification_id);
CREATE INDEX idx_extraction_corrections_type ON extraction_corrections(correction_type);

-- 7. 处理性能统计表
CREATE TABLE IF NOT EXISTS processing_performance (
    id SERIAL PRIMARY KEY,
    document_classification_id INTEGER NOT NULL REFERENCES document_classifications(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL,
    total_pages INTEGER NOT NULL,
    classification_time_ms INTEGER DEFAULT 0,
    extraction_time_ms INTEGER DEFAULT 0,
    validation_time_ms INTEGER DEFAULT 0,
    total_time_ms INTEGER DEFAULT 0,
    memory_peak_mb FLOAT DEFAULT 0.0,
    cpu_avg_percent FLOAT DEFAULT 0.0,
    processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_processing_performance_classification_id ON processing_performance(document_classification_id);
CREATE INDEX idx_processing_performance_file_type ON processing_performance(file_type);

-- =====================================================
-- 数据导入脚本
-- =====================================================

-- 初始化 TOC 提取规则
INSERT INTO toc_extraction_rules (rule_type, pattern, description, confidence_score) VALUES
-- 章节标题模式
('chapter_title_pattern', '^(第)?[一二三四五六七八九十百千万]+[、、]{1}', '中文数字+顿号开头的章节标题', 0.85),
('chapter_title_pattern', '^\d+[\.．、]{1}', '数字+点号的章节标题', 0.80),
('chapter_title_pattern', '^\d+\.\d+', '多级数字编号', 0.75),

-- 附件模式
('attachment_pattern', '^附件\d+', '附件标记', 0.95),
('attachment_pattern', '^(附|表|图|清单)\d+', '附属材料标记', 0.90),

-- 小节模式
('subsection_pattern', '^\s+\([一二三四五]\)', '括号编号的小节', 0.70),
('subsection_pattern', '^\s+[①②③④⑤⑥⑦⑧⑨⑩]', '圆圈编号的小节', 0.70);

-- 初始化多源可靠性统计
INSERT INTO source_reliability_stats (source_name, success_count, failure_count, avg_confidence) VALUES
('direct_text', 0, 0, 0.95),
('ocr', 0, 0, 0.75),
('pdf_outline', 0, 0, 0.98),
('llm_validation', 0, 0, 0.85)
ON CONFLICT (source_name) DO NOTHING;

-- =====================================================
-- 查询示例
-- =====================================================

-- 获取最近分类的文档
-- SELECT dc.id, f.filename, dc.file_type, dc.total_pages, dc.text_page_ratio, dc.classification_timestamp
-- FROM document_classifications dc
-- JOIN uploaded_files f ON dc.file_id = f.id
-- ORDER BY dc.created_at DESC LIMIT 10;

-- 查看 OCR 页面率
-- SELECT file_type, AVG(scan_page_ratio) as avg_scan_ratio, AVG(text_page_ratio) as avg_text_ratio
-- FROM document_classifications
-- GROUP BY file_type;

-- 查看提取方法统计
-- SELECT extraction_method, COUNT(*) as count, AVG(confidence_score) as avg_confidence
-- FROM extraction_results
-- GROUP BY extraction_method;

-- 获取用户纠正信息
-- SELECT correction_type, COUNT(*) as count
-- FROM extraction_corrections
-- GROUP BY correction_type;

-- 查看处理性能
-- SELECT file_type, AVG(total_time_ms) as avg_time_ms, MAX(total_time_ms) as max_time_ms
-- FROM processing_performance
-- GROUP BY file_type
-- ORDER BY avg_time_ms DESC;
