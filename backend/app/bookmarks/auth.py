"""Authentication dependency for bookmark endpoints.

Extracts and verifies the Supabase JWT from the Authorization header,
returning the authenticated user's ID.
"""

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

security = HTTPBearer()


def _get_supabase_client() -> Client:
    """Return a Supabase client configured from environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables "
            "must both be set."
        )
    return create_client(url, key)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
) -> str:
    """Extract and verify the user ID from a Supabase JWT.

    Uses the Supabase admin client to validate the token and retrieve
    the user. Returns the user's UUID string.

    Raises
    ------
    HTTPException (401)
        If the token is missing, invalid, or expired.
    """
    token = credentials.credentials
    client = _get_supabase_client()

    try:
        user_response = client.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc

    if user_response is None or user_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    return user_response.user.id
