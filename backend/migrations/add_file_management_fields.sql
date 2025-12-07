-- 文件管理系统Schema优化
-- 添加状态管理、路径管理、分类信息等字段

-- 1. 添加新字段到uploaded_files表
ALTER TABLE uploaded_files 
    -- 状态管理
    ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'uploaded',
    ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 上传人信息
    ADD COLUMN IF NOT EXISTS uploader VARCHAR(100),
    ADD COLUMN IF NOT EXISTS uploader_id VARCHAR(50),
    
    -- 路径管理
    ADD COLUMN IF NOT EXISTS temp_path TEXT,
    ADD COLUMN IF NOT EXISTS parsed_path TEXT,
    ADD COLUMN IF NOT EXISTS archive_path TEXT,
    
    -- 分类信息
    ADD COLUMN IF NOT EXISTS category VARCHAR(50),
    ADD COLUMN IF NOT EXISTS semantic_filename TEXT,
    ADD COLUMN IF NOT EXISTS is_filename_accurate BOOLEAN DEFAULT false,
    
    -- 元数据
    ADD COLUMN IF NOT EXISTS metadata JSONB,
    
    -- 时间戳
    ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS indexed_at TIMESTAMP,
    
    -- 错误处理
    ADD COLUMN IF NOT EXISTS error_log TEXT,
    ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0,
    
    -- 重复文件处理
    ADD COLUMN IF NOT EXISTS duplicate_action VARCHAR(20),
    ADD COLUMN IF NOT EXISTS original_file_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;

-- 2. 更新created_at为uploaded_at的别名（如果需要）
-- ALTER TABLE uploaded_files RENAME COLUMN created_at TO uploaded_at;

-- 3. 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_file_status ON uploaded_files(status);
CREATE INDEX IF NOT EXISTS idx_file_category ON uploaded_files(category);
CREATE INDEX IF NOT EXISTS idx_file_uploader ON uploaded_files(uploader);
CREATE INDEX IF NOT EXISTS idx_file_sha256 ON uploaded_files(sha256);
CREATE INDEX IF NOT EXISTS idx_file_archived_at ON uploaded_files(archived_at);

-- 4. 元数据JSONB索引（支持高效JSONB查询）
CREATE INDEX IF NOT EXISTS idx_file_metadata ON uploaded_files USING GIN(metadata);

-- 5. 创建文件版本历史表（用于追踪更新）
CREATE TABLE IF NOT EXISTS file_versions (
    id SERIAL PRIMARY KEY,
    file_id VARCHAR(50) NOT NULL,
    version INT NOT NULL,
    filename VARCHAR(255),
    file_path TEXT,
    file_size BIGINT,
    sha256 VARCHAR(64),
    uploader VARCHAR(100),
    action VARCHAR(20),  -- overwrite/update
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    FOREIGN KEY (file_id) REFERENCES uploaded_files(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_version_file_id ON file_versions(file_id);
CREATE INDEX IF NOT EXISTS idx_version_created_at ON file_versions(created_at);

-- 6. 添加注释
COMMENT ON COLUMN uploaded_files.status IS '文件状态: uploaded/parsing/parsed/archiving/archived/indexing/indexed/failed';
COMMENT ON COLUMN uploaded_files.uploader IS '上传人姓名';
COMMENT ON COLUMN uploaded_files.temp_path IS '临时文件路径（上传后）';
COMMENT ON COLUMN uploaded_files.parsed_path IS '解析目录路径';
COMMENT ON COLUMN uploaded_files.archive_path IS '归档文件路径';
COMMENT ON COLUMN uploaded_files.category IS '文档分类: tender/proposal/contract/report/reference/other';
COMMENT ON COLUMN uploaded_files.semantic_filename IS '语义化文件名';
COMMENT ON COLUMN uploaded_files.is_filename_accurate IS '文件名是否准确（影响分析策略）';
COMMENT ON COLUMN uploaded_files.metadata IS '解析的元数据（JSONB格式）';
COMMENT ON COLUMN uploaded_files.duplicate_action IS '重复文件处理动作: overwrite/update/skip';
COMMENT ON COLUMN uploaded_files.original_file_id IS '如果是更新，指向原文件ID';
COMMENT ON COLUMN uploaded_files.version IS '文件版本号';
