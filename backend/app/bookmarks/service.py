"""Service layer for bookmark operations.

Handles creating, listing, and deleting bookmarks via Supabase,
including fetching full chunk data and episode metadata for responses.
"""

import logging
import os

from supabase import Client, create_client

from app.bookmarks.schemas import BookmarkResponse

logger = logging.getLogger(__name__)

BOOKMARK_LIMIT = 100
"""Maximum number of bookmarks allowed per user."""


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



class BookmarkLimitReachedError(Exception):
    """Raised when a user has reached the maximum number of bookmarks."""


def create_bookmark(user_id: str, chunk_id: str) -> BookmarkResponse:
    """Create a new bookmark linking a user to a transcript chunk.

    Uses the ``create_bookmark_atomic`` Supabase RPC function which
    checks the bookmark count and inserts in a single transaction,
    preventing race conditions from concurrent requests.

    Parameters
    ----------
    user_id:
        UUID of the authenticated user.
    chunk_id:
        UUID of the transcript chunk to bookmark.

    Returns
    -------
    BookmarkResponse
        The newly created bookmark with full chunk and episode metadata.

    Raises
    ------
    BookmarkLimitReachedError
        If the user already has 100 bookmarks.
    ValueError
        If the chunk_id does not exist.
    """
    client = _get_supabase_client()

    try:
        rpc_result = client.rpc(
            "create_bookmark_atomic",
            {"p_user_id": user_id, "p_chunk_id": chunk_id, "p_limit": BOOKMARK_LIMIT},
        ).execute()
    except Exception as exc:
        if "BOOKMARK_LIMIT_REACHED" in str(exc):
            raise BookmarkLimitReachedError(
                f"Bookmark limit reached. You can save a maximum of "
                f"{BOOKMARK_LIMIT} bookmarks."
            ) from exc
        raise

    bookmark_row = rpc_result.data[0]
    bookmark_id = bookmark_row["bookmark_id"]
    created_at = bookmark_row["bookmark_created_at"]

    # Fetch chunk data with episode metadata
    return _build_bookmark_response(client, bookmark_id, chunk_id, created_at)


def list_bookmarks(user_id: str) -> list[BookmarkResponse]:
    """Retrieve all bookmarks for the authenticated user.

    Returns bookmarks with full chunk data and episode metadata,
    ordered by creation date (most recent first).

    Parameters
    ----------
    user_id:
        UUID of the authenticated user.

    Returns
    -------
    list[BookmarkResponse]
        All bookmarks for the user.
    """
    client = _get_supabase_client()

    # Fetch all bookmarks for the user with chunk and episode data via join
    result = (
        client.table("bookmarks")
        .select(
            "id, chunk_id, created_at, "
            "transcript_chunks("
            "id, chunk_text, speaker_label, start_timestamp, "
            "end_timestamp, chunk_index, episode_id, "
            "episodes(id, title, episode_number, publication_date, "
            "podcasts(name))"
            ")"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    bookmarks: list[BookmarkResponse] = []
    for row in result.data or []:
        chunk = row.get("transcript_chunks")
        if chunk is None:
            continue

        episode = chunk.get("episodes")
        if episode is None:
            continue

        podcast_data = episode.get("podcasts")
        podcast_name = ""
        if isinstance(podcast_data, dict):
            podcast_name = podcast_data.get("name", "")
        elif isinstance(podcast_data, list) and podcast_data:
            podcast_name = podcast_data[0].get("name", "")

        bookmarks.append(
            BookmarkResponse(
                bookmark_id=row["id"],
                chunk_id=row["chunk_id"],
                chunk_text=chunk["chunk_text"],
                speaker_label=chunk["speaker_label"],
                start_timestamp=chunk["start_timestamp"],
                end_timestamp=chunk["end_timestamp"],
                chunk_index=chunk["chunk_index"],
                episode_id=chunk["episode_id"],
                episode_title=episode["title"],
                episode_number=episode.get("episode_number"),
                podcast_name=podcast_name,
                publication_date=episode.get("publication_date"),
                created_at=row["created_at"],
            )
        )

    return bookmarks


def get_bookmark_owner(bookmark_id: str) -> str | None:
    """Return the user_id that owns a bookmark, or None if not found.

    Parameters
    ----------
    bookmark_id:
        UUID of the bookmark.

    Returns
    -------
    str | None
        The owner's user_id, or None if the bookmark doesn't exist.
    """
    client = _get_supabase_client()
    result = (
        client.table("bookmarks")
        .select("user_id")
        .eq("id", bookmark_id)
        .execute()
    )
    if not result.data:
        return None
    return result.data[0]["user_id"]


def delete_bookmark(bookmark_id: str) -> None:
    """Delete a bookmark by ID.

    Parameters
    ----------
    bookmark_id:
        UUID of the bookmark to delete.
    """
    client = _get_supabase_client()
    client.table("bookmarks").delete().eq("id", bookmark_id).execute()


def _build_bookmark_response(
    client: Client,
    bookmark_id: str,
    chunk_id: str,
    created_at: str,
) -> BookmarkResponse:
    """Fetch chunk + episode metadata and build a BookmarkResponse.

    Parameters
    ----------
    client:
        Supabase client.
    bookmark_id:
        UUID of the bookmark.
    chunk_id:
        UUID of the transcript chunk.
    created_at:
        Timestamp when the bookmark was created.

    Returns
    -------
    BookmarkResponse
        The bookmark with full chunk and episode metadata.
    """
    chunk_result = (
        client.table("transcript_chunks")
        .select(
            "id, chunk_text, speaker_label, start_timestamp, "
            "end_timestamp, chunk_index, episode_id, "
            "episodes(id, title, episode_number, publication_date, "
            "podcasts(name))"
        )
        .eq("id", chunk_id)
        .execute()
    )

    chunk_row = chunk_result.data[0]
    episode = chunk_row["episodes"]

    podcast_data = episode.get("podcasts")
    podcast_name = ""
    if isinstance(podcast_data, dict):
        podcast_name = podcast_data.get("name", "")
    elif isinstance(podcast_data, list) and podcast_data:
        podcast_name = podcast_data[0].get("name", "")

    return BookmarkResponse(
        bookmark_id=bookmark_id,
        chunk_id=chunk_id,
        chunk_text=chunk_row["chunk_text"],
        speaker_label=chunk_row["speaker_label"],
        start_timestamp=chunk_row["start_timestamp"],
        end_timestamp=chunk_row["end_timestamp"],
        chunk_index=chunk_row["chunk_index"],
        episode_id=chunk_row["episode_id"],
        episode_title=episode["title"],
        episode_number=episode.get("episode_number"),
        podcast_name=podcast_name,
        publication_date=episode.get("publication_date"),
        created_at=created_at,
    )
