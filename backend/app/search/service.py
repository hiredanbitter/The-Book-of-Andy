"""Search service — business logic for keyword and semantic search.

Uses PostgreSQL full-text search and pgvector cosine similarity via
Supabase to find matching transcript chunks, then fetches surrounding
context chunks and episode/podcast metadata.
"""

import logging
import os

from openai import OpenAI
from supabase import Client, create_client

from app.ingestion.config import EMBEDDING_MODEL
from app.search.schemas import ContextChunk, SearchResponse, SearchResult

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


def _get_openai_client() -> OpenAI:
    """Return an OpenAI client configured from environment variables."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set."
        )
    return OpenAI(api_key=api_key)


def _embed_query(query: str) -> list[float]:
    """Embed a search query using the OpenAI Embeddings API.

    Parameters
    ----------
    query:
        The user's search query text.

    Returns
    -------
    list[float]
        The embedding vector for the query.

    Raises
    ------
    RuntimeError
        If the OpenAI API call fails.
    """
    client = _get_openai_client()
    try:
        response = client.embeddings.create(input=[query], model=EMBEDDING_MODEL)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to embed query via OpenAI: {exc}"
        ) from exc
    return response.data[0].embedding


def _sanitize_query(query: str) -> str:
    """Sanitize the user query string for use with ``plainto_tsquery``.

    Strips leading/trailing whitespace. ``plainto_tsquery`` handles
    raw user input safely — no special formatting is needed.
    """
    return query.strip()


def keyword_search(
    query: str,
    page: int = 1,
    page_size: int = 10,
) -> SearchResponse:
    """Perform keyword search against transcript chunks.

    Uses PostgreSQL full-text search (``to_tsvector`` / ``to_tsquery``)
    on the ``chunk_text`` column.  For each matching chunk the 2
    preceding and 2 following chunks (by ``chunk_index`` within the same
    episode) are returned as context.

    Parameters
    ----------
    query:
        The user's search terms.
    page:
        1-based page number.
    page_size:
        Number of results per page.

    Returns
    -------
    SearchResponse
        Paginated results with total count.
    """
    if not query or not query.strip():
        return SearchResponse(results=[], total=0, page=page, page_size=page_size)

    client = _get_supabase_client()
    sanitized = _sanitize_query(query)
    if not sanitized:
        return SearchResponse(results=[], total=0, page=page, page_size=page_size)

    offset = (page - 1) * page_size

    # Use Supabase RPC to call a database function for full-text search.
    # This function handles the full-text search, context retrieval,
    # and metadata joins in a single database round-trip.
    result = client.rpc(
        "keyword_search",
        {
            "search_query": sanitized,
            "result_limit": page_size,
            "result_offset": offset,
        },
    ).execute()

    rows = result.data or []

    if not rows:
        return SearchResponse(results=[], total=0, page=page, page_size=page_size)

    # The RPC returns a total_count field on each row
    total = rows[0].get("total_count", 0) if rows else 0

    # Collect all episode IDs and chunk indices to fetch context in bulk
    context_requests: list[tuple[str, int]] = []
    for row in rows:
        context_requests.append((row["episode_id"], row["chunk_index"]))

    # Fetch context chunks for all results
    context_map = _fetch_context_chunks(client, context_requests)

    results: list[SearchResult] = []
    for row in rows:
        episode_id = row["episode_id"]
        chunk_index = row["chunk_index"]
        key = (episode_id, chunk_index)

        before, after = context_map.get(key, ([], []))

        results.append(
            SearchResult(
                chunk_id=row["chunk_id"],
                chunk_text=row["chunk_text"],
                speaker_label=row["speaker_label"],
                start_timestamp=row["start_timestamp"],
                end_timestamp=row["end_timestamp"],
                chunk_index=chunk_index,
                episode_id=episode_id,
                episode_title=row["episode_title"],
                episode_number=row.get("episode_number"),
                podcast_name=row["podcast_name"],
                publication_date=row.get("publication_date"),
                context_before=before,
                context_after=after,
            )
        )

    return SearchResponse(
        results=results,
        total=total,
        page=page,
        page_size=page_size,
    )


def _fetch_context_chunks(
    client: Client,
    requests: list[tuple[str, int]],
) -> dict[tuple[str, int], tuple[list[ContextChunk], list[ContextChunk]]]:
    """Fetch the 2 preceding and 2 following chunks for each match.

    Parameters
    ----------
    client:
        Supabase client.
    requests:
        List of (episode_id, chunk_index) pairs for which to fetch context.

    Returns
    -------
    dict
        Mapping from (episode_id, chunk_index) to (context_before, context_after).
    """
    if not requests:
        return {}

    # Gather all episode_ids and the range of chunk indices we need
    episode_indices: dict[str, set[int]] = {}
    for episode_id, chunk_index in requests:
        if episode_id not in episode_indices:
            episode_indices[episode_id] = set()
        # We need chunks at chunk_index-2, chunk_index-1, chunk_index+1, chunk_index+2
        for offset in (-2, -1, 1, 2):
            idx = chunk_index + offset
            if idx >= 0:
                episode_indices[episode_id].add(idx)

    # Fetch all needed context chunks in batches per episode
    context_chunks: dict[str, dict[int, ContextChunk]] = {}
    for episode_id, indices in episode_indices.items():
        if not indices:
            continue
        indices_list = sorted(indices)
        result = (
            client.table("transcript_chunks")
            .select(
                "chunk_index, chunk_text, speaker_label, "
                "start_timestamp, end_timestamp"
            )
            .eq("episode_id", episode_id)
            .in_("chunk_index", indices_list)
            .order("chunk_index")
            .execute()
        )
        ep_chunks: dict[int, ContextChunk] = {}
        for row in result.data or []:
            ep_chunks[row["chunk_index"]] = ContextChunk(
                chunk_index=row["chunk_index"],
                chunk_text=row["chunk_text"],
                speaker_label=row["speaker_label"],
                start_timestamp=row["start_timestamp"],
                end_timestamp=row["end_timestamp"],
            )
        context_chunks[episode_id] = ep_chunks

    # Build the result mapping
    result_map: dict[
        tuple[str, int], tuple[list[ContextChunk], list[ContextChunk]]
    ] = {}
    for episode_id, chunk_index in requests:
        ep_chunks = context_chunks.get(episode_id, {})
        before = []
        for offset in (-2, -1):
            idx = chunk_index + offset
            if idx >= 0 and idx in ep_chunks:
                before.append(ep_chunks[idx])
        after = []
        for offset in (1, 2):
            idx = chunk_index + offset
            if idx in ep_chunks:
                after.append(ep_chunks[idx])
        result_map[(episode_id, chunk_index)] = (before, after)

    return result_map


SEMANTIC_SEARCH_LIMIT: int = 30
"""Maximum number of results returned by semantic search."""


def semantic_search(
    query: str,
) -> SearchResponse:
    """Perform semantic search against transcript chunks.

    Embeds the user's query using the OpenAI Embeddings API and finds
    the most similar chunk vectors via pgvector cosine similarity.
    Returns up to ``SEMANTIC_SEARCH_LIMIT`` (30) results — no pagination.
    For each matching chunk the 2 preceding and 2 following chunks
    (by ``chunk_index`` within the same episode) are returned as context.

    Parameters
    ----------
    query:
        The user's natural-language search terms.

    Returns
    -------
    SearchResponse
        Results with total count (page fixed to 1).

    Raises
    ------
    RuntimeError
        If the OpenAI Embeddings API call fails.
    """
    if not query or not query.strip():
        return SearchResponse(
            results=[], total=0, page=1, page_size=SEMANTIC_SEARCH_LIMIT
        )

    # Embed the query
    query_embedding = _embed_query(query.strip())

    client = _get_supabase_client()

    # Use Supabase RPC to call the semantic_search database function.
    # No pagination — return up to SEMANTIC_SEARCH_LIMIT results.
    result = client.rpc(
        "semantic_search",
        {
            "query_embedding": query_embedding,
            "result_limit": SEMANTIC_SEARCH_LIMIT,
            "result_offset": 0,
        },
    ).execute()

    rows = result.data or []

    if not rows:
        return SearchResponse(
            results=[], total=0, page=1, page_size=SEMANTIC_SEARCH_LIMIT
        )

    total = rows[0].get("total_count", 0) if rows else 0

    # Collect all episode IDs and chunk indices to fetch context in bulk
    context_requests: list[tuple[str, int]] = []
    for row in rows:
        context_requests.append((row["episode_id"], row["chunk_index"]))

    # Fetch context chunks for all results
    context_map = _fetch_context_chunks(client, context_requests)

    results: list[SearchResult] = []
    for row in rows:
        episode_id = row["episode_id"]
        chunk_index = row["chunk_index"]
        key = (episode_id, chunk_index)

        before, after = context_map.get(key, ([], []))

        results.append(
            SearchResult(
                chunk_id=row["chunk_id"],
                chunk_text=row["chunk_text"],
                speaker_label=row["speaker_label"],
                start_timestamp=row["start_timestamp"],
                end_timestamp=row["end_timestamp"],
                chunk_index=chunk_index,
                episode_id=episode_id,
                episode_title=row["episode_title"],
                episode_number=row.get("episode_number"),
                podcast_name=row["podcast_name"],
                publication_date=row.get("publication_date"),
                context_before=before,
                context_after=after,
            )
        )

    return SearchResponse(
        results=results,
        total=total,
        page=1,
        page_size=SEMANTIC_SEARCH_LIMIT,
    )
