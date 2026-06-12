"""
app/dependencies/auth.py
─────────────────────────
FastAPI dependency: resolve the current authenticated User from a JWT.

Why it exists:
    Route handlers that require an authenticated user declare
    `current_user: User = Depends(get_current_user)`.  All token-parsing and
    DB lookup logic lives here, not in the handler.

How it connects:
    • Used by api/v1/endpoints/auth.py  (GET /auth/spotify/me).
    • Future playlist/sync endpoints will also import `get_current_user`.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_internal_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT, look up the User, and return it.

    Raises HTTP 401 on any auth failure so callers don't need to handle it.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_internal_token(credentials.credentials)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user
