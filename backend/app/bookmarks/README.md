# Bookmarks Module

Authenticated API endpoints for saving, listing, and deleting bookmarked transcript chunks.

## Files

- **`auth.py`** — FastAPI dependency that extracts and verifies Supabase JWTs from the `Authorization: Bearer <token>` header. Returns the authenticated user's UUID. All bookmark endpoints depend on this.
- **`schemas.py`** — Pydantic request/response models. `BookmarkCreate` accepts a `chunk_id`. `BookmarkResponse` includes full chunk data and episode metadata so the frontend can render bookmark cards in the same format as search result cards.
- **`service.py`** — Business logic layer. Handles Supabase queries for creating, listing, counting, ownership-checking, and deleting bookmarks. Joins through `transcript_chunks -> episodes -> podcasts` to return enriched metadata.
- **`router.py`** — FastAPI router registered at `/bookmarks`. Exposes `POST`, `GET`, and `DELETE` endpoints, all gated behind `get_current_user_id` auth dependency.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/bookmarks` | Required | Save a bookmark (accepts `chunk_id`). Enforces 100-bookmark cap. |
| `GET` | `/bookmarks` | Required | List all bookmarks for the authenticated user with full metadata. |
| `DELETE` | `/bookmarks/{bookmark_id}` | Required | Delete a bookmark. Must be owned by the requesting user. |

## Design Decisions

- **Auth via `get_user(token)`**: The backend verifies the Supabase JWT by calling `client.auth.get_user(token)` with the service role client, which validates the token server-side rather than doing local JWT decoding. This avoids needing to manage JWKS keys.
- **100-bookmark cap**: Enforced at the API layer before insert. The count query uses Supabase's `count="exact"` for efficiency.
- **Ownership checks on delete**: The service fetches the bookmark's `user_id` before deletion and the router compares it to the authenticated user, returning 403 for mismatches and 404 for missing bookmarks.
