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

## Implementation Decisions

- **FastAPI** was chosen for its async support, automatic OpenAPI docs, and strong typing with Pydantic.
- **Poetry** is used for dependency management to ensure reproducible installs.
- **CORS** is configured to allow all origins during development. This will be tightened for production.
- Environment variables are loaded from a `.env` file using `python-dotenv`.
