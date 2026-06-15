"""
app/services/spotify.py
────────────────────────
Service layer: all Spotify OAuth business logic.

Why it exists:
    Route handlers should be thin – they parse HTTP, call a service, and
    serialise the response.  This service owns the multi-step OAuth dance,
    token storage, and profile fetching so none of that leaks into the router.

How it connects:
    • Called by api/v1/endpoints/auth.py.
    • Calls UserRepository + SpotifyAccountRepository for persistence.
    • Calls core/security.py for token encryption.
    • Uses httpx.AsyncClient for all Spotify HTTP calls.
"""

import base64
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import create_internal_token, decrypt_token, encrypt_token
from app.models.user import SpotifyAccount, User
from app.repositories.spotify_repository import SpotifyAccountRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import AuthenticatedUser, SpotifyAccountRead, SpotifyUserProfile, UserRead

logger = get_logger(__name__)
settings = get_settings()


class SpotifyAuthError(Exception):
    """Raised when any step of the Spotify OAuth flow fails."""


class SpotifyService:
    """
    Encapsulates the Spotify OAuth Authorization Code Flow.

    Instantiated per-request with a DB session so it participates in the
    request-scoped transaction managed by the `get_db` dependency.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._spotify_repo = SpotifyAccountRepository(session)

    # ── Step 1: Build the authorization URL ──────────────────────────────────

    def build_authorization_url(self) -> tuple[str, str]:
        """
        Return (authorization_url, state).

        The `state` parameter is a CSRF token.  The caller must store it in a
        short-lived cookie/session and verify it matches when the callback arrives.
        """
        state = secrets.token_urlsafe(32)
        params = {
            "response_type": "code",
            "client_id": settings.spotify_client_id,
            "scope": settings.spotify_scopes,
            "redirect_uri": settings.spotify_redirect_uri,
            "state": state,
            "show_dialog": "false",
        }
        url = f"{settings.spotify_auth_url}?{urlencode(params)}"
        logger.debug("built_spotify_auth_url", url=url)
        return url, state

    # ── Step 2: Exchange code for tokens ─────────────────────────────────────

    async def exchange_code_for_tokens(self, code: str) -> dict[str, str]:
        """
        POST to Spotify's token endpoint, return the raw token response dict.
        Raises SpotifyAuthError on any HTTP or API error.
        """
        credentials = base64.b64encode(
            f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.spotify_token_url,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.spotify_redirect_uri,
                },
                timeout=10.0,
            )

        if response.status_code != 200:
            logger.error(
                "spotify_token_exchange_failed",
                status=response.status_code,
                body=response.text,
            )
            raise SpotifyAuthError(
                f"Token exchange failed: {response.status_code} {response.text}"
            )

        return response.json()  # type: ignore[no-any-return]

    # ── Step 3: Fetch Spotify user profile ───────────────────────────────────

    async def fetch_spotify_profile(self, access_token: str) -> SpotifyUserProfile:
        """Call GET /v1/me and return a typed profile object."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.spotify_api_base}/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )

        if response.status_code != 200:
            logger.error(
                "spotify_profile_fetch_failed",
                status=response.status_code,
                body=response.text,
            )
            raise SpotifyAuthError(
                f"Profile fetch failed: {response.status_code} {response.text}"
            )

        data = response.json()
        return SpotifyUserProfile(
            id=data["id"],
            email=data.get("email", ""),
            display_name=data.get("display_name"),
        )

    # ── Step 4: Persist user + tokens ────────────────────────────────────────

    async def handle_callback(self, code: str) -> AuthenticatedUser:
        """
        Full OAuth callback handler: token exchange → profile fetch → DB upsert.

        Returns an AuthenticatedUser containing our own internal JWT (not the
        Spotify token) so the frontend can use it for subsequent Crossfade API calls.
        """
        # 4a. Exchange code
        token_data = await self.exchange_code_for_tokens(code)
        

        raw_access_token: str = token_data["access_token"]
        raw_refresh_token: str = token_data["refresh_token"]
        expires_in: int = int(token_data.get("expires_in", 3600))
        token_expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)

        # 4b. Fetch Spotify profile
        profile = await self.fetch_spotify_profile(raw_access_token)
        logger.info("spotify_profile_fetched", spotify_user_id=profile.id)

        # 4c. Upsert Crossfade user
        user, created = await self._user_repo.get_or_create(email=profile.email,display_name=profile.display_name,)
        if created:
            logger.info("user_created", user_id=str(user.id))
        else:
            logger.info("user_found", user_id=str(user.id))

        # 4d. Encrypt and upsert Spotify account
        account = await self._spotify_repo.upsert(
            user_id=user.id,
            spotify_user_id=profile.id,
            access_token=encrypt_token(raw_access_token),
            refresh_token=encrypt_token(raw_refresh_token),
            token_expiry=token_expiry,
        )

        # 4e. Issue our own internal JWT
        internal_jwt = create_internal_token(subject=str(user.id))

        return self._build_auth_response(user, account, internal_jwt)

    # ── Helper: read current user's Spotify account ──────────────────────────

    async def get_authenticated_user(self, user: User) -> AuthenticatedUser:
        """
        Load the SpotifyAccount for an already-authenticated user and wrap it.
        Called by GET /auth/spotify/me.
        """
        account = await self._spotify_repo.get_by_user_id(user.id)
        if account is None:
            raise SpotifyAuthError("No Spotify account linked for this user")

        internal_jwt = create_internal_token(subject=str(user.id))
        return self._build_auth_response(user, account, internal_jwt)
     # ── Helper: read current user's Spotify playlists ──────────────────────────
    async def get_current_user_playlists(
        self,
        user: User,
        limit: int = 50,
    ) -> list[dict]:
        spotify_account = await self._spotify_repo.get_by_user_id(user.id)
        if spotify_account is None:
            raise SpotifyAuthError("No linked Spotify account found")

        access_token = decrypt_token(spotify_account.access_token)

        playlists: list[dict] = []
        url = f"{settings.spotify_api_base}/me/playlists"
        params = {"limit": limit, "offset": 0}

        async with httpx.AsyncClient() as client:
            while url:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params if "?" not in url else None,
                )

                if response.status_code != 200:
                    raise SpotifyAuthError(
                        f"Failed to fetch playlists: {response.status_code} {response.text}"
                    )

                data = response.json()
                playlists.extend(data.get("items", []))
                url = data.get("next")
                params = None

        return playlists


    async def get_playlist(
        self,
        user: User,
        spotify_playlist_id: str,
    ) -> dict:
        spotify_account = await self._spotify_repo.get_by_user_id(user.id)
        if spotify_account is None:
            raise SpotifyAuthError("No linked Spotify account found")

        access_token = decrypt_token(spotify_account.access_token)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.spotify_api_base}/playlists/{spotify_playlist_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                
    

                #params={"fields": "id,name,description,snapshot_id"},
            )
            

        if response.status_code != 200:
            raise SpotifyAuthError(
                f"Failed to fetch playlist: {response.status_code} {response.text}"
            )
        data = response.json()


        return data
        


    async def get_playlist_tracks(
        self,
        user: User,
        spotify_playlist_id: str,
        limit: int = 100,
    ) -> list[dict]:
        spotify_account = await self._spotify_repo.get_by_user_id(user.id)
        if spotify_account is None:
            raise SpotifyAuthError("No linked Spotify account found")
        

        access_token = decrypt_token(spotify_account.access_token)

        items: list[dict] = []
        
        url =f"{settings.spotify_api_base}/playlists/{spotify_playlist_id}/tracks"
        params = {
            "limit": limit,
            "offset": 0,
            #"fields": (
                #"items(added_at,added_by.id,"
                #"track(id,name,duration_ms,artists(name),album(name))),next"
            #),
        }

        async with httpx.AsyncClient() as client:
            while url:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params if "?" not in url else None,
                )

                me_response = await client.get(
                f"{settings.spotify_api_base}/me",
                headers={"Authorization": f"Bearer {access_token}"}
)

                if response.status_code != 200:
                    raise SpotifyAuthError(
                        f"Failed to fetch playlist tracks: {response.status_code} {response.text}"
                    )

                data = response.json()
                items.extend(data.get("items", []))
                url = data.get("next")
                params = None

        return items


    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_auth_response(
        user: User, account: SpotifyAccount, internal_jwt: str
    ) -> AuthenticatedUser:
        return AuthenticatedUser(
            user=UserRead.model_validate(user),
            spotify_account=SpotifyAccountRead.model_validate(account),
            access_token=internal_jwt,
        )
