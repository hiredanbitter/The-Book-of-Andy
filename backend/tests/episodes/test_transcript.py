"""Tests for the episode transcript endpoint and service layer."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests for the GET /episodes/:id/transcript endpoint
# ---------------------------------------------------------------------------


class TestTranscriptEndpoint:
    """Tests for the GET /episodes/{episode_id}/transcript FastAPI endpoint."""

    @patch("app.episodes.service._get_supabase_client")
    def test_episode_not_found_returns_404(self, mock_get_client):
        """When the episode does not exist, return 404."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Episode query returns empty
        mock_select = MagicMock()
        mock_select.select.return_value = mock_select
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=[])
        mock_client.table.return_value = mock_select

        response = client.get("/episodes/nonexistent-id/transcript")
        assert response.status_code == 404
        assert response.json()["detail"] == "Episode not found."

    @patch("app.episodes.service._get_supabase_client")
    def test_returns_episode_metadata_and_chunks(self, mock_get_client):
        """Verify response includes episode metadata and ordered chunks."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock episode query with podcast join
        episode_data = [
            {
                "id": "ep-001",
                "title": "Episode One",
                "episode_number": 1,
                "publication_date": "2025-01-15",
                "description": "First episode description",
                "podcasts": {"name": "Test Podcast"},
            }
        ]

        # Mock transcript chunks
        chunks_data = [
            {
                "id": "chunk-001",
                "chunk_index": 0,
                "chunk_text": "Hello and welcome",
                "speaker_label": "SPEAKER_01",
                "start_timestamp": "0:00:00",
                "end_timestamp": "0:00:30",
            },
            {
                "id": "chunk-002",
                "chunk_index": 1,
                "chunk_text": "Today we discuss topics",
                "speaker_label": "SPEAKER_02",
                "start_timestamp": "0:00:30",
                "end_timestamp": "0:01:00",
            },
        ]

        # Set up table mock to return different results based on table name
        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            mock_select = MagicMock()
            mock_select.select.return_value = mock_select
            mock_select.eq.return_value = mock_select
            mock_select.order.return_value = mock_select

            if table_name == "episodes":
                mock_select.execute.return_value = MagicMock(data=episode_data)
            else:
                mock_select.execute.return_value = MagicMock(data=chunks_data)
            call_count += 1
            return mock_select

        mock_client.table.side_effect = table_side_effect

        response = client.get("/episodes/ep-001/transcript")
        assert response.status_code == 200
        data = response.json()

        # Verify episode metadata
        episode = data["episode"]
        assert episode["episode_id"] == "ep-001"
        assert episode["episode_title"] == "Episode One"
        assert episode["episode_number"] == 1
        assert episode["podcast_name"] == "Test Podcast"
        assert episode["publication_date"] == "2025-01-15"
        assert episode["description"] == "First episode description"

        # Verify chunks
        assert len(data["chunks"]) == 2
        assert data["chunks"][0]["chunk_id"] == "chunk-001"
        assert data["chunks"][0]["chunk_index"] == 0
        assert data["chunks"][0]["chunk_text"] == "Hello and welcome"
        assert data["chunks"][0]["speaker_label"] == "SPEAKER_01"
        assert data["chunks"][1]["chunk_id"] == "chunk-002"
        assert data["chunks"][1]["chunk_index"] == 1

    @patch("app.episodes.service._get_supabase_client")
    def test_episode_with_no_chunks(self, mock_get_client):
        """Episode exists but has no transcript chunks yet."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        episode_data = [
            {
                "id": "ep-002",
                "title": "Episode Two",
                "episode_number": 2,
                "publication_date": None,
                "description": None,
                "podcasts": {"name": "Test Podcast"},
            }
        ]

        def table_side_effect(table_name):
            mock_select = MagicMock()
            mock_select.select.return_value = mock_select
            mock_select.eq.return_value = mock_select
            mock_select.order.return_value = mock_select

            if table_name == "episodes":
                mock_select.execute.return_value = MagicMock(data=episode_data)
            else:
                mock_select.execute.return_value = MagicMock(data=[])
            return mock_select

        mock_client.table.side_effect = table_side_effect

        response = client.get("/episodes/ep-002/transcript")
        assert response.status_code == 200
        data = response.json()

        assert data["episode"]["episode_id"] == "ep-002"
        assert data["episode"]["episode_number"] == 2
        assert data["episode"]["publication_date"] is None
        assert data["episode"]["description"] is None
        assert data["chunks"] == []

    @patch("app.episodes.service._get_supabase_client")
    def test_podcast_name_from_list_format(self, mock_get_client):
        """Handle Supabase returning podcast join as a list."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        episode_data = [
            {
                "id": "ep-003",
                "title": "Episode Three",
                "episode_number": 3,
                "publication_date": "2025-03-01",
                "description": "Third episode",
                "podcasts": [{"name": "List Format Podcast"}],
            }
        ]

        def table_side_effect(table_name):
            mock_select = MagicMock()
            mock_select.select.return_value = mock_select
            mock_select.eq.return_value = mock_select
            mock_select.order.return_value = mock_select

            if table_name == "episodes":
                mock_select.execute.return_value = MagicMock(data=episode_data)
            else:
                mock_select.execute.return_value = MagicMock(data=[])
            return mock_select

        mock_client.table.side_effect = table_side_effect

        response = client.get("/episodes/ep-003/transcript")
        assert response.status_code == 200
        data = response.json()
        assert data["episode"]["podcast_name"] == "List Format Podcast"
