-- 财务报告存档表
CREATE TABLE IF NOT EXISTS financial_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    year INTEGER,  -- NULL表示未识别年份
    archive_path TEXT NOT NULL,
    page_count INTEGER NOT NULL,
    file_size BIGINT NOT NULL,
    archived_at TIMESTAMP DEFAULT NOW(),
    
    -- 唯一约束：同一文件的同一年份只能有一条记录
    UNIQUE(file_id, year)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_financial_reports_file_id ON financial_reports(file_id);
CREATE INDEX IF NOT EXISTS idx_financial_reports_year ON financial_reports(year);
CREATE INDEX IF NOT EXISTS idx_financial_reports_archived_at ON financial_reports(archived_at);

-- 注释
COMMENT ON TABLE financial_reports IS '财务报告存档表 - 按年份分离的财务报告';
COMMENT ON COLUMN financial_reports.year IS '报告年份，NULL表示未识别';
COMMENT ON COLUMN financial_reports.archive_path IS '存档文件路径';
COMMENT ON COLUMN financial_reports.page_count IS '页数';
COMMENT ON COLUMN financial_reports.file_size IS '文件大小(字节)';
