"""Configuration for the transcript ingestion pipeline.

Chunking parameters are defined here so they can be tuned without
modifying the pipeline logic.
"""

# Number of transcript lines per chunk (default: 1)
DEFAULT_CHUNK_SIZE: int = 1

# OpenAI embedding model to use
EMBEDDING_MODEL: str = "text-embedding-3-small"

# Dimension of the embedding vectors produced by the model
EMBEDDING_DIMENSION: int = 1536
