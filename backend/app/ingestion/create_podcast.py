#!/usr/bin/env python3
"""CLI script for creating a podcast in the database.

Usage:
    poetry run python -m app.ingestion.create_podcast <podcast_name>

Arguments:
    podcast_name  Name of the podcast to create.

If a podcast with the given name already exists, its ID is returned
without creating a duplicate.

Environment variables required:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

from app.ingestion.storage import get_supabase_client


def create_podcast(name: str) -> str:
    """Insert a podcast into the podcasts table if it doesn't already exist.

    Parameters
    ----------
    name:
        Name of the podcast.

    Returns
    -------
    str
        UUID of the podcast (existing or newly created).
    """
    client = get_supabase_client()

    # Check if a podcast with this name already exists
    existing = (
        client.table("podcasts")
        .select("id")
        .eq("name", name)
        .execute()
    )

    if existing.data:
        return str(existing.data[0]["id"])

    # Insert new podcast
    result = (
        client.table("podcasts")
        .insert({"name": name})
        .execute()
    )

    if not result.data:
        raise RuntimeError(f"Failed to insert podcast '{name}'")

    return str(result.data[0]["id"])


def main() -> None:
    """Entry point for the podcast creation CLI."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Create a podcast in the database (or return existing ID)."
    )
    parser.add_argument(
        "podcast_name",
        help="Name of the podcast.",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        podcast_id = create_podcast(args.podcast_name)
    except Exception:
        logger.exception("Failed to create podcast")
        sys.exit(1)

    logger.info("Podcast '%s' — ID: %s", args.podcast_name, podcast_id)
    # Print the ID so it can be captured by other scripts
    print(podcast_id)


if __name__ == "__main__":
    main()
