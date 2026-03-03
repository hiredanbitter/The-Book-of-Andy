"""Tests for the bookmark API endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Shared test data
MOCK_USER_ID = "user-abc-123"
MOCK_OTHER_USER_ID = "user-xyz-789"
MOCK_CHUNK_ID = "chunk-001"
MOCK_BOOKMARK_ID = "bm-001"


def _auth_header() -> dict[str, str]:
    """Return a mock Authorization header."""
    return {"Authorization": "Bearer fake-jwt-token"}


def _mock_chunk_with_episode() -> list[dict]:
    """Return mock transcript_chunks row with nested episode/podcast joins."""
    return [
        {
            "id": MOCK_CHUNK_ID,
            "chunk_text": "This is a test chunk about podcasting",
            "speaker_label": "SPEAKER_01",
            "start_timestamp": "0:05:00",
            "end_timestamp": "0:05:30",
            "chunk_index": 5,
            "episode_id": "ep-001",
            "episodes": {
                "id": "ep-001",
                "title": "Episode One",
                "episode_number": 1,
                "publication_date": "2025-01-15",
                "podcasts": {"name": "Test Podcast"},
            },
        }
    ]


# ---------------------------------------------------------------------------
# Unauthenticated access tests
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """All bookmark endpoints should return 401 without a valid token."""

    def test_post_bookmark_unauthenticated(self):
        """POST /bookmarks without auth returns 401 or 403."""
        response = client.post(
            "/bookmarks", json={"chunk_id": MOCK_CHUNK_ID}
        )
        assert response.status_code in (401, 403)

    def test_get_bookmarks_unauthenticated(self):
        """GET /bookmarks without auth returns 401 or 403."""
        response = client.get("/bookmarks")
        assert response.status_code in (401, 403)

    def test_delete_bookmark_unauthenticated(self):
        """DELETE /bookmarks/:id without auth returns 401 or 403."""
        response = client.delete(f"/bookmarks/{MOCK_BOOKMARK_ID}")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# POST /bookmarks tests
# ---------------------------------------------------------------------------


class TestCreateBookmark:
    """Tests for the POST /bookmarks endpoint."""

    @patch("app.bookmarks.auth._get_supabase_client")
    @patch("app.bookmarks.service._get_supabase_client")
    def test_create_bookmark_success(
        self, mock_service_client, mock_auth_client
    ):
        """Authenticated user with < 100 bookmarks can create a bookmark."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock service client
        mock_svc = MagicMock()
        mock_service_client.return_value = mock_svc

        # Mock bookmark count query (< 100)
        mock_count_select = MagicMock()
        mock_count_select.eq.return_value = mock_count_select
        mock_count_select.execute.return_value = MagicMock(count=5)

        # Mock bookmark insert
        mock_insert = MagicMock()
        mock_insert.execute.return_value = MagicMock(
            data=[
                {
                    "id": MOCK_BOOKMARK_ID,
                    "user_id": MOCK_USER_ID,
                    "chunk_id": MOCK_CHUNK_ID,
                    "created_at": "2025-06-01T12:00:00Z",
                }
            ]
        )

        # Mock chunk+episode fetch
        mock_chunk_select = MagicMock()
        mock_chunk_select.eq.return_value = mock_chunk_select
        mock_chunk_select.execute.return_value = MagicMock(
            data=_mock_chunk_with_episode()
        )

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = MagicMock()
            if table_name == "bookmarks" and call_count == 1:
                # Count query
                mock_table.select.return_value = mock_count_select
                return mock_table
            elif table_name == "bookmarks" and call_count == 2:
                # Insert query
                mock_table.insert.return_value = mock_insert
                return mock_table
            else:
                # Chunk fetch
                mock_table.select.return_value = mock_chunk_select
                return mock_table

        mock_svc.table.side_effect = table_side_effect

        response = client.post(
            "/bookmarks",
            json={"chunk_id": MOCK_CHUNK_ID},
            headers=_auth_header(),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["bookmark_id"] == MOCK_BOOKMARK_ID
        assert data["chunk_id"] == MOCK_CHUNK_ID
        assert data["chunk_text"] == "This is a test chunk about podcasting"
        assert data["speaker_label"] == "SPEAKER_01"
        assert data["episode_id"] == "ep-001"
        assert data["episode_title"] == "Episode One"
        assert data["podcast_name"] == "Test Podcast"
        assert data["created_at"] == "2025-06-01T12:00:00Z"

    @patch("app.bookmarks.auth._get_supabase_client")
    @patch("app.bookmarks.service._get_supabase_client")
    def test_create_bookmark_limit_reached(
        self, mock_service_client, mock_auth_client
    ):
        """User with 100 bookmarks gets a 400 error."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock service client
        mock_svc = MagicMock()
        mock_service_client.return_value = mock_svc

        # Mock bookmark count = 100
        mock_count_select = MagicMock()
        mock_count_select.eq.return_value = mock_count_select
        mock_count_select.execute.return_value = MagicMock(count=100)

        mock_svc.table.return_value.select.return_value = mock_count_select

        response = client.post(
            "/bookmarks",
            json={"chunk_id": MOCK_CHUNK_ID},
            headers=_auth_header(),
        )
        assert response.status_code == 400
        assert "limit" in response.json()["detail"].lower()

    @patch("app.bookmarks.auth._get_supabase_client")
    def test_create_bookmark_missing_chunk_id(self, mock_auth_client):
        """POST /bookmarks without chunk_id returns 422."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        response = client.post(
            "/bookmarks", json={}, headers=_auth_header()
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /bookmarks tests
# ---------------------------------------------------------------------------


class TestListBookmarks:
    """Tests for the GET /bookmarks endpoint."""

    @patch("app.bookmarks.auth._get_supabase_client")
    @patch("app.bookmarks.service._get_supabase_client")
    def test_list_bookmarks_returns_data(
        self, mock_service_client, mock_auth_client
    ):
        """Authenticated user gets their bookmarks with metadata."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock service client
        mock_svc = MagicMock()
        mock_service_client.return_value = mock_svc

        # Mock list query with joins
        bookmark_data = [
            {
                "id": MOCK_BOOKMARK_ID,
                "chunk_id": MOCK_CHUNK_ID,
                "created_at": "2025-06-01T12:00:00Z",
                "transcript_chunks": {
                    "id": MOCK_CHUNK_ID,
                    "chunk_text": "Test chunk text",
                    "speaker_label": "SPEAKER_01",
                    "start_timestamp": "0:05:00",
                    "end_timestamp": "0:05:30",
                    "chunk_index": 5,
                    "episode_id": "ep-001",
                    "episodes": {
                        "id": "ep-001",
                        "title": "Episode One",
                        "episode_number": 1,
                        "publication_date": "2025-01-15",
                        "podcasts": {"name": "Test Podcast"},
                    },
                },
            }
        ]

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=bookmark_data)
        mock_svc.table.return_value.select.return_value = mock_select

        response = client.get("/bookmarks", headers=_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert len(data["bookmarks"]) == 1

        bm = data["bookmarks"][0]
        assert bm["bookmark_id"] == MOCK_BOOKMARK_ID
        assert bm["chunk_text"] == "Test chunk text"
        assert bm["episode_title"] == "Episode One"
        assert bm["podcast_name"] == "Test Podcast"

    @patch("app.bookmarks.auth._get_supabase_client")
    @patch("app.bookmarks.service._get_supabase_client")
    def test_list_bookmarks_empty(
        self, mock_service_client, mock_auth_client
    ):
        """User with no bookmarks gets an empty list."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock service client
        mock_svc = MagicMock()
        mock_service_client.return_value = mock_svc

        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.order.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=[])
        mock_svc.table.return_value.select.return_value = mock_select

        response = client.get("/bookmarks", headers=_auth_header())
        assert response.status_code == 200
        data = response.json()
        assert data["bookmarks"] == []


