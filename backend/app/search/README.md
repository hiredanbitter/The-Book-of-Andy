# Search Module

API endpoints and business logic for searching podcast transcript chunks.

## Directory Structure

| File | Purpose |
|---|---|
| `__init__.py` | Package marker |
| `router.py` | FastAPI router — defines `GET /search/keyword` and `GET /search/semantic` |
| `schemas.py` | Pydantic models for request/response shapes |
| `service.py` | Business logic — full-text search, semantic search, context retrieval, metadata joins |

## Endpoints

### `GET /search/keyword`

Performs keyword search against `transcript_chunks.chunk_text` using PostgreSQL full-text search (`to_tsvector` / `to_tsquery`).

**Query Parameters**

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | *(required)* | Search term(s) |
| `page` | int | 1 | Page number (1-based) |
| `page_size` | int | 10 | Results per page (max 100) |

**Response Shape**

```json
{
  "results": [
    {
      "chunk_id": "uuid",
      "chunk_text": "...",
      "speaker_label": "SPEAKER_01",
      "start_timestamp": "0:05:00",
      "end_timestamp": "0:05:30",
      "chunk_index": 5,
      "episode_id": "uuid",
      "episode_title": "Episode Title",
      "episode_number": 1,
      "podcast_name": "Podcast Name",
      "publication_date": "2025-01-15",
      "context_before": [ ... ],
      "context_after": [ ... ]
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10
}
```

### `GET /search/semantic`

Performs semantic search by embedding the user's query via the OpenAI Embeddings API and finding the closest matching chunks using pgvector cosine similarity.

**Query Parameters**

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | *(required)* | Natural-language search term(s) |

Pagination is not supported — the endpoint always returns up to 30 results (hard limit).

**Response Shape**

Same as keyword search (see above), with `page` always `1` and `page_size` always `30`.

**Error Responses**

| Status | Condition |
|---|---|
| 503 | OpenAI Embeddings API is unavailable |

## Implementation Notes

- **Full-text search** is handled by a PostgreSQL function (`keyword_search`) called via Supabase RPC. The function performs the text search, joins with `episodes` and `podcasts` for metadata, and returns paginated results with a total count — all in a single database round-trip.
- **Semantic search** embeds the query using the OpenAI Embeddings API (`text-embedding-3-small`) and calls a PostgreSQL function (`semantic_search`) via Supabase RPC that uses pgvector cosine similarity (`<=>` operator) to find the closest matching chunks. Results are hard-limited to 30 (no pagination). If the OpenAI API is unavailable, the endpoint returns a 503.
- **Context chunks** (2 before, 2 after the matching chunk by `chunk_index` within the same episode) are fetched in a separate batch query per episode to keep the RPC functions simple.
- The SQL migration for the `keyword_search` function lives at `backend/migrations/001_keyword_search_function.sql`.
- The SQL migration for the `semantic_search` function lives at `backend/migrations/002_semantic_search_function.sql`.
