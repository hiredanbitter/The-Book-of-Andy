"""FastAPI router for episode endpoints."""

from fastapi import APIRouter, Path
from fastapi.responses import JSONResponse

from app.episodes.schemas import TranscriptResponse
from app.episodes.service import get_episode_transcript

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.get("/{episode_id}/transcript", response_model=TranscriptResponse)
def episode_transcript(
    episode_id: str = Path(..., description="UUID of the episode"),
) -> TranscriptResponse | JSONResponse:
    """Return the full transcript for an episode.

    Fetches episode metadata (podcast name, title, episode number,
    publication date, description) and all transcript chunks in
    chronological order.

    Returns 404 if the episode does not exist.
    """
    result = get_episode_transcript(episode_id)
    if result is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Episode not found."},
        )
    return result
