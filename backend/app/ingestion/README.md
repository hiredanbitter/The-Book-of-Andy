# Ingestion — Transcript Chunking & Embedding Pipeline

This module implements the transcript ingestion pipeline that parses plain-text transcript files, chunks them into non-overlapping fixed-size groups of lines, generates embeddings via the OpenAI API, and stores everything in Supabase.

## Purpose

Converts raw transcript text files into searchable, embedded chunks in the `transcript_chunks` database table. This is the foundational step that enables both keyword and semantic search.

## Key Files

| File | Description |
|------|-------------|
| `config.py` | Configurable pipeline parameters (chunk size, embedding model) |
| `parser.py` | Parses plain-text transcript files into structured `TranscriptLine` objects |
| `chunker.py` | Groups parsed lines into non-overlapping `TranscriptChunk` objects of fixed size |
| `embeddings.py` | Generates embedding vectors via the OpenAI Embeddings API |
| `storage.py` | Inserts chunks with embeddings into the Supabase `transcript_chunks` table; verifies episode existence |
| `pipeline.py` | Orchestrates the full parse → chunk → embed → store pipeline (validates episode exists first) |
| `ingest_transcript.py` | CLI entry point for running the ingestion pipeline from the command line |
| `create_podcast.py` | CLI script to create a podcast in the `podcasts` table (idempotent — returns existing ID if name matches) |
| `create_episode.py` | CLI script to create an episode in the `episodes` table with all required metadata fields |

## Usage

### 1. Create a Podcast

Before creating episodes, the parent podcast must exist:

```bash
# From the backend/ directory
poetry run python -m app.ingestion.create_podcast "The Book of Andy"
# Prints the podcast UUID (creates if new, returns existing if name matches)
```

### 2. Create an Episode

Create an episode record with metadata before ingesting its transcript:

```bash
poetry run python -m app.ingestion.create_episode <podcast_id> "Episode Title" \
    --episode-number 1 \
    --publication-date 2025-01-15 \
    --description "Episode description here" \
    --transcript-file-url "https://your-supabase-url.supabase.co/storage/v1/object/public/transcripts/episode1.txt"
# Prints the episode UUID
```

### 3. Ingest a Transcript

The ingestion pipeline requires a valid episode ID (it verifies the episode exists before processing):

```bash
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path>

# With custom chunk size
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path> --chunk-size 10
```

### Full Workflow Example

```bash
# Step 1: Create the podcast (idempotent)
PODCAST_ID=$(poetry run python -m app.ingestion.create_podcast "The Book of Andy")

# Step 2: Create the episode
EPISODE_ID=$(poetry run python -m app.ingestion.create_episode "$PODCAST_ID" "Episode 1: Pilot" \
    --episode-number 1 \
    --publication-date 2025-01-15 \
    --description "The first episode" \
    --transcript-file-url "https://example.supabase.co/storage/v1/object/public/transcripts/ep1.txt")

# Step 3: Ingest the transcript
poetry run python -m app.ingestion.ingest_transcript "$EPISODE_ID" ./transcripts/ep1.txt
```

### Required Environment Variables

- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key (for privileged inserts)
- `OPENAI_API_KEY` — OpenAI API key (for embedding generation)

These can be set in a `.env` file in the project root.

## Transcript Format

The parser expects plain-text files with lines in this format:

```
[0:00:16 - 0:00:30] SPEAKER_01: transcript text here
```

- Timestamps use `H:MM:SS` format
- Speaker labels are alphanumeric with underscores (e.g. `SPEAKER_01`)
- Blank lines are silently skipped
- Malformed lines are logged as warnings and skipped

## Chunking Strategy

Lines are grouped into non-overlapping chunks of fixed size:

- **Default chunk size**: 1 line per chunk
- Each line appears in exactly one chunk, with no lines shared between consecutive chunks
- The chunk size is configurable via a CLI flag or by modifying `config.py`

Each chunk stores:
- The combined raw text of all lines in the chunk
- The speaker label from the first line
- The start timestamp from the first line
- The end timestamp from the last line
- The chunk index (position within the episode)
- The embedding vector (1536 dimensions from OpenAI `text-embedding-3-small`)

## Implementation Decisions

- **Non-overlapping fixed-size chunks** ensure that each line appears in exactly one chunk, eliminating duplicate or near-duplicate search results.
- **Configurable chunk size** allows tuning via a CLI flag or `config.py` without code changes.
- **`text-embedding-3-small`** was chosen as the embedding model for its good balance of quality and cost, matching the 1536-dimensional vector column in the database schema.
- **Malformed line handling** logs warnings but does not abort the pipeline, following the principle of processing as much valid data as possible.
- **Chunk text preserves the original line format** (timestamps, speaker labels) so that the stored text is self-contained and useful for display.
- **Episode validation** — the pipeline verifies the episode exists in the database before running, providing a clear error message with guidance if the episode is missing.
- **Idempotent podcast creation** — `create_podcast` checks for an existing podcast by name before inserting, preventing duplicates.
- **Episode creation validates podcast** — `create_episode` verifies the parent podcast exists before inserting, enforcing referential integrity at the application level.
