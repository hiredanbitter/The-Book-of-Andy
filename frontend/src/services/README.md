# Services

API client modules for communicating with the FastAPI backend.

## Key Files

- **`searchApi.ts`** — Client for `GET /search/keyword` and `GET /search/semantic` endpoints. Returns typed `SearchResponse` objects.
- **`bookmarksApi.ts`** — Client for bookmark endpoints (`GET /bookmarks`, `POST /bookmarks`, `DELETE /bookmarks/:id`). All calls require a Supabase JWT access token passed in the `Authorization` header. Includes a custom `BookmarkLimitError` class thrown when the API returns a 400 status (user has reached the 100 bookmark cap).

## Implementation Decisions

- **Typed responses**: Both modules define response interfaces that mirror the backend Pydantic schemas to ensure type safety across the API boundary.
- **Error handling**: `bookmarksApi` distinguishes between bookmark limit errors (400) and general failures, allowing the UI to display context-appropriate error messages.
- **No global auth header**: The access token is passed explicitly to each bookmark API function rather than being set globally, keeping the service stateless and testable.
