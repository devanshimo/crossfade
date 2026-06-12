# Crossfade

Crossfade is a playlist synchronization platform that keeps playlists in sync across music streaming services.

The long-term goal is to allow users to connect platforms such as Spotify and Apple Music and automatically mirror playlist changes between them without manually recreating playlists.

## Current Status

🚧 Active Development

### Completed

* FastAPI backend setup
* Layered architecture (Routes → Services → Repositories → Database)
* Spotify OAuth Authorization Code Flow
* PostgreSQL integration
* SQLAlchemy ORM models
* Alembic migrations
* User and Spotify account persistence
* Playlist domain schema design

### In Progress

* Spotify profile retrieval
* Playlist import pipeline
* Playlist synchronization engine

---

## Architecture

```text
Client
   │
   ▼
FastAPI Routes
   │
   ▼
Services
(Business Logic)
   │
   ▼
Repositories
(Data Access)
   │
   ▼
PostgreSQL
```

### Backend Stack

* FastAPI
* PostgreSQL
* SQLAlchemy 2.0
* Alembic
* Pydantic v2
* httpx
* Spotify Web API
* Docker

---

## Database Design

Current core entities:

### User

Represents a Crossfade user.

### SpotifyAccount

Stores encrypted Spotify OAuth credentials linked to a user.

### Playlist

Stores imported playlist metadata.

### Track

Stores track metadata and identifiers.

### PlaylistTrack

Association entity that preserves playlist ordering and playlist-specific metadata.

---

## OAuth Flow

```text
User
 │
 ▼
Spotify Login
 │
 ▼
Authorization Code
 │
 ▼
Crossfade Backend
 │
 ▼
Access Token Exchange
 │
 ▼
Spotify API
```

Security measures:

* OAuth state validation
* Encrypted token storage
* Internal JWT authentication

---

## Project Roadmap

### Phase 1 — Authentication

* [x] Spotify OAuth
* [ ] Apple Music Authentication
* [ ] User session management

### Phase 2 — Playlist Import

* [ ] Fetch user playlists
* [ ] Import playlist metadata
* [ ] Import playlist tracks

### Phase 3 — Track Matching

* [ ] ISRC-based matching
* [ ] Metadata fallback matching
* [ ] Unresolved track handling

### Phase 4 — Synchronization

* [ ] Spotify → Apple Music sync
* [ ] Apple Music → Spotify sync
* [ ] Change detection
* [ ] Conflict resolution

### Phase 5 — Production

* [ ] Background workers
* [ ] Scheduled sync jobs
* [ ] Monitoring
* [ ] Deployment

---

## Local Development

### Clone Repository

```bash
git clone <repository-url>
cd crossfade/backend
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file:

```env
DATABASE_URL=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=
SECRET_KEY=
```

### Run Migrations

```bash
alembic upgrade head
```

### Start Server

```bash
uvicorn app.main:app --reload
```

---

## Learning Log

This project is being built as a public engineering journey and is documented day-by-day, including architectural decisions, debugging sessions, and implementation milestones.
