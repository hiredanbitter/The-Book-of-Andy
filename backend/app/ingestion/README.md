# Ingestion — Transcript Chunking & Embedding Pipeline

This module implements the transcript ingestion pipeline that parses plain-text transcript files, chunks them using a sliding window strategy, generates embeddings via the OpenAI API, and stores everything in Supabase.

## Purpose

Converts raw transcript text files into searchable, embedded chunks in the `transcript_chunks` database table. This is the foundational step that enables both keyword and semantic search.

## Key Files

| File | Description |
|------|-------------|
| `config.py` | Configurable pipeline parameters (chunk size, overlap, embedding model) |
| `parser.py` | Parses plain-text transcript files into structured `TranscriptLine` objects |
| `chunker.py` | Groups parsed lines into overlapping `TranscriptChunk` objects using a sliding window |
| `embeddings.py` | Generates embedding vectors via the OpenAI Embeddings API |
| `storage.py` | Inserts chunks with embeddings into the Supabase `transcript_chunks` table |
| `pipeline.py` | Orchestrates the full parse → chunk → embed → store pipeline |
| `ingest_transcript.py` | CLI entry point for running the pipeline from the command line |

## Usage

```bash
# From the backend/ directory
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path>

# With custom chunk settings
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path> --chunk-size 10 --chunk-overlap 5
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

Lines are grouped into overlapping chunks using a sliding window:

- **Default chunk size**: 8 lines per chunk
- **Default overlap**: 4 lines shared between consecutive chunks
- Both parameters are configurable via CLI flags or by modifying `config.py`

Each chunk stores:
- The combined raw text of all lines in the chunk
- The speaker label from the first line
- The start timestamp from the first line
- The end timestamp from the last line
- The chunk index (position within the episode)
- The embedding vector (1536 dimensions from OpenAI `text-embedding-3-small`)

## Implementation Decisions

- **Sliding window with overlap** ensures that no content falls at the boundary between chunks and is missed during search.
- **Configurable parameters** allow tuning chunk size and overlap without code changes.
- **`text-embedding-3-small`** was chosen as the embedding model for its good balance of quality and cost, matching the 1536-dimensional vector column in the database schema.
- **Malformed line handling** logs warnings but does not abort the pipeline, following the principle of processing as much valid data as possible.
- **Chunk text preserves the original line format** (timestamps, speaker labels) so that the stored text is self-contained and useful for display.
