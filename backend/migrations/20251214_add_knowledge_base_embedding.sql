-- Adds embedding support to existing knowledge_base table.
-- This is required for /api/knowledge/search/semantic and /api/knowledge/reindex.
--
-- Notes:
-- - pgvector 的 ivfflat/hnsw 索引需要列有固定维度，否则会报错："column does not have dimensions"。
-- - 当前后端默认 Ollama embedding 模型是 `mxbai-embed-large`（常见为 1024 维），因此这里使用 vector(1024)。
-- - 如果你切换 embedding 模型且维度不同，需要同步修改为对应维度（例如 vector(768)）。

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE IF EXISTS knowledge_base
  ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- Optional: index to speed up vector search (requires pgvector).
-- If you later choose a fixed dimension and large datasets, ivfflat lists may need tuning.
CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding
  ON knowledge_base
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

COMMIT;
