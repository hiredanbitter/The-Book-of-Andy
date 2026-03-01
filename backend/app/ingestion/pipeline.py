"""End-to-end transcript ingestion pipeline.

Orchestrates parsing, chunking, embedding, and storage for a single
episode transcript.
"""

import logging

from app.ingestion.chunker import TranscriptChunk, build_chunks
from app.ingestion.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from app.ingestion.embeddings import generate_embeddings
from app.ingestion.parser import parse_transcript
from app.ingestion.storage import store_chunks

logger = logging.getLogger(__name__)


def run_pipeline(
    episode_id: str,
    transcript_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> int:
    """Run the full ingestion pipeline for a single episode.

    Steps:
      1. Parse the transcript file into individual lines
      2. Group lines into overlapping chunks
      3. Generate embeddings for each chunk via OpenAI
      4. Store chunks + embeddings in Supabase

    Parameters
    ----------
    episode_id:
        UUID of the episode in the ``episodes`` table.
    transcript_path:
        Local file path to the plain-text transcript file.
    chunk_size:
        Number of lines per chunk.
    chunk_overlap:
        Number of lines shared between consecutive chunks.

    Returns
    -------
    int
        Number of chunks successfully stored.
    """
    # Step 1 — Parse
    logger.info("Step 1/4: Parsing transcript from %s", transcript_path)
    lines = parse_transcript(transcript_path)
    if not lines:
        logger.warning("No valid lines found in %s — aborting.", transcript_path)
        return 0

    # Step 2 — Chunk
    logger.info("Step 2/4: Building chunks (size=%d, overlap=%d)", chunk_size, chunk_overlap)
    chunks: list[TranscriptChunk] = build_chunks(
        lines, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    if not chunks:
        logger.warning("Chunking produced no chunks — aborting.")
        return 0

    # Step 3 — Embed
    logger.info("Step 3/4: Generating embeddings for %d chunks", len(chunks))
    chunk_texts = [chunk.chunk_text for chunk in chunks]
    embeddings = generate_embeddings(chunk_texts)

    # Step 4 — Store
    logger.info("Step 4/4: Storing chunks in Supabase")
    inserted = store_chunks(episode_id, chunks, embeddings)

    logger.info(
        "Pipeline complete: %d chunks ingested for episode %s",
        inserted,
        episode_id,
    )
    return inserted
