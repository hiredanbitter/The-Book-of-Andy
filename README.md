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

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for a full description of the system components, data flow, and how services connect.

## License

Private project.
