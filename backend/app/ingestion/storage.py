"""Supabase storage helpers for the ingestion pipeline.

Handles inserting transcript chunks (with embeddings) into the
``transcript_chunks`` table.
"""

import logging
import os

from supabase import Client, create_client

from app.ingestion.chunker import TranscriptChunk

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Return a Supabase client configured from environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables "
            "must both be set."
        )
    return create_client(url, key)


def store_chunks(
    episode_id: str,
    chunks: list[TranscriptChunk],
    embeddings: list[list[float]],
) -> int:
    """Insert transcript chunks with embeddings into Supabase.

    Parameters
    ----------
    episode_id:
        UUID of the episode these chunks belong to.
    chunks:
        Ordered list of transcript chunks.
    embeddings:
        Embedding vectors, one per chunk (same order as *chunks*).

    Returns
    -------
    int
        Number of rows successfully inserted.

    Raises
    ------
    RuntimeError
        If the Supabase insert fails.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Mismatch: {len(chunks)} chunks but {len(embeddings)} embeddings"
        )

    client = get_supabase_client()

    rows = [
        {
            "episode_id": episode_id,
            "chunk_text": chunk.chunk_text,
            "speaker_label": chunk.speaker_label,
            "start_timestamp": chunk.start_timestamp,
            "end_timestamp": chunk.end_timestamp,
            "embedding": embedding,
            "chunk_index": chunk.chunk_index,
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    try:
        result = (
            client.table("transcript_chunks").insert(rows).execute()
        )
    except Exception as exc:
        logger.error("Failed to insert chunks into Supabase: %s", exc)
        raise RuntimeError(
            f"Supabase insert failed: {exc}"
        ) from exc

    inserted_count = len(result.data) if result.data else 0
    logger.info(
        "Inserted %d chunks for episode %s", inserted_count, episode_id
    )
    return inserted_count
