"""OpenAI Embeddings integration.

Generates embedding vectors for transcript chunks using the OpenAI
Embeddings API.  Handles batching and error reporting.
"""

import logging
import os

from openai import OpenAI

from app.ingestion.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """Return an OpenAI client configured from environment variables."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it before running the ingestion pipeline."
        )
    return OpenAI(api_key=api_key)


def generate_embeddings(
    texts: list[str],
    model: str = EMBEDDING_MODEL,
) -> list[list[float]]:
    """Generate embedding vectors for a list of text strings.

    Parameters
    ----------
    texts:
        The text strings to embed.
    model:
        The OpenAI embedding model to use.

    Returns
    -------
    list[list[float]]
        One embedding vector per input text, in the same order.

    Raises
    ------
    RuntimeError
        If the OpenAI API call fails.
    """
    if not texts:
        return []

    client = get_openai_client()

    try:
        response = client.embeddings.create(input=texts, model=model)
    except Exception as exc:
        logger.error("OpenAI Embeddings API call failed: %s", exc)
        raise RuntimeError(
            f"Failed to generate embeddings via OpenAI: {exc}"
        ) from exc

    # Sort by index to guarantee ordering matches input
    sorted_data = sorted(response.data, key=lambda item: item.index)
    embeddings = [item.embedding for item in sorted_data]

    logger.info(
        "Generated %d embeddings (model=%s, dimensions=%d)",
        len(embeddings),
        model,
        len(embeddings[0]) if embeddings else 0,
    )
    return embeddings
