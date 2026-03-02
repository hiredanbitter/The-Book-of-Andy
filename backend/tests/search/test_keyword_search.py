"""Tests for the keyword search endpoint and service layer."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.search.service import _fetch_context_chunks, _sanitize_query

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests for _build_tsquery
# ---------------------------------------------------------------------------


class TestSanitizeQuery:
    def test_single_term(self):
        assert _sanitize_query("burnout") == "burnout"

    def test_multiple_terms_preserved(self):
        assert _sanitize_query("work life balance") == "work life balance"

    def test_strips_whitespace(self):
        assert _sanitize_query("  hello world  ") == "hello world"

    def test_empty_string(self):
        assert _sanitize_query("") == ""

    def test_whitespace_only(self):
        assert _sanitize_query("   ") == ""

    def test_special_chars_preserved(self):
        """plainto_tsquery handles special chars safely."""
        assert _sanitize_query("work-life balance!") == "work-life balance!"


# ---------------------------------------------------------------------------
# Unit tests for the /search/keyword endpoint
# ---------------------------------------------------------------------------


class TestKeywordSearchEndpoint:
    """Tests for the GET /search/keyword FastAPI endpoint."""

    def test_missing_query_param_returns_422(self):
        """Endpoint requires a `q` parameter."""
        response = client.get("/search/keyword")
        assert response.status_code == 422

    def test_empty_query_returns_422(self):
        """Empty query string should be rejected by min_length=1."""
        response = client.get("/search/keyword?q=")
        assert response.status_code == 422

    @patch("app.search.service._get_supabase_client")
    def test_no_results_returns_empty(self, mock_get_client):
        """When the RPC returns no rows, response has empty results."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # RPC returns empty data
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        mock_client.rpc.return_value = mock_rpc

        response = client.get("/search/keyword?q=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 10

    @patch("app.search.service._get_supabase_client")
    def test_search_returns_results_with_metadata(self, mock_get_client):
        """Verify results include chunk data and episode/podcast metadata."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock RPC result
        rpc_data = [
            {
                "chunk_id": "abc-123",
                "chunk_text": "This is about burnout and stress",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:05:00",
                "end_timestamp": "0:05:30",
                "chunk_index": 5,
                "episode_id": "ep-001",
                "episode_title": "Episode One",
                "episode_number": 1,
                "podcast_name": "Test Podcast",
                "publication_date": "2025-01-15",
                "total_count": 1,
            }
        ]
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=rpc_data)
        mock_client.rpc.return_value = mock_rpc

        # Mock context chunks query (return empty — no context neighbors)
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.in_.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=[])
        mock_client.table.return_value = mock_select
        mock_select.select.return_value = mock_select

        response = client.get("/search/keyword?q=burnout")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["results"]) == 1

        result = data["results"][0]
        assert result["chunk_id"] == "abc-123"
        assert result["chunk_text"] == "This is about burnout and stress"
        assert result["speaker_label"] == "SPEAKER_01"
        assert result["start_timestamp"] == "0:05:00"
        assert result["end_timestamp"] == "0:05:30"
        assert result["chunk_index"] == 5
        assert result["episode_id"] == "ep-001"
        assert result["episode_title"] == "Episode One"
        assert result["episode_number"] == 1
        assert result["podcast_name"] == "Test Podcast"
        assert result["publication_date"] == "2025-01-15"
        assert result["context_before"] == []
        assert result["context_after"] == []

    @patch("app.search.service._get_supabase_client")
    def test_search_with_context_chunks(self, mock_get_client):
        """Verify context_before and context_after are populated."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock RPC result — match is at chunk_index=5
        rpc_data = [
            {
                "chunk_id": "abc-123",
                "chunk_text": "Main matching chunk",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:05:00",
                "end_timestamp": "0:05:30",
                "chunk_index": 5,
                "episode_id": "ep-001",
                "episode_title": "Episode One",
                "episode_number": 1,
                "podcast_name": "Test Podcast",
                "publication_date": "2025-01-15",
                "total_count": 1,
            }
        ]
        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=rpc_data)
        mock_client.rpc.return_value = mock_rpc

        # Mock context chunks — indices 3, 4, 6, 7
        context_data = [
            {
                "chunk_index": 3,
                "chunk_text": "Context before 1",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:03:00",
                "end_timestamp": "0:03:30",
            },
            {
                "chunk_index": 4,
                "chunk_text": "Context before 2",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:04:00",
                "end_timestamp": "0:04:30",
            },
            {
                "chunk_index": 6,
                "chunk_text": "Context after 1",
                "speaker_label": "SPEAKER_02",
                "start_timestamp": "0:06:00",
                "end_timestamp": "0:06:30",
            },
            {
                "chunk_index": 7,
                "chunk_text": "Context after 2",
                "speaker_label": "SPEAKER_02",
                "start_timestamp": "0:07:00",
                "end_timestamp": "0:07:30",
            },
        ]
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.in_.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=context_data)
        mock_client.table.return_value = mock_select
        mock_select.select.return_value = mock_select

        response = client.get("/search/keyword?q=burnout")
        assert response.status_code == 200
        data = response.json()

        result = data["results"][0]
        assert len(result["context_before"]) == 2
        assert len(result["context_after"]) == 2
        assert result["context_before"][0]["chunk_index"] == 3
        assert result["context_before"][1]["chunk_index"] == 4
        assert result["context_after"][0]["chunk_index"] == 6
        assert result["context_after"][1]["chunk_index"] == 7

    @patch("app.search.service._get_supabase_client")
    def test_pagination_parameters(self, mock_get_client):
        """Verify page and page_size are passed to the RPC correctly."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_rpc = MagicMock()
        mock_rpc.execute.return_value = MagicMock(data=[])
        mock_client.rpc.return_value = mock_rpc

        response = client.get("/search/keyword?q=test&page=3&page_size=5")
        assert response.status_code == 200

        # Verify RPC was called with correct offset
        mock_client.rpc.assert_called_once_with(
            "keyword_search",
            {
                "search_query": "test",  # raw query, plainto_tsquery handles it
                "result_limit": 5,
                "result_offset": 10,  # (3-1) * 5
            },
        )

    def test_page_must_be_positive(self):
        """Page parameter must be >= 1."""
        response = client.get("/search/keyword?q=test&page=0")
        assert response.status_code == 422

    def test_page_size_must_be_positive(self):
        """Page size must be >= 1."""
        response = client.get("/search/keyword?q=test&page_size=0")
        assert response.status_code == 422

    def test_page_size_max_100(self):
        """Page size must be <= 100."""
        response = client.get("/search/keyword?q=test&page_size=101")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Unit tests for _fetch_context_chunks
# ---------------------------------------------------------------------------


class TestFetchContextChunks:
    def test_empty_requests(self):
        """No requests should return empty dict."""
        mock_client = MagicMock()
        result = _fetch_context_chunks(mock_client, [])
        assert result == {}

    def test_context_at_start_of_episode(self):
        """Chunk at index 0 should only have context_after."""
        mock_client = MagicMock()

        context_data = [
            {
                "chunk_index": 1,
                "chunk_text": "After 1",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:01:00",
                "end_timestamp": "0:01:30",
            },
            {
                "chunk_index": 2,
                "chunk_text": "After 2",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:02:00",
                "end_timestamp": "0:02:30",
            },
        ]
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.in_.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=context_data)
        mock_client.table.return_value = mock_select
        mock_select.select.return_value = mock_select

        result = _fetch_context_chunks(mock_client, [("ep-001", 0)])
        before, after = result[("ep-001", 0)]
        assert len(before) == 0
        assert len(after) == 2

    def test_context_at_chunk_index_1(self):
        """Chunk at index 1 should have only 1 context_before."""
        mock_client = MagicMock()

        context_data = [
            {
                "chunk_index": 0,
                "chunk_text": "Before 1",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:00:00",
                "end_timestamp": "0:00:30",
            },
            {
                "chunk_index": 2,
                "chunk_text": "After 1",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:02:00",
                "end_timestamp": "0:02:30",
            },
            {
                "chunk_index": 3,
                "chunk_text": "After 2",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:03:00",
                "end_timestamp": "0:03:30",
            },
        ]
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.in_.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=context_data)
        mock_client.table.return_value = mock_select
        mock_select.select.return_value = mock_select

        result = _fetch_context_chunks(mock_client, [("ep-001", 1)])
        before, after = result[("ep-001", 1)]
        assert len(before) == 1
        assert before[0].chunk_index == 0
        assert len(after) == 2
