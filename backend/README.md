# Backend — Podcast Transcript Search API

Python FastAPI backend for the Podcast Transcript Search App.

## Purpose

This directory contains the API server that powers transcript search (keyword and semantic), transcript retrieval, bookmark management, and the transcript ingestion pipeline.

## Key Files

| File / Directory | Description |
|------------------|-------------|
| `app/` | Application source code |
| `app/main.py` | FastAPI application entry point with CORS and health check |
| `app/__init__.py` | Python package marker |
| `app/ingestion/` | Transcript chunking & embedding pipeline (see [ingestion README](./app/ingestion/README.md)) |
| `pyproject.toml` | Project metadata and dependencies (managed by Poetry) |

## Getting Started

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Runs on [http://localhost:8000](http://localhost:8000) by default.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |

Additional endpoints will be added as the project progresses (search, transcripts, bookmarks).

## Transcript Ingestion Pipeline

The ingestion pipeline parses plain-text transcript files, chunks them with a sliding window, generates embeddings via OpenAI, and stores everything in Supabase. See the [ingestion module README](./app/ingestion/README.md) for full details.

```bash
# Ingest a transcript
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path>

# With custom chunk settings
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path> --chunk-size 10 --chunk-overlap 5
```

Required environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`.

## Implementation Decisions

- **FastAPI** was chosen for its async support, automatic OpenAPI docs, and strong typing with Pydantic.
- **Poetry** is used for dependency management to ensure reproducible installs.
- **CORS** is configured to allow all origins during development. This will be tightened for production.
- Environment variables are loaded from a `.env` file using `python-dotenv`.
