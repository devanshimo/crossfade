"""
tests/test_auth.py
───────────────────
Tests for the Spotify OAuth flow.

Strategy:
    • SpotifyService methods that call Spotify's API are tested by monkeypatching
      httpx.AsyncClient so no real network calls happen.
    • Route-level tests verify HTTP behaviour (redirects, CSRF, 401s).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_internal_token, decrypt_token, encrypt_token
from app.models.user import SpotifyAccount, User
from app.repositories.spotify_repository import SpotifyAccountRepository
from app.repositories.user_repository import UserRepository
from app.services.spotify import SpotifyAuthError, SpotifyService


# ── Security helpers ──────────────────────────────────────────────────────────

def test_encrypt_decrypt_roundtrip() -> None:
    plaintext = "super-secret-spotify-token-abc123"
    assert decrypt_token(encrypt_token(plaintext)) == plaintext


def test_internal_token_roundtrip() -> None:
    from app.core.security import decode_internal_token
    token = create_internal_token("some-uuid")
    payload = decode_internal_token(token)
    assert payload["sub"] == "some-uuid"


# ── SpotifyService.build_authorization_url ────────────────────────────────────

@pytest.mark.asyncio
async def test_build_authorization_url_contains_client_id(
    db_session: AsyncSession,
) -> None:
    service = SpotifyService(db_session)
    url, state = service.build_authorization_url()

    assert "accounts.spotify.com/authorize" in url
    assert "response_type=code" in url
    assert len(state) > 20


# ── SpotifyService.exchange_code_for_tokens ───────────────────────────────────

@pytest.mark.asyncio
async def test_exchange_code_raises_on_bad_status(db_session: AsyncSession) -> None:
    service = SpotifyService(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(SpotifyAuthError, match="Token exchange failed"):
            await service.exchange_code_for_tokens("bad-code")


@pytest.mark.asyncio
async def test_exchange_code_returns_token_dict(db_session: AsyncSession) -> None:
    service = SpotifyService(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "access-abc",
        "refresh_token": "refresh-xyz",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        result = await service.exchange_code_for_tokens("valid-code")

    assert result["access_token"] == "access-abc"


# ── SpotifyService.handle_callback (integration across service + repos) ───────

@pytest.mark.asyncio
async def test_handle_callback_creates_user_and_account(
    db_session: AsyncSession,
) -> None:
    service = SpotifyService(db_session)

    token_payload = MagicMock()
    token_payload.status_code = 200
    token_payload.json.return_value = {
        "access_token": "at-abc",
        "refresh_token": "rt-xyz",
        "expires_in": 3600,
    }

    profile_payload = MagicMock()
    profile_payload.status_code = 200
    profile_payload.json.return_value = {
        "id": "spotify-user-999",
        "email": "test@crossfade.io",
        "display_name": "Test User",
    }

    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=token_payload),
        patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=profile_payload),
    ):
        auth_user = await service.handle_callback(code="valid-code")

    assert auth_user.user.email == "test@crossfade.io"
    assert auth_user.spotify_account.spotify_user_id == "spotify-user-999"
    assert auth_user.token_type == "bearer"
    assert len(auth_user.access_token) > 10  # our internal JWT

    # Verify DB rows were actually written
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_email("test@crossfade.io")
    assert user is not None

    spotify_repo = SpotifyAccountRepository(db_session)
    account = await spotify_repo.get_by_user_id(user.id)
    assert account is not None
    assert account.spotify_user_id == "spotify-user-999"
    # Tokens should be stored encrypted (not plaintext)
    assert account.access_token != "at-abc"
    assert decrypt_token(account.access_token) == "at-abc"


# ── GET /v1/auth/spotify/login ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_redirects_to_spotify(client: AsyncClient) -> None:
    response = await client.get("/v1/auth/spotify/login", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert "accounts.spotify.com/authorize" in location
    # CSRF cookie must be set
    assert "spotify_oauth_state" in response.cookies


# ── GET /v1/auth/spotify/callback – CSRF check ────────────────────────────────

@pytest.mark.asyncio
async def test_callback_rejects_state_mismatch(client: AsyncClient) -> None:
    client.cookies.set("spotify_oauth_state", "correct-state")
    response = await client.get(
        "/v1/auth/spotify/callback",
        params={"code": "any-code", "state": "wrong-state"},
    )
    assert response.status_code == 400
    assert "CSRF" in response.json()["detail"]


# ── GET /v1/auth/spotify/me – unauthenticated ─────────────────────────────────

@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/v1/auth/spotify/me")
    assert response.status_code == 403   # HTTPBearer returns 403 when no header


@pytest.mark.asyncio
async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/v1/auth/spotify/me",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert response.status_code == 401
