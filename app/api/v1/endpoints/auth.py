"""
app/api/v1/endpoints/auth.py
──────────────────────────────
Route handlers for Spotify OAuth.

Why it exists:
    Keeps HTTP concerns (request parsing, redirects, status codes) separate
    from business logic (which lives in SpotifyService).  Each handler is
    intentionally thin.

Endpoints:
    GET /auth/spotify/login     – redirect user to Spotify
    GET /auth/spotify/callback  – receive code, exchange for tokens
    GET /auth/spotify/me        – return current user info (requires auth)

How it connects:
    • Registered on the app router in api/v1/router.py.
    • Delegates all logic to SpotifyService.
    • Uses get_current_user dependency for protected routes.
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import AuthenticatedUser
from app.services.spotify import SpotifyAuthError, SpotifyService

logger = get_logger(__name__)
router = APIRouter(prefix="/auth/spotify", tags=["auth"])

_STATE_COOKIE = "spotify_oauth_state"


@router.get(
    "/login",
    summary="Initiate Spotify OAuth flow",
    description=(
        "Redirects the user to the Spotify authorization page. "
        "Sets a short-lived `spotify_oauth_state` cookie for CSRF protection."
    ),
    status_code=status.HTTP_302_FOUND,
)
async def spotify_login(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    service = SpotifyService(db)
    auth_url, state = service.build_authorization_url()

    logger.info("spotify_login_initiated")

    redirect = RedirectResponse(url=auth_url)
    redirect.set_cookie(
        key=_STATE_COOKIE,
        value=state,
        httponly=True,
        samesite="lax",
        secure=False,   # set True in production behind HTTPS
        max_age=300,    # 5 minutes – enough time to complete the OAuth dance
    )
    return redirect


@router.get(
    "/callback",
    response_model=AuthenticatedUser,
    summary="Handle Spotify OAuth callback",
    description=(
        "Receives the authorization `code` from Spotify, "
        "exchanges it for tokens, stores them, and returns an authenticated user."
    ),
)
async def spotify_callback(
    code: str = Query(..., description="Authorization code from Spotify"),
    state: str = Query(..., description="State value for CSRF verification"),
    stored_state: str | None = Cookie(None, alias=_STATE_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    # CSRF check
    if not stored_state or stored_state != state:
        logger.warning(
            "spotify_callback_state_mismatch",
            received=state,
            stored=stored_state,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state – possible CSRF attempt",
        )

    service = SpotifyService(db)
    try:
        auth_user = await service.handle_callback(code=code)
    except SpotifyAuthError as exc:
        logger.error("spotify_callback_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Spotify authentication failed: {exc}",
        ) from exc

    logger.info("spotify_callback_success", user_id=str(auth_user.user.id))
    return auth_user


@router.get(
    "/me",
    response_model=AuthenticatedUser,
    summary="Get current authenticated user",
    description="Returns the currently authenticated Crossfade user and their linked Spotify account.",
)
async def spotify_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthenticatedUser:
    service = SpotifyService(db)
    try:
        return await service.get_authenticated_user(current_user)
    except SpotifyAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc