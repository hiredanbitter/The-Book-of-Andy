"""Pydantic models for bookmark request and response shapes."""

from pydantic import BaseModel, Field


class BookmarkCreate(BaseModel):
    """Request body for creating a bookmark."""

    chunk_id: str = Field(..., description="UUID of the transcript chunk to bookmark")


class BookmarkResponse(BaseModel):
    """A single bookmark with full chunk data and episode metadata."""

    bookmark_id: str
    chunk_id: str
    chunk_text: str
    speaker_label: str
    start_timestamp: str
    end_timestamp: str
    chunk_index: int
    episode_id: str
    episode_title: str
    episode_number: int | None = None
    podcast_name: str
    publication_date: str | None = None
    created_at: str


class BookmarkListResponse(BaseModel):
    """Response containing all bookmarks for the authenticated user."""

    bookmarks: list[BookmarkResponse]
