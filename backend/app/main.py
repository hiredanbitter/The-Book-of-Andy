import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bookmarks.router import router as bookmarks_router
from app.episodes.router import router as episodes_router
from app.search.router import router as search_router

load_dotenv()

DEFAULT_CORS_ORIGINS = ["http://localhost:5173"]


def _get_allowed_origins() -> list[str]:
    """Return the list of allowed CORS origins.

    Reads from the CORS_ALLOWED_ORIGINS environment variable (comma-separated).
    Falls back to allowing only http://localhost:5173 if the variable is not set.
    """
    env_value = os.environ.get("CORS_ALLOWED_ORIGINS")
    if env_value:
        return [origin.strip() for origin in env_value.split(",") if origin.strip()]
    return DEFAULT_CORS_ORIGINS

app = FastAPI(
    title="Podcast Transcript Search API",
    description="Backend API for the Podcast Transcript Search App",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(bookmarks_router)
app.include_router(episodes_router)
app.include_router(search_router)


@app.get("/health")
def health_check():
    """Health check endpoint that returns a 200 response."""
    return {"status": "ok"}
