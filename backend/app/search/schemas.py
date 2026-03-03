"""Pydantic models for search request parameters and response shapes."""

from pydantic import BaseModel, Field


class ContextChunk(BaseModel):
    """A neighboring chunk used as context around a matching chunk."""

    chunk_index: int
    chunk_text: str
    speaker_label: str
    start_timestamp: str
    end_timestamp: str


class SearchResult(BaseModel):
    """A single search result with matching chunk, context, and metadata."""

    chunk_id: str
    chunk_text: str
    highlighted_text: str | None = None
    speaker_label: str
    start_timestamp: str
    end_timestamp: str
    chunk_index: int
    episode_id: str
    episode_title: str
    episode_number: int | None = None
    podcast_name: str
    publication_date: str | None = None
    context_before: list[ContextChunk] = Field(default_factory=list)
    context_after: list[ContextChunk] = Field(default_factory=list)


class SearchResponse(BaseModel):
    """Paginated search response."""

    results: list[SearchResult]
    total: int
    page: int
    page_size: int
