#!/usr/bin/env python3
"""CLI script for creating an episode in the database.

Usage:
    poetry run python -m app.ingestion.create_episode <podcast_id> <title> \\
        --episode-number N --publication-date YYYY-MM-DD \\
        --description "..." --transcript-file-url "..."

Arguments:
    podcast_id  UUID of the parent podcast in the podcasts table.
    title       Episode title.

Options:
    --episode-number N           Episode number (integer).
    --publication-date YYYY-MM-DD  Publication date.
    --description TEXT            Episode description.
    --transcript-file-url URL    URL of the raw transcript file in Supabase Storage.

Environment variables required:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

from app.ingestion.storage import get_supabase_client


def create_episode(
    podcast_id: str,
    title: str,
    episode_number: int | None = None,
    publication_date: str | None = None,
    description: str | None = None,
    transcript_file_url: str | None = None,
) -> str:
    """Insert an episode into the episodes table.

    Parameters
    ----------
    podcast_id:
        UUID of the parent podcast.
    title:
        Episode title.
    episode_number:
        Episode number (optional).
    publication_date:
        Publication date in YYYY-MM-DD format (optional).
    description:
        Episode description (optional).
    transcript_file_url:
        URL of the raw transcript file in Supabase Storage (optional).

    Returns
    -------
    str
        UUID of the newly created episode.
    """
    client = get_supabase_client()

    # Verify the podcast exists
    podcast_check = (
        client.table("podcasts")
        .select("id")
        .eq("id", podcast_id)
        .execute()
    )
    if not podcast_check.data:
        raise ValueError(
            f"Podcast with ID '{podcast_id}' does not exist. "
            "Create the podcast first using create_podcast."
        )

    row: dict[str, str | int | None] = {
        "podcast_id": podcast_id,
        "title": title,
    }
    if episode_number is not None:
        row["episode_number"] = episode_number
    if publication_date is not None:
        row["publication_date"] = publication_date
    if description is not None:
        row["description"] = description
    if transcript_file_url is not None:
        row["transcript_file_url"] = transcript_file_url

    result = client.table("episodes").insert(row).execute()

    if not result.data:
        raise RuntimeError(f"Failed to insert episode '{title}'")

    return str(result.data[0]["id"])


def main() -> None:
    """Entry point for the episode creation CLI."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Create an episode in the database."
    )
    parser.add_argument(
        "podcast_id",
        help="UUID of the parent podcast.",
    )
    parser.add_argument(
        "title",
        help="Episode title.",
    )
    parser.add_argument(
        "--episode-number",
        type=int,
        default=None,
        help="Episode number.",
    )
    parser.add_argument(
        "--publication-date",
        default=None,
        help="Publication date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--description",
        default=None,
        help="Episode description.",
    )
    parser.add_argument(
        "--transcript-file-url",
        default=None,
        help="URL of the raw transcript file in Supabase Storage.",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        episode_id = create_episode(
            podcast_id=args.podcast_id,
            title=args.title,
            episode_number=args.episode_number,
            publication_date=args.publication_date,
            description=args.description,
            transcript_file_url=args.transcript_file_url,
        )
    except Exception:
        logger.exception("Failed to create episode")
        sys.exit(1)

    logger.info("Episode '%s' — ID: %s", args.title, episode_id)
    # Print the ID so it can be captured by other scripts
    print(episode_id)


if __name__ == "__main__":
    main()
