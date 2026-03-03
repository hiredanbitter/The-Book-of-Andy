"""Pydantic models for episode transcript responses."""

from pydantic import BaseModel


class TranscriptChunk(BaseModel):
    """A single transcript chunk with text and metadata."""

    chunk_id: str
    chunk_index: int
    chunk_text: str
    speaker_label: str
    start_timestamp: str
    end_timestamp: str


class EpisodeMetadata(BaseModel):
    """Episode-level metadata displayed at the top of the transcript page."""

    episode_id: str
    episode_title: str
    episode_number: int | None = None
    podcast_name: str
    publication_date: str | None = None
    description: str | None = None


class TranscriptResponse(BaseModel):
    """Full transcript response with episode metadata and ordered chunks."""

    episode: EpisodeMetadata
    chunks: list[TranscriptChunk]
