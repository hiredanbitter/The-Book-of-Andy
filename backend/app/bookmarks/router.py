"""FastAPI router for bookmark endpoints."""

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from app.bookmarks.auth import get_current_user_id
from app.bookmarks.schemas import (
    BookmarkCreate,
    BookmarkListResponse,
    BookmarkResponse,
)
from app.bookmarks.service import (
    BOOKMARK_LIMIT,
    create_bookmark,
    delete_bookmark,
    get_bookmark_count,
    get_bookmark_owner,
    list_bookmarks,
)

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post("", response_model=BookmarkResponse, status_code=201)
def create_bookmark_endpoint(
    body: BookmarkCreate,
    user_id: str = Depends(get_current_user_id),
) -> BookmarkResponse | JSONResponse:
    """Save a bookmark linking the authenticated user to a transcript chunk.

    Enforces a maximum of 100 bookmarks per user. Returns the new
    bookmark with full chunk data and episode metadata.
    """
    count = get_bookmark_count(user_id)
    if count >= BOOKMARK_LIMIT:
        return JSONResponse(
            status_code=400,
            content={
                "detail": (
                    f"Bookmark limit reached. You can save a maximum of "
                    f"{BOOKMARK_LIMIT} bookmarks."
                )
            },
        )

    bookmark = create_bookmark(user_id=user_id, chunk_id=body.chunk_id)
    return bookmark


@router.get("", response_model=BookmarkListResponse)
def list_bookmarks_endpoint(
    user_id: str = Depends(get_current_user_id),
) -> BookmarkListResponse:
    """Retrieve all bookmarks for the authenticated user.

    Returns bookmarks with full chunk text, speaker label, timestamps,
    and episode metadata so the frontend can render bookmark cards.
    """
    bookmarks = list_bookmarks(user_id)
    return BookmarkListResponse(bookmarks=bookmarks)


@router.delete("/{bookmark_id}")
def delete_bookmark_endpoint(
    bookmark_id: str = Path(..., description="UUID of the bookmark to delete"),
    user_id: str = Depends(get_current_user_id),
) -> JSONResponse:
    """Delete a bookmark owned by the authenticated user.

    Returns 403 if the bookmark belongs to another user.
    Returns 404 if the bookmark does not exist.
    """
    owner = get_bookmark_owner(bookmark_id)
    if owner is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Bookmark not found."},
        )
    if owner != user_id:
        return JSONResponse(
            status_code=403,
            content={"detail": "You do not have permission to delete this bookmark."},
        )

    delete_bookmark(bookmark_id)
    return JSONResponse(
        status_code=200,
        content={"detail": "Bookmark deleted successfully."},
    )
