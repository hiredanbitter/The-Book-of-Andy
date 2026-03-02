-- Migration: Create keyword_search RPC function
-- This function performs full-text search on transcript_chunks.chunk_text,
-- joins with episodes and podcasts for metadata, and returns paginated
-- results with a total count.

CREATE OR REPLACE FUNCTION keyword_search(
    search_query TEXT,
    result_limit INT DEFAULT 10,
    result_offset INT DEFAULT 0
)
RETURNS TABLE (
    chunk_id UUID,
    chunk_text TEXT,
    speaker_label TEXT,
    start_timestamp TEXT,
    end_timestamp TEXT,
    chunk_index INT,
    episode_id UUID,
    episode_title TEXT,
    episode_number INT,
    podcast_name TEXT,
    publication_date DATE,
    total_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH matches AS (
        SELECT
            tc.id AS chunk_id,
            tc.chunk_text,
            tc.speaker_label,
            tc.start_timestamp,
            tc.end_timestamp,
            tc.chunk_index,
            tc.episode_id,
            e.title AS episode_title,
            e.episode_number,
            p.name AS podcast_name,
            e.publication_date,
            COUNT(*) OVER() AS total_count
        FROM transcript_chunks tc
        JOIN episodes e ON tc.episode_id = e.id
        JOIN podcasts p ON e.podcast_id = p.id
        WHERE to_tsvector('english', tc.chunk_text) @@ plainto_tsquery('english', search_query)
        ORDER BY ts_rank(to_tsvector('english', tc.chunk_text), plainto_tsquery('english', search_query)) DESC
        LIMIT result_limit
        OFFSET result_offset
    )
    SELECT * FROM matches;
END;
$$;
