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
| `GET` | `/search/keyword` | Keyword search via PostgreSQL full-text search |
| `GET` | `/search/semantic` | Semantic search via OpenAI embeddings + pgvector cosine similarity |
| `POST` | `/bookmarks` | Create a bookmark (atomic 100-cap enforcement via DB function) |
| `GET` | `/bookmarks` | List all bookmarks for the authenticated user |
| `DELETE` | `/bookmarks/{id}` | Delete a bookmark owned by the authenticated user |

## Transcript Ingestion Pipeline

The ingestion pipeline parses plain-text transcript files, chunks them into fixed-size groups of lines, generates embeddings via OpenAI, and stores everything in Supabase. See the [ingestion module README](./app/ingestion/README.md) for full details.

```bash
# Step 1: Create a podcast (idempotent — returns existing ID if name matches)
poetry run python -m app.ingestion.create_podcast "The Book of Andy"

# Step 2: Create an episode with metadata
poetry run python -m app.ingestion.create_episode <podcast_id> "Episode Title" \
    --episode-number 1 --publication-date 2025-01-15 \
    --description "Description" --transcript-file-url "https://..."

# Step 3: Ingest a transcript (validates episode exists first)
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path>

# With custom chunk size
poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file_path> --chunk-size 10
```

Required environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`.

## CORS Configuration

By default, the backend only allows requests from `http://localhost:5173` (the local Vite dev server). To allow additional origins (e.g. a production frontend), set the `CORS_ALLOWED_ORIGINS` environment variable to a comma-separated list of URLs:

```bash
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://your-production-domain.com
```

If `CORS_ALLOWED_ORIGINS` is not set, only `http://localhost:5173` is allowed. See `backend/.env.example` for a template.

> **Note:** Authenticated endpoints verify JWTs using the public JWKS endpoint at `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` (ES256). No additional secret is required — the signing key is fetched and cached automatically.

## Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for violations (auto-fix enabled)
poetry run ruff check . --fix

# Format code
poetry run ruff format .
```

Ruff is configured in `pyproject.toml` under `[tool.ruff]`.

## Railway Deployment

The `Procfile` and `requirements.txt` in this directory are used by Railway to build and start the backend service.

- **`requirements.txt`** is auto-generated from `pyproject.toml` via `poetry export` and **should not be edited manually**. Poetry remains the source of truth for dependencies in local development. Regenerate it whenever dependencies change:
  ```bash
  poetry export -f requirements.txt --output requirements.txt --without-hashes
  ```
- **`Procfile`** tells Railway how to start the application. It should not need to change unless the app entrypoint changes.

## Implementation Decisions

- **FastAPI** was chosen for its async support, automatic OpenAPI docs, and strong typing with Pydantic.
- **Poetry** is used for dependency management to ensure reproducible installs.
- **CORS** is configured via the `CORS_ALLOWED_ORIGINS` environment variable, defaulting to `http://localhost:5173` for local development.
- Environment variables are loaded from a `.env` file using `python-dotenv`.
