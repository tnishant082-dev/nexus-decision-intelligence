-- Optional pgvector schema (not applied locally; DuckDB is the default store).
-- Use when you run Postgres with the pgvector extension.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS nexus_knowledge_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    title TEXT,
    body TEXT NOT NULL,
    metadata JSONB,
    embedding vector(384)
);

CREATE INDEX IF NOT EXISTS nexus_knowledge_chunks_embedding_idx
    ON nexus_knowledge_chunks USING ivfflat (embedding vector_cosine_ops);
