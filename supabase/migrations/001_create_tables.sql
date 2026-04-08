-- ============================================================
-- Blog Automation: Supabase Migration
-- Run this SQL on EACH website's Supabase project
-- via the SQL Editor at https://supabase.com/dashboard
-- ============================================================

-- 1. Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector for semantic search
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- trigram for fuzzy text matching

-- 2. Create the posts table
CREATE TABLE IF NOT EXISTS posts (
  id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title           TEXT NOT NULL,
  slug            TEXT UNIQUE NOT NULL,
  content         TEXT NOT NULL,
  keywords        TEXT[] DEFAULT '{}',
  meta_description TEXT,
  status          TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
  embedding       VECTOR(768),            -- nomic-embed-text produces 768-dim vectors
  search_vector   TSVECTOR,               -- full-text search vector
  quality_score   FLOAT DEFAULT 0,        -- content quality metric (0-100)
  word_count      INT DEFAULT 0,
  reading_time    INT DEFAULT 0,          -- estimated minutes
  author          TEXT DEFAULT 'AI Writer',
  sanity_id       TEXT,                   -- reference to Sanity document ID after sync
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Indexes for performance
CREATE INDEX IF NOT EXISTS idx_posts_search_vector 
  ON posts USING GIN(search_vector);

CREATE INDEX IF NOT EXISTS idx_posts_embedding 
  ON posts USING ivfflat(embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_posts_status 
  ON posts(status);

CREATE INDEX IF NOT EXISTS idx_posts_slug 
  ON posts(slug);

CREATE INDEX IF NOT EXISTS idx_posts_created_at 
  ON posts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_posts_keywords 
  ON posts USING GIN(keywords);

-- 4. Auto-update search_vector on insert/update
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := 
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.meta_description, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(array_to_string(NEW.keywords, ' '), '')), 'A');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_search_vector
  BEFORE INSERT OR UPDATE OF title, content, meta_description, keywords
  ON posts
  FOR EACH ROW
  EXECUTE FUNCTION update_search_vector();

-- 5. Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_updated_at
  BEFORE UPDATE ON posts
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- 6. Hybrid search function: combines full-text search + vector similarity
-- Returns posts ranked by a weighted combination of both scores
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding VECTOR(768),
  match_count INT DEFAULT 10,
  fts_weight FLOAT DEFAULT 0.3,
  vector_weight FLOAT DEFAULT 0.7
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  slug TEXT,
  content TEXT,
  meta_description TEXT,
  keywords TEXT[],
  quality_score FLOAT,
  created_at TIMESTAMPTZ,
  fts_rank FLOAT,
  vector_similarity FLOAT,
  combined_score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.title,
    p.slug,
    p.content,
    p.meta_description,
    p.keywords,
    p.quality_score,
    p.created_at,
    ts_rank(p.search_vector, websearch_to_tsquery('english', query_text))::FLOAT AS fts_rank,
    (1 - (p.embedding <=> query_embedding))::FLOAT AS vector_similarity,
    (
      fts_weight * ts_rank(p.search_vector, websearch_to_tsquery('english', query_text)) +
      vector_weight * (1 - (p.embedding <=> query_embedding))
    )::FLOAT AS combined_score
  FROM posts p
  WHERE p.status = 'published'
    AND (
      p.search_vector @@ websearch_to_tsquery('english', query_text)
      OR p.embedding <=> query_embedding < 0.8
    )
  ORDER BY combined_score DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 7. Full-text search only function (for when embeddings aren't available)
CREATE OR REPLACE FUNCTION search_posts_fts(
  query_text TEXT,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  slug TEXT,
  meta_description TEXT,
  keywords TEXT[],
  created_at TIMESTAMPTZ,
  rank FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.title,
    p.slug,
    p.meta_description,
    p.keywords,
    p.created_at,
    ts_rank(p.search_vector, websearch_to_tsquery('english', query_text))::FLOAT AS rank
  FROM posts p
  WHERE p.status = 'published'
    AND p.search_vector @@ websearch_to_tsquery('english', query_text)
  ORDER BY rank DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- 8. Get related posts by keyword overlap + vector similarity
CREATE OR REPLACE FUNCTION get_related_posts(
  post_id UUID,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  slug TEXT,
  meta_description TEXT,
  similarity FLOAT
) AS $$
DECLARE
  post_embedding VECTOR(768);
  post_keywords TEXT[];
BEGIN
  SELECT p.embedding, p.keywords INTO post_embedding, post_keywords
  FROM posts p WHERE p.id = post_id;

  IF post_embedding IS NULL THEN
    -- Fallback to keyword overlap only
    RETURN QUERY
    SELECT p.id, p.title, p.slug, p.meta_description,
      (SELECT COUNT(*)::FLOAT FROM unnest(p.keywords) k WHERE k = ANY(post_keywords)) AS similarity
    FROM posts p
    WHERE p.id != post_id AND p.status = 'published'
      AND p.keywords && post_keywords
    ORDER BY similarity DESC
    LIMIT match_count;
  ELSE
    RETURN QUERY
    SELECT p.id, p.title, p.slug, p.meta_description,
      (1 - (p.embedding <=> post_embedding))::FLOAT AS similarity
    FROM posts p
    WHERE p.id != post_id AND p.status = 'published'
    ORDER BY p.embedding <=> post_embedding
    LIMIT match_count;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- 9. Stats view for the admin dashboard
CREATE OR REPLACE VIEW post_stats AS
SELECT
  COUNT(*) AS total_posts,
  COUNT(*) FILTER (WHERE status = 'published') AS published_posts,
  COUNT(*) FILTER (WHERE status = 'draft') AS draft_posts,
  COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS posts_today,
  COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') AS posts_this_week,
  ROUND(AVG(quality_score)::NUMERIC, 1) AS avg_quality_score,
  ROUND(AVG(word_count)::NUMERIC, 0) AS avg_word_count
FROM posts;

-- 10. Row Level Security (optional but recommended)
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Public can read published posts
CREATE POLICY "Public can read published posts"
  ON posts FOR SELECT
  USING (status = 'published');

-- Service role can do everything (used by blog generator)
CREATE POLICY "Service role full access"
  ON posts FOR ALL
  USING (auth.role() = 'service_role');