# ---------------------------------------------------------------------------
# DELETE /bookmarks/:id tests
# ---------------------------------------------------------------------------


class TestDeleteBookmark:
    """Tests for the DELETE /bookmarks/:id endpoint."""

    @patch("app.bookmarks.auth._get_supabase_client")
    @patch("app.bookmarks.service._get_supabase_client")
    def test_delete_own_bookmark(
        self, mock_service_client, mock_auth_client
    ):
        """Authenticated user can delete their own bookmark."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock service client
        mock_svc = MagicMock()
        mock_service_client.return_value = mock_svc

        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = MagicMock()
            if call_count == 1:
                # Owner check
                mock_select = MagicMock()
                mock_select.eq.return_value = mock_select
                mock_select.execute.return_value = MagicMock(
                    data=[{"user_id": MOCK_USER_ID}]
                )
                mock_table.select.return_value = mock_select
            else:
                # Delete
                mock_delete = MagicMock()
                mock_delete.eq.return_value = mock_delete
                mock_delete.execute.return_value = MagicMock(data=[])
                mock_table.delete.return_value = mock_delete
            return mock_table

        mock_svc.table.side_effect = table_side_effect

        response = client.delete(
            f"/bookmarks/{MOCK_BOOKMARK_ID}", headers=_auth_header()
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["detail"].lower()

    @patch("app.bookmarks.auth._get_supabase_client")
    @patch("app.bookmarks.service._get_supabase_client")
    def test_delete_other_users_bookmark_returns_403(
        self, mock_service_client, mock_auth_client
    ):
        """Deleting another user's bookmark returns 403."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock service client
        mock_svc = MagicMock()
        mock_service_client.return_value = mock_svc

        # Owner check returns a different user
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value = MagicMock(
            data=[{"user_id": MOCK_OTHER_USER_ID}]
        )
        mock_svc.table.return_value.select.return_value = mock_select

        response = client.delete(
            f"/bookmarks/{MOCK_BOOKMARK_ID}", headers=_auth_header()
        )
        assert response.status_code == 403

    @patch("app.bookmarks.auth._get_supabase_client")
    @patch("app.bookmarks.service._get_supabase_client")
    def test_delete_nonexistent_bookmark_returns_404(
        self, mock_service_client, mock_auth_client
    ):
        """Deleting a bookmark that doesn't exist returns 404."""
        # Mock auth
        mock_auth = MagicMock()
        mock_auth_client.return_value = mock_auth
        mock_user = MagicMock()
        mock_user.id = MOCK_USER_ID
        mock_auth.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock service client
        mock_svc = MagicMock()
        mock_service_client.return_value = mock_svc

        # Owner check returns empty
        mock_select = MagicMock()
        mock_select.eq.return_value = mock_select
        mock_select.execute.return_value = MagicMock(data=[])
        mock_svc.table.return_value.select.return_value = mock_select

        response = client.delete(
            "/bookmarks/nonexistent-id", headers=_auth_header()
        )
        assert response.status_code == 404
