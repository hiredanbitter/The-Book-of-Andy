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
# Step 1: Create a podcast (idempotent — returns existing ID if name matches)
poetry run python -m app.ingestion.create_podcast "The Book of Andy"

# Step 2: Create an episode with metadata
poetry run python -m app.ingestion.create_episode <podcast_id> "Episode Title" \
    --episode-number 1 --publication-date 2025-01-15 \
    --description "Description" --transcript-file-url "https://..."

# Step 3: Ingest a transcript (validates episode exists first)
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path>

# With custom chunk settings
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path> --chunk-size 10 --chunk-overlap 5
```

Required environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`.

## Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for violations (auto-fix enabled)
poetry run ruff check . --fix

# Format code
poetry run ruff format .
```

Ruff is configured in `pyproject.toml` under `[tool.ruff]`.

## Implementation Decisions

- **FastAPI** was chosen for its async support, automatic OpenAPI docs, and strong typing with Pydantic.
- **Poetry** is used for dependency management to ensure reproducible installs.
- **CORS** is configured to allow all origins during development. This will be tightened for production.
- Environment variables are loaded from a `.env` file using `python-dotenv`.
