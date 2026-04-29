# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Frontend:** React 18 + Vite 5, React Router v6, Axios, Vitest + jsdom, ESLint — plain JSX (no TypeScript)
- **Backend:** FastAPI (Python 3.11–3.13), SQLAlchemy 2.0, Pydantic v2, JWT via python-jose + bcrypt
- **Database:** SQLite locally, PostgreSQL on Railway (production)
- **Deployment:** Railway (backend + DB), Vite static build (frontend)

**Python 3.14 is not supported** — `pydantic-core` PyO3 bindings don't support CPython 3.14. Use 3.11–3.13.

## Commands

All backend commands run from `brain-training/` (not from inside `backend/`).

### Backend

```bash
# First-time setup
~/.pyenv/versions/3.13.3/bin/python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # then set SECRET_KEY

# Run (venv must be active)
DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload
# → http://localhost:8000  |  Swagger UI: http://localhost:8000/docs
```

Always use `python -m uvicorn` (not bare `uvicorn`) and `python -m pytest` (not bare `pytest`) — on macOS the bare commands resolve to system binaries that lack the venv packages.

### Frontend

```bash
cd frontend
npm install          # first time
cp .env.example .env # first time
npm run dev          # → http://localhost:5173
npm run build        # production build → dist/
npm run lint         # ESLint
```

### Tests

```bash
# Backend (from brain-training/, venv active)
# Note: conftest.py overrides DATABASE_URL to ./test.db regardless of env
# pytest.ini sets asyncio_mode=strict — async test functions need @pytest.mark.asyncio
DATABASE_URL="sqlite:////tmp/brain_training_test.db" python -m pytest backend/tests/ -v

# Run a single test file
DATABASE_URL="sqlite:////tmp/brain_training_test.db" python -m pytest backend/tests/test_auth.py -v

# Frontend
cd frontend && npm run test          # single run
cd frontend && npm run test:watch    # watch mode
```

## Architecture

### Request Flow

```
Browser (React + Vite)
  ↓ /api/* proxied to http://localhost:8000 (dev)
FastAPI (backend/main.py)
  ↓ JWT middleware (backend/security.py)
  ↓ 8 routers → services (business logic) → SQLAlchemy ORM
SQLite / PostgreSQL
```

The Vite dev server proxy (`vite.config.js`) forwards `/api/*` to `localhost:8000`, so the frontend calls relative `/api/` paths. In production the frontend build is served separately; the backend URL is set via `VITE_API_URL`.

### Authentication

JWT tokens are stored in both **httpOnly cookies** (browser security) and returned in the response body for direct API use (Swagger, etc.). The frontend stores the token in `sessionStorage` and attaches it via `useAuth` context (`src/hooks/useAuth.jsx`). All authenticated endpoints call `get_current_user` which decodes the JWT from the cookie.

### Key Backend Modules

| Path | Purpose |
|---|---|
| `backend/main.py` | FastAPI app, router registration, CORS, `init_db()` call |
| `backend/database.py` | SQLAlchemy engine, `Base`, `SessionLocal`, `init_db()` |
| `backend/security.py` | `create_access_token`, `get_current_user` dependency |
| `backend/schemas/` | Pydantic v2 request/response schemas for all 8 routers |
| `backend/services/adaptive_difficulty.py` | Staircase difficulty: >80% success → +1, <50% → −1 (scale 1–10) |
| `backend/services/session_planner.py` | Builds sessions from 2–3 domains, ≥2 exercise variants per domain |
| `backend/services/brain_health_score.py` | Composite score: 60% cognitive average + 40% lifestyle |
| `backend/services/streak_manager.py` | 36-hour streak window, UTC datetimes |
| `backend/services/exercise_generator.py` | Generates per-difficulty exercise payloads (symbol matching, visual categorisation) |

There are 8 routers: `auth`, `baseline`, `adaptive_baseline`, `sessions`, `progress`, `lifestyle`, `account`, `feedback`.

### Key Frontend Modules

| Path | Purpose |
|---|---|
| `src/App.jsx` | Router setup, `AuthProvider` wrapping, `AppRoutes` (public vs. authenticated routing) |
| `src/hooks/useAuth.jsx` | Global auth state, login/logout, token management |
| `src/api/client.js` | Axios instance; exports `authAPI`, domain-specific API objects |
| `src/components/exercises/` | 6 exercise components (see below) |
| `src/hooks/useDashboard.js` | Dashboard data fetching |
| `src/hooks/useSession.js` | Session state management |
| `src/hooks/useStreakData.js` | Streak data fetching |
| `src/hooks/useGameHistory.js` | Per-exercise history |
| `src/components/ui/FeedbackWidget.jsx` | Floating feedback button — overlaid on all authenticated pages |
| `src/components/ui/PostGameFeedback.jsx` | Optional post-session feedback modal (in `SessionSummary`) |

### Cognitive Domains & Exercises

| Domain | Exercises |
|---|---|
| Processing Speed | `CardMemoryGame.jsx` |
| Working Memory | `NBack.jsx`, `DigitSpan.jsx` |
| Attention | `GoNoGo.jsx`, `Stroop.jsx`, `VisualCategorisation.jsx` |

Executive Function and Episodic Memory are deferred to v1.1. `SymbolMatching.jsx` is hidden (replacement pending).

### Database Models

Ten SQLAlchemy models under `backend/models/`: `User`, `Session`, `ExerciseAttempt`, `DomainProgress`, `LifestyleLog`, `Streak`, `SkillAssessment`, `BaselineResult`, `FeedbackEntry`, `FeedbackRun`. Models use cascade delete. All tables are auto-created via `init_db()` on startup.

### Feedback System

Two entry points capture free-text user feedback (auth required):
1. `FeedbackWidget` — persistent floating button on all authenticated pages
2. `PostGameFeedback` — optional modal shown in `SessionSummary`

Both POST to `/api/feedback`. The export endpoint `GET /api/feedback` is restricted to emails listed in the `ADMIN_EMAILS` env var.

## Environment Variables

**Backend (`backend/.env`):**
- `SECRET_KEY` — JWT signing secret (required; generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- `DATABASE_URL` — SQLite path must be local filesystem (network mounts cause I/O errors)
- `ALGORITHM` — JWT algorithm (default `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` — token lifetime (default `1440`)
- `FRONTEND_URL` — used for CORS in production
- `ADMIN_EMAILS` — comma-separated emails allowed to call the feedback export endpoint

**Frontend (`frontend/.env`):**
- `VITE_API_URL` — backend URL (not needed in dev; Vite proxy handles it)

## Feedback Agent Pipeline

`feedback_agent/` contains an autonomous Claude-powered pipeline that runs outside the app:

- **`review_pipeline.py`** — fetches unprocessed user feedback + Supabase audit findings, classifies them, and creates/updates GitHub issues. Run this first.
- **`implementation_pipeline.py`** — fetches open `ready-to-implement` GitHub issues, implements each one via Claude API, runs tests, updates `spec.md`, commits, pushes, and opens a PR.

Both scripts require additional env vars beyond the backend `.env`: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`. They load from `backend/.env` automatically.

```bash
# Install pipeline dependencies (separate from backend venv)
pip install -r feedback_agent/requirements.txt

# Dry run (no code written, no PRs opened)
DRY_RUN=1 python -m feedback_agent.implementation_pipeline
```

`agent-config.json` at the repo root defines which Claude agents are active and maps to design docs under `docs/` (`product-brief.md`, `functional-spec.md`, `design-guide.md`, `technical-architecture.md`).
