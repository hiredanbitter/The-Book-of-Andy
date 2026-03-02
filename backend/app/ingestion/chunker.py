"""Sliding-window chunker for transcript lines.

Groups parsed transcript lines into overlapping chunks.  The chunk size
and overlap are configurable via function parameters, with sensible
defaults from ``config.py``.
"""

import logging
from dataclasses import dataclass

from app.ingestion.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from app.ingestion.parser import TranscriptLine

logger = logging.getLogger(__name__)


@dataclass
class TranscriptChunk:
    """A chunk of consecutive transcript lines ready for embedding."""

    chunk_text: str
    speaker_label: str
    start_timestamp: str
    end_timestamp: str
    chunk_index: int


def build_chunks(
    lines: list[TranscriptLine],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TranscriptChunk]:
    """Create overlapping chunks from a list of parsed transcript lines.

    Parameters
    ----------
    lines:
        Ordered list of transcript lines for a single episode.
    chunk_size:
        Number of lines per chunk (default from config).
    chunk_overlap:
        Number of lines shared between consecutive chunks (default from config).

    Returns
    -------
    list[TranscriptChunk]
        Ordered list of chunks with metadata derived from their lines.
    """
    if not lines:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be less than "
            f"chunk_size ({chunk_size})"
        )

    step = chunk_size - chunk_overlap
    chunks: list[TranscriptChunk] = []

    for chunk_index, start in enumerate(range(0, len(lines), step)):
        window = lines[start : start + chunk_size]
        if not window:
            break

        # Combine line texts, preserving the original transcript format
        chunk_text = "\n".join(
            f"[{line.start_timestamp} - {line.end_timestamp}] "
            f"{line.speaker_label}: {line.text}"
            for line in window
        )

        chunks.append(
            TranscriptChunk(
                chunk_text=chunk_text,
                speaker_label=window[0].speaker_label,
                start_timestamp=window[0].start_timestamp,
                end_timestamp=window[-1].end_timestamp,
                chunk_index=chunk_index,
            )
        )

        # If the window already reached the end, stop
        if start + chunk_size >= len(lines):
            break

    logger.info(
        "Created %d chunks (chunk_size=%d, overlap=%d) from %d lines",
        len(chunks),
        chunk_size,
        chunk_overlap,
        len(lines),
    )
    return chunks
