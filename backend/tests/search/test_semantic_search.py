"""Tests for the semantic search endpoint and service layer."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.search.service import SEMANTIC_SEARCH_LIMIT, _embed_query, semantic_search

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests for _embed_query
# ---------------------------------------------------------------------------


class TestEmbedQuery:
    @patch("app.search.service._get_openai_client")
    def test_returns_embedding_vector(self, mock_get_client):
        """Should return the embedding vector from OpenAI."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1, 0.2, 0.3]
        mock_embedding.index = 0
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]
        mock_client.embeddings.create.return_value = mock_response

        result = _embed_query("test query")
        assert result == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once()

    @patch("app.search.service._get_openai_client")
    def test_raises_runtime_error_on_api_failure(self, mock_get_client):
        """Should wrap OpenAI exceptions in RuntimeError."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.embeddings.create.side_effect = Exception("API down")

        raised = False
        try:
            _embed_query("test query")
        except RuntimeError as e:
            raised = True
            assert "API down" in str(e)
        assert raised, "Expected a RuntimeError to be raised"


# ---------------------------------------------------------------------------
# Unit tests for the semantic_search service function
# ---------------------------------------------------------------------------


class TestSemanticSearchService:
    @patch("app.search.service._get_supabase_client")
    @patch("app.search.service._embed_query")
    def test_empty_query_returns_empty(self, mock_embed, mock_get_client):
        """Empty query should return empty results without calling APIs."""
        result = semantic_search(query="")
        assert result.results == []
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == SEMANTIC_SEARCH_LIMIT
        mock_embed.assert_not_called()
        mock_get_client.assert_not_called()

    @patch("app.search.service._get_supabase_client")
    @patch("app.search.service._embed_query")
    def test_whitespace_query_returns_empty(self, mock_embed, mock_get_client):
        """Whitespace-only query should return empty results."""
        result = semantic_search(query="   ")
        assert result.results == []
        assert result.total == 0
        mock_embed.assert_not_called()

    @patch("app.search.service._get_supabase_client")
    @patch("app.search.service._embed_query")
    def test_no_results_returns_empty(self, mock_embed, mock_get_client):
        """When the RPC returns no rows, response has empty results."""
        mock_embed.return_value = [0.1] * 1536
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        mock_client.rpc.return_value = mock_rpc

        result = semantic_search(query="nonexistent")
        assert result.results == []
        assert result.total == 0

    @patch("app.search.service._get_supabase_client")
    @patch("app.search.service._embed_query")
    def test_returns_results_with_metadata(self, mock_embed, mock_get_client):
        """Verify results include chunk data and episode/podcast metadata."""
        mock_embed.return_value = [0.1] * 1536
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        rpc_data = [
            {
                "chunk_id": "abc-123",
                "chunk_text": "Discussion about work-life balance",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:05:00",
                "end_timestamp": "0:05:30",
                "chunk_index": 5,
                "episode_id": "ep-001",
                "episode_title": "Episode One",
                "episode_number": 1,
                "podcast_name": "Test Podcast",
                "publication_date": "2025-01-15",
                "similarity": 0.92,
                "total_count": 1,
            }
        ]
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=rpc_data)
        mock_client.rpc.return_value = mock_rpc

        # Mock context chunks query (return empty)
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.in_.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=[])
        mock_client.table.return_value = mock_select
        mock_select.select.return_value = mock_select

        result = semantic_search(query="burnout")
        assert result.total == 1
        assert result.page == 1
        assert result.page_size == SEMANTIC_SEARCH_LIMIT
        assert len(result.results) == 1
        r = result.results[0]
        assert r.chunk_id == "abc-123"
        assert r.chunk_text == "Discussion about work-life balance"
        assert r.episode_title == "Episode One"
        assert r.podcast_name == "Test Podcast"

    @patch("app.search.service._get_supabase_client")
    @patch("app.search.service._embed_query")
    def test_rpc_called_with_limit_30_offset_0(
        self, mock_embed, mock_get_client
    ):
        """Verify the RPC is called with limit=30 and offset=0 (no pagination)."""
        mock_embed.return_value = [0.1] * 1536
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        mock_client.rpc.return_value = mock_rpc

        semantic_search(query="test")

        mock_client.rpc.assert_called_once_with(
            "semantic_search",
            {
                "query_embedding": [0.1] * 1536,
                "result_limit": SEMANTIC_SEARCH_LIMIT,
                "result_offset": 0,
            },
        )


# ---------------------------------------------------------------------------
# Unit tests for the /search/semantic endpoint
# ---------------------------------------------------------------------------


class TestSemanticSearchEndpoint:
    """Tests for the GET /search/semantic FastAPI endpoint."""

    def test_missing_query_param_returns_422(self):
        """Endpoint requires a `q` parameter."""
        response = client.get("/search/semantic")
        assert response.status_code == 422

    def test_empty_query_returns_422(self):
        """Empty query string should be rejected by min_length=1."""
        response = client.get("/search/semantic?q=")
        assert response.status_code == 422

    @patch("app.search.router.semantic_search")
    def test_no_results_returns_empty(self, mock_search):
        """When the service returns no rows, response has empty results."""
        from app.search.schemas import SearchResponse

        mock_search.return_value = SearchResponse(
            results=[], total=0, page=1, page_size=30
        )

        response = client.get("/search/semantic?q=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 30

    @patch("app.search.router.semantic_search")
    def test_search_returns_results_with_metadata(self, mock_search):
        """Verify results include chunk data and episode/podcast metadata."""
        from app.search.schemas import SearchResponse, SearchResult

        mock_search.return_value = SearchResponse(
            results=[
                SearchResult(
                    chunk_id="abc-123",
                    chunk_text="Discussion about work-life balance",
                    speaker_label="SPEAKER_01",
                    start_timestamp="0:05:00",
                    end_timestamp="0:05:30",
                    chunk_index=5,
                    episode_id="ep-001",
                    episode_title="Episode One",
                    episode_number=1,
                    podcast_name="Test Podcast",
                    publication_date="2025-01-15",
                    context_before=[],
                    context_after=[],
                )
            ],
            total=1,
            page=1,
            page_size=30,
        )

        response = client.get("/search/semantic?q=burnout")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1

        result = data["results"][0]
        assert result["chunk_id"] == "abc-123"
        assert result["chunk_text"] == "Discussion about work-life balance"
        assert result["speaker_label"] == "SPEAKER_01"
        assert result["episode_title"] == "Episode One"
        assert result["podcast_name"] == "Test Podcast"
        assert result["context_before"] == []
        assert result["context_after"] == []

    @patch("app.search.router.semantic_search")
    def test_openai_failure_returns_503(self, mock_search):
        """When OpenAI API fails, endpoint returns 503."""
        mock_search.side_effect = RuntimeError("OpenAI API unavailable")

        response = client.get("/search/semantic?q=burnout")
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "temporarily unavailable" in data["detail"]

    @patch("app.search.router.semantic_search")
    def test_endpoint_only_accepts_q_param(self, mock_search):
        """page and page_size params are ignored (not declared on endpoint)."""
        from app.search.schemas import SearchResponse

        mock_search.return_value = SearchResponse(
            results=[], total=0, page=1, page_size=30
        )

        # Extra query params are silently ignored by FastAPI
        response = client.get("/search/semantic?q=test&page=2&page_size=5")
        assert response.status_code == 200
        # The service was called with only q (no page/page_size)
        mock_search.assert_called_once_with(query="test")

    @patch("app.search.router.semantic_search")
    def test_search_with_context_chunks(self, mock_search):
        """Verify context_before and context_after are populated."""
        from app.search.schemas import (
            ContextChunk,
            SearchResponse,
            SearchResult,
        )

        mock_search.return_value = SearchResponse(
            results=[
                SearchResult(
                    chunk_id="abc-123",
                    chunk_text="Main matching chunk",
                    speaker_label="SPEAKER_01",
                    start_timestamp="0:05:00",
                    end_timestamp="0:05:30",
                    chunk_index=5,
                    episode_id="ep-001",
                    episode_title="Episode One",
                    episode_number=1,
                    podcast_name="Test Podcast",
                    publication_date="2025-01-15",
                    context_before=[
                        ContextChunk(
                            chunk_index=3,
                            chunk_text="Context before 1",
                            speaker_label="SPEAKER_01",
                            start_timestamp="0:03:00",
                            end_timestamp="0:03:30",
                        ),
                        ContextChunk(
                            chunk_index=4,
                            chunk_text="Context before 2",
                            speaker_label="SPEAKER_01",
                            start_timestamp="0:04:00",
                            end_timestamp="0:04:30",
                        ),
                    ],
                    context_after=[
                        ContextChunk(
                            chunk_index=6,
                            chunk_text="Context after 1",
                            speaker_label="SPEAKER_02",
                            start_timestamp="0:06:00",
                            end_timestamp="0:06:30",
                        ),
                        ContextChunk(
                            chunk_index=7,
                            chunk_text="Context after 2",
                            speaker_label="SPEAKER_02",
                            start_timestamp="0:07:00",
                            end_timestamp="0:07:30",
                        ),
                    ],
                )
            ],
            total=1,
            page=1,
            page_size=30,
        )

        response = client.get("/search/semantic?q=burnout")
        assert response.status_code == 200
        data = response.json()

        result = data["results"][0]
        assert len(result["context_before"]) == 2
        assert len(result["context_after"]) == 2
        assert result["context_before"][0]["chunk_index"] == 3
        assert result["context_before"][1]["chunk_index"] == 4
        assert result["context_after"][0]["chunk_index"] == 6
        assert result["context_after"][1]["chunk_index"] == 7
