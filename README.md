# Podcast Transcript Search App

A full-stack application for searching podcast transcripts using both keyword and semantic search. Built to help users discover specific moments across podcast episodes.

## Tech Stack

- **Frontend:** React (TypeScript) with Vite
- **Backend:** Python FastAPI
- **Database:** Supabase (PostgreSQL + pgvector)
- **Storage:** Supabase Storage (raw transcript files)
- **Authentication:** Supabase Auth with Google OAuth
- **Embeddings:** OpenAI Embeddings API
- **Frontend Deployment:** Vercel
- **Backend Deployment:** Render or Railway

## Directory Structure

```
.
├── frontend/          # React (Vite) frontend application
├── backend/           # Python FastAPI backend application
├── supabase/          # Supabase SQL migrations and database schema
├── ARCHITECTURE.md    # System architecture and data flow documentation
├── .env.example       # Required environment variables
└── github-issues.md   # Project issue tracker / ticket reference
```

## Getting Started

### Prerequisites

- Node.js (v18+)
- Python 3.10+
- Poetry (Python package manager)
- A Supabase project (with pgvector enabled)
- An OpenAI API key

### Environment Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Fill in the required values in `.env` (see `.env.example` for documentation of each variable).

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at [http://localhost:5173](http://localhost:5173).

### Running the Backend

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

The backend will start at [http://localhost:8000](http://localhost:8000).

- Health check: `GET http://localhost:8000/health`
- API docs (Swagger): `GET http://localhost:8000/docs`

## Database Setup

The Supabase database schema and migrations are in the [`supabase/`](./supabase) directory. See the [Supabase README](./supabase/README.md) for full schema documentation, RLS policies, and implementation decisions.

### Google OAuth

Google OAuth is configured through the Supabase Auth dashboard. To enable it:

1. Create a Google OAuth client in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add the client ID and secret to the Supabase Auth settings under **Providers > Google**
3. Set the redirect URL to your Supabase project's auth callback URL

## Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for the Python backend and [ESLint](https://eslint.org/) for the TypeScript frontend.

### Running linters manually

```bash
# Backend (from the backend/ directory)
poetry run ruff check . --fix

# Frontend (from the frontend/ directory)
npm run lint
```

### Pre-commit hook

A [pre-commit](https://pre-commit.com/) configuration is included so that both linters run automatically on every commit.

```bash
# Install the pre-commit framework (one-time)
pip install pre-commit

# Install the git hook (run from the repo root)
pre-commit install
```

Once installed, Ruff and ESLint will run against staged files each time you `git commit`. They will auto-fix what they can; if unfixable violations remain the commit will be blocked.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for a full description of the system components, data flow, and how services connect.

## License

Private project.
