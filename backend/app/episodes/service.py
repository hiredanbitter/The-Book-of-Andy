"""Service layer for episode transcript retrieval.

Fetches episode metadata and all transcript chunks from Supabase,
returning them in chronological order for the transcript detail page.
"""

import logging
import os

from supabase import Client, create_client

from app.episodes.schemas import (
    EpisodeMetadata,
    TranscriptChunk,
    TranscriptResponse,
)

logger = logging.getLogger(__name__)


def _get_supabase_client() -> Client:
    """Return a Supabase client configured from environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables "
            "must both be set."
        )
    return create_client(url, key)


def get_episode_transcript(episode_id: str) -> TranscriptResponse | None:
    """Fetch the full transcript for an episode.

    Retrieves episode metadata (with podcast name) and all transcript
    chunks ordered by ``chunk_index``.

    Parameters
    ----------
    episode_id:
        UUID of the episode.

    Returns
    -------
    TranscriptResponse | None
        The transcript with metadata if the episode exists, otherwise ``None``.
    """
    client = _get_supabase_client()

    # Fetch episode metadata with podcast name via join
    episode_result = (
        client.table("episodes")
        .select(
            "id, title, episode_number, publication_date, description, "
            "podcasts(name)"
        )
        .eq("id", episode_id)
        .execute()
    )

    if not episode_result.data:
        return None

    episode_row = episode_result.data[0]

    # Extract podcast name from the joined podcasts relation
    podcast_data = episode_row.get("podcasts")
    podcast_name = ""
    if isinstance(podcast_data, dict):
        podcast_name = podcast_data.get("name", "")
    elif isinstance(podcast_data, list) and podcast_data:
        podcast_name = podcast_data[0].get("name", "")

    episode = EpisodeMetadata(
        episode_id=episode_row["id"],
        episode_title=episode_row["title"],
        episode_number=episode_row.get("episode_number"),
        podcast_name=podcast_name,
        publication_date=episode_row.get("publication_date"),
        description=episode_row.get("description"),
    )

    # Fetch all transcript chunks for this episode, ordered by chunk_index
    chunks_result = (
        client.table("transcript_chunks")
        .select(
            "id, chunk_index, chunk_text, speaker_label, "
            "start_timestamp, end_timestamp"
        )
        .eq("episode_id", episode_id)
        .order("chunk_index")
        .execute()
    )

    chunks = [
        TranscriptChunk(
            chunk_id=row["id"],
            chunk_index=row["chunk_index"],
            chunk_text=row["chunk_text"],
            speaker_label=row["speaker_label"],
            start_timestamp=row["start_timestamp"],
            end_timestamp=row["end_timestamp"],
        )
        for row in (chunks_result.data or [])
    ]

    return TranscriptResponse(episode=episode, chunks=chunks)
