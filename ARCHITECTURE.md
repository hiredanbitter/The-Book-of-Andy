# Architecture

This document describes the overall architecture of the Podcast Transcript Search App, including each component, how they connect, and the data flow from transcript ingestion through to search results.

## System Overview

```
┌─────────────┐       ┌─────────────────┐       ┌──────────────────────┐
│   React     │◄─────►│  FastAPI         │◄─────►│  Supabase            │
│   Frontend  │  API  │  Backend         │  DB   │  (PostgreSQL +       │
│   (Vite)    │       │                  │       │   pgvector + Storage │
└─────────────┘       └────────┬─────────┘       │   + Auth)            │
                               │                 └──────────────────────┘
                               │
                       ┌───────▼─────────┐
                       │  OpenAI         │
                       │  Embeddings API │
                       └─────────────────┘
```

## Components

### React Frontend (Vite + TypeScript)

The user-facing single-page application. Provides:

- **Search interface** — A homepage with a search bar and keyword/semantic toggle. Users can search transcripts and view paginated results.
- **Transcript detail page** — Displays a full episode transcript with speaker labels, timestamps, and highlights for matched chunks.
- **Bookmarks dashboard** — Logged-in users can save, view, and manage bookmarked transcript chunks.
- **Authentication** — Google OAuth sign-in/sign-out via Supabase Auth, with session persistence.

Deployed to **Vercel**.

### FastAPI Backend (Python)

The API layer that sits between the frontend and data stores. Provides:

- **Keyword search** (`GET /search/keyword`) — Full-text search against transcript chunks using PostgreSQL.
- **Semantic search** (`GET /search/semantic`) — Embeds the user's query via OpenAI and finds similar chunks using pgvector cosine similarity.
- **Transcript retrieval** (`GET /episodes/:id/transcript`) — Returns all chunks for an episode in order.
- **Bookmark CRUD** (`POST/GET/DELETE /bookmarks`) — Authenticated endpoints for managing saved chunks.
- **Health check** (`GET /health`) — Simple liveness check.
- **Transcript ingestion pipeline** — CLI script that parses plain text transcripts, chunks them with a sliding window, generates embeddings, and stores everything in Supabase.

Deployed to **Render** or **Railway**.

### Supabase

Provides multiple services:

- **PostgreSQL Database** — Stores all structured data: podcasts, episodes, transcript chunks, and bookmarks.
- **pgvector Extension** — Enables vector similarity search on transcript chunk embeddings.
- **Supabase Storage** — Stores raw transcript text files.
- **Supabase Auth** — Handles Google OAuth authentication. The frontend uses the Supabase JS client for sign-in/sign-out and session management.

### OpenAI Embeddings API

Used in two places:

1. **Ingestion** — When a transcript is ingested, each chunk's text is sent to OpenAI to generate an embedding vector, which is stored in the `transcript_chunks` table.
2. **Semantic search** — When a user performs a semantic search, their query is embedded using the same model, then compared against stored vectors using pgvector cosine similarity.

## Data Flow

### Transcript Ingestion

1. An admin places a plain text transcript file in Supabase Storage.
2. A CLI script is run with the episode ID and transcript file path.
3. The script downloads/reads the transcript file.
4. The parser extracts each line's speaker label, timestamps, and text.
5. Lines are grouped into overlapping chunks (sliding window: ~8-10 lines per chunk, ~4-5 line overlap).
6. Each chunk is sent to the OpenAI Embeddings API to generate a vector.
7. Chunks (with text, metadata, and embeddings) are inserted into the `transcript_chunks` table in Supabase.

### Search (Keyword)

1. User types a search term and selects "Keyword" mode on the frontend.
2. Frontend calls `GET /search/keyword?q=<term>&page=1&page_size=10`.
3. Backend runs a PostgreSQL full-text search against `chunk_text` in `transcript_chunks`.
4. For each match, the backend retrieves 2 context chunks before and after (by `chunk_index`).
5. Results are returned with chunk text, context, speaker label, timestamps, and episode metadata.
6. Frontend renders paginated result cards.

### Search (Semantic)

1. User types a natural language query and selects "Semantic" mode.
2. Frontend calls `GET /search/semantic?q=<query>&page=1&page_size=10`.
3. Backend sends the query to the OpenAI Embeddings API to get a vector.
4. Backend queries `transcript_chunks` using pgvector cosine similarity to find the closest matches.
5. Context chunks and metadata are fetched the same way as keyword search.
6. Results are returned and rendered on the frontend.

### Authentication

1. User clicks "Sign In" in the app header.
2. Supabase Auth initiates the Google OAuth flow.
3. On success, a session is created and persisted in the browser.
4. Auth state is available globally via React context so all components can react to it.
5. Authenticated users can access bookmark features.

## Database Schema

| Table | Key Columns |
|-------|-------------|
| `podcasts` | id, name, created_at |
| `episodes` | id, podcast_id (FK), title, episode_number, publication_date, description, transcript_file_url, created_at |
| `transcript_chunks` | id, episode_id (FK), chunk_text, speaker_label, start_timestamp, end_timestamp, embedding (vector), chunk_index, created_at |
| `bookmarks` | id, user_id (FK), chunk_id (FK), created_at |
