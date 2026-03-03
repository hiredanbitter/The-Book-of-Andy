# Episodes Module

This module provides API endpoints for episode-related data, starting with the transcript detail endpoint.

## Key Files

- **`router.py`** — FastAPI router defining the `GET /episodes/{episode_id}/transcript` endpoint. Returns episode metadata and all transcript chunks in chronological order. Returns 404 if the episode does not exist.
- **`service.py`** — Business logic for fetching episode data from Supabase. Queries the `episodes` table (with a join to `podcasts` for the podcast name) and the `transcript_chunks` table ordered by `chunk_index`.
- **`schemas.py`** — Pydantic models for the transcript response:
  - `TranscriptChunk` — a single chunk with text, speaker label, and timestamps
  - `EpisodeMetadata` — episode-level metadata including podcast name
  - `TranscriptResponse` — combines episode metadata with an ordered list of chunks

## Implementation Decisions

- The podcast name is fetched via a Supabase join (`podcasts(name)`) on the `episodes` table rather than a separate query, keeping the database round-trips minimal.
- The service handles both dict and list formats for the Supabase join result, since Supabase can return either depending on the relationship type.
- Chunks are returned in a flat ordered list rather than grouped by speaker, leaving rendering decisions to the frontend.
