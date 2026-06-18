"""
app/api/v1/router.py
─────────────────────
Aggregates all v1 endpoint routers into a single APIRouter.

Why it exists:
    Centralising includes here means main.py stays clean as the API grows.
    Adding a new resource (e.g. playlists) is a single `include_router` line.

How it connects:
    • Included by main.py under the /v1 prefix.
    • Imports each endpoint module's `router` object.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.api.v1.endpoints import playlist
from app.api.v1.endpoints import apple_music
from app.api.v1.endpoints import sync_jobs



api_router = APIRouter(prefix="/v1")

api_router.include_router(auth.router)
api_router.include_router(playlist.router)
api_router.include_router(apple_music.router)
api_router.include_router(sync_jobs.router)
