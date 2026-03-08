"""Authentication dependency for bookmark endpoints.

Verifies the Supabase JWT locally using the project's public JWKS endpoint
(ES256) and extracts the authenticated user's ID from the token claims.
The JWKS response is cached so that the public key is fetched at most once
per ``JWKS_CACHE_TTL`` seconds, avoiding a network call on every request.
"""

import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

security = HTTPBearer()

# Default cache lifetime in seconds (5 minutes).
JWKS_CACHE_TTL = 300

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    """Return a cached ``PyJWKClient`` for the Supabase JWKS endpoint.

    The client is created lazily on first call and reused thereafter.
    ``PyJWKClient`` handles internal caching of the fetched key set;
    we set its ``lifespan`` to ``JWKS_CACHE_TTL`` so the keys are
    re-fetched only after that interval elapses.
    """
    global _jwks_client  # noqa: PLW0603
    if _jwks_client is None:
        url = os.environ.get("SUPABASE_URL", "")
        if not url:
            raise RuntimeError(
                "SUPABASE_URL environment variable must be set."
            )
        jwks_url = f"{url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=JWKS_CACHE_TTL)
    return _jwks_client


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
) -> str:
    """Extract and verify the user ID from a Supabase JWT.

    Fetches the signing key from the Supabase JWKS endpoint (cached),
    then decodes the token with ES256. Returns the user's UUID string
    from the ``sub`` claim.

    Raises
    ------
    HTTPException (401)
        If the token is missing, invalid, or expired.
    """
    token = credentials.credentials

    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    return user_id
