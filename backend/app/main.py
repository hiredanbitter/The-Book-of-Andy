from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bookmarks.router import router as bookmarks_router
from app.episodes.router import router as episodes_router
from app.search.router import router as search_router

load_dotenv()

app = FastAPI(
    title="Podcast Transcript Search API",
    description="Backend API for the Podcast Transcript Search App",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
