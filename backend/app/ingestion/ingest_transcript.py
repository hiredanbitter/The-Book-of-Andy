#!/usr/bin/env python3
"""CLI script for ingesting a transcript into the database.

Usage:
    poetry run python -m app.ingestion.ingest_transcript
        <episode_id> <transcript_file_path>
        [--chunk-size N] [--chunk-overlap N]

Arguments:
    episode_id           UUID of the episode in the episodes table.
    transcript_file_path Path to the plain-text transcript file.

Options:
    --chunk-size N       Number of lines per chunk (default: 8).
    --chunk-overlap N    Number of overlapping lines between chunks (default: 4).

Environment variables required:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
    OPENAI_API_KEY
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

from app.ingestion.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from app.ingestion.pipeline import run_pipeline


def main() -> None:
    """Entry point for the transcript ingestion CLI."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Ingest a transcript file into the database."
    )
    parser.add_argument(
        "episode_id",
        help="UUID of the episode in the episodes table.",
    )
    parser.add_argument(
        "transcript_file_path",
        help="Path to the plain-text transcript file.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Number of lines per chunk (default: {DEFAULT_CHUNK_SIZE}).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=(
            "Number of overlapping lines between chunks"
            f" (default: {DEFAULT_CHUNK_OVERLAP})."
        ),
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info(
        "Starting ingestion for episode %s from %s",
        args.episode_id,
        args.transcript_file_path,
    )

    try:
        chunk_count = run_pipeline(
            episode_id=args.episode_id,
            transcript_path=args.transcript_file_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    except Exception:
        logger.exception("Ingestion pipeline failed")
        sys.exit(1)

    logger.info(
        "Success: %d chunks ingested for episode %s",
        chunk_count,
        args.episode_id,
    )


if __name__ == "__main__":
    main()
