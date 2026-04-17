# Technical Architecture: Brain Training App

**Version:** 1.0
**Date:** 2026-04-16
**Mirrors:** spec-v0.8

---

## 1. Stack Summary

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React 18 + Vite | Component model well-suited to exercise UI; Vite gives fast dev loop |
| Backend | FastAPI (Python 3.11) | Async support, automatic OpenAPI docs, concise route definitions |
| Database | PostgreSQL 18 (Railway managed) | Relational model fits user/session/attempt structure; managed = no ops overhead |
| Testing (frontend) | Vitest + jsdom + @testing-library/react | Lightweight, co-located with Vite config |
| Testing (backend) | pytest + httpx TestClient | Standard Python test stack; TestClient gives full route coverage |
| Deployment | Railway | Single platform for frontend (static), backend (service), and database |
| CI/CD | GitHub Actions | Nightly feedback pipeline + PR-gated tests |

---

## 2. Repository Structure

```
apps/brain-training/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── models/
│   │   └── models.py              # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── schemas.py             # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py                # /api/auth/*
│   │   ├── sessions.py            # /api/sessions/*
│   │   ├── progress.py            # /api/progress/*
│   │   ├── lifestyle.py           # /api/lifestyle/*
│   │   └── feedback.py            # /api/feedback
│   ├── services/
│   │   ├── adaptive_difficulty.py # 2-up/1-down staircase algorithm
│   │   └── brain_health_score.py  # BHS calculation (60% cognitive, 40% lifestyle)
│   └── tests/
│       └── test_*.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── exercises/         # GoNoGo, Stroop, CardMemory, DigitSpan, Baseline
│   │   │   ├── nav/               # Sidebar, BottomNav
│   │   │   └── ui/                # Button, Card, ProgressBar, FeedbackWidget
│   │   ├── pages/                 # Dashboard, Session, Onboarding, SessionSummary, etc.
│   │   ├── hooks/                 # useAuth, useSession, useProgress
│   │   ├── utils/                 # scoring.js, api.js (axios instance)
│   │   ├── styles/
│   │   │   ├── variables.css      # All CSS custom properties (tokens)
│   │   │   └── components.css     # Layout and responsive rules
│   │   └── test/                  # *.test.jsx / *.test.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── feedback_agent/
│   ├── pipeline.py                # Nightly orchestration script
│   ├── synthesizer.py             # Claude synthesis stage
│   ├── implementer.py             # Claude implementation stage
│   ├── test_updater.py            # Claude test sync stage
│   ├── pipeline_reviewer.py       # Weekly self-improvement stage
│   ├── git_helper.py              # Branch/commit/push/PR helpers
│   ├── github_issues.py           # Issue creation/closure
│   ├── spec_updater.py            # spec.md version bump
│   ├── db.py                      # PostgreSQL feedback DB helpers
│   ├── json_utils.py              # Robust JSON extraction from Claude responses
│   └── prompts/                   # Markdown prompt templates
│       ├── synthesis.md
│       ├── implementation.md
│       ├── test_update.md
│       ├── test_fix.md
│       └── pipeline_review.md
├── docs/                          # This folder — project documentation
├── agent-config.json              # Agent Central project config
└── spec.md                        # Legacy spec (source of truth until fully migrated to docs/)
```

---

## 3. Database Schema

### users
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| email | TEXT | UNIQUE, NOT NULL |
| password_hash | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### sessions
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| session_type | TEXT | 'training' \| 'baseline' \| 'free_play' |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |
| duration_seconds | INTEGER | |
| domains_trained | JSONB | Array of domain names |

### exercise_attempts
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| session_id | UUID | FK → sessions.id |
| user_id | UUID | FK → users.id |
| exercise_type | TEXT | e.g. 'stroop', 'gonogo', 'digit_span' |
| domain | TEXT | e.g. 'processing_speed' |
| difficulty | INTEGER | 1–10 |
| score | DECIMAL | 0–100 |
| trials_presented | INTEGER | |
| trials_correct | INTEGER | |
| avg_response_ms | INTEGER | |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### domain_progress
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, UNIQUE with domain |
| domain | TEXT | |
| current_score | DECIMAL | 0–100 |
| current_difficulty | INTEGER | 1–10 |
| sessions_count | INTEGER | |
| last_updated | TIMESTAMPTZ | |

### baseline_results
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| domain | TEXT | |
| score | DECIMAL | |
| difficulty_seeded | INTEGER | |
| completed_at | TIMESTAMPTZ | |

### lifestyle_logs
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| date | DATE | |
| exercise_minutes | INTEGER | |
| sleep_hours | DECIMAL | |
| sleep_quality | INTEGER | 1–5 |
| stress_level | INTEGER | 1–5 |
| mood | INTEGER | 1–5 |
| social_engagement | BOOLEAN | |

### streaks
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, UNIQUE |
| current_streak | INTEGER | |
| longest_streak | INTEGER | |
| last_session_date | DATE | |

### feedback_entries
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, nullable |
| session_id | UUID | FK → sessions.id, nullable |
| page_context | TEXT | |
| feedback_text | TEXT | max 1000 chars |
| processed | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### feedback_runs
| Column | Type | Constraints |
|---|---|---|
| id | SERIAL | PK |
| run_at | TIMESTAMPTZ | DEFAULT NOW() |
| status | TEXT | 'pending'\|'completed'\|'tests_failed'\|'error' |
| feedback_count | INTEGER | |
| themes | JSONB | Synthesised change items |
| changes_applied | JSONB | |
| branch_name | TEXT | |
| pr_url | TEXT | |
| error | TEXT | |

---

## 4. API Design

### Authentication

JWT tokens, dual-stored in:
- `httpOnly` cookie (set via `Set-Cookie` header, `SameSite=None;Secure` for Railway cross-origin)
- `localStorage` (for axios Bearer header injection)

Token sent as `Authorization: Bearer <token>` on every request via axios interceptor. On 401, `localStorage` token cleared and user redirected to login.

### Base URL

`/api` (Railway backend service URL in production, `http://localhost:8000` in dev)

### Key Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | No | Create account with consent checkbox |
| POST | /api/auth/login | No | Return JWT + set cookie |
| POST | /api/auth/logout | Yes | Clear cookie |
| GET | /api/progress | Yes | All domain progress for current user |
| POST | /api/sessions | Yes | Start session |
| PATCH | /api/sessions/{id} | Yes | Update / complete session |
| POST | /api/sessions/{id}/attempts | Yes | Log exercise attempt |
| GET | /api/sessions/{id}/summary | Yes | Post-session summary data |
| GET | /api/baseline | Yes | Current baseline results |
| POST | /api/baseline | Yes | Submit baseline attempt |
| GET | /api/lifestyle | Yes | Recent lifestyle logs |
| POST | /api/lifestyle | Yes | Submit lifestyle log |
| GET | /api/feedback | No* | Export feedback for pipeline (*internal use, no auth in dev) |
| POST | /api/feedback | No | Submit user feedback |

---

## 5. Agent Communication

| Agent | Reads from | Writes to |
|---|---|---|
| feedback_agent | `feedback_entries` table (PostgreSQL) | Source files on disk, `feedback_runs` table |
| build_agent | `docs/`, codebase files | Updated source files |
| testing_agent | Source files, test files | Updated test files |
| code_audit_agent | Source files | Supabase `code_audit_findings` |

`agent-config.json` is read by the Agent Central orchestrator at the start of each run.

The existing `feedback_agent/pipeline.py` runs nightly via GitHub Actions and handles the full feedback → synthesise → implement → test → PR loop autonomously. It will be progressively migrated to use agent definitions loaded from Supabase.

---

## 6. Deployment Architecture

```
GitHub (james-jxr/app-dev-capability)
    ↓ push to main
Railway
    ├── Frontend — static Vite build
    │     URL: brain-training.up.railway.app (or custom domain)
    └── Backend — FastAPI via uvicorn
          URL: brain-training-api.up.railway.app
          └── PostgreSQL (Railway managed, same project)

GitHub Actions (.github/workflows/nightly-feedback.yml)
    ↓ nightly cron + manual trigger
    Runs feedback_agent/pipeline.py
    → Opens PR to main on success
```

### Environment variables

| Variable | Service | Description |
|---|---|---|
| `DATABASE_URL` | Backend + pipeline | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | Pipeline | Claude API key |
| `GITHUB_TOKEN` | Pipeline | GitHub token for PR/issue management |
| `GITHUB_REPOSITORY` | Pipeline | `james-jxr/app-dev-capability` |
| `SUPABASE_URL` | Orchestrator | Agent Central Supabase URL |
| `SUPABASE_SERVICE_KEY` | Orchestrator | Supabase service role key |

---

## 7. CI/CD Pipeline

### Nightly feedback pipeline (GitHub Actions)

Workflow: `.github/workflows/nightly-feedback.yml`

Steps:
1. Fetch unprocessed feedback from PostgreSQL
2. Check GitHub for `ready-to-implement` issues
3. Synthesise feedback → change items (Claude Opus)
4. Create GitHub Issues for non-implementable items
5. Implement change items (write source files, Claude Opus)
6. Update test files (Claude Sonnet)
7. Run full test suite — auto-fix up to 3 iterations (Claude Sonnet)
8. Update spec.md version
9. Commit → push feature branch → open PR
10. Close implemented GitHub Issues
11. Mark feedback as processed

### Test commands

```bash
# Backend
DATABASE_URL=sqlite:////tmp/test.db pytest backend/tests/ -q

# Frontend (from frontend/)
npm test -- --run
```

---

## 8. Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Auth token storage | httpOnly cookie + localStorage | Cookie for security; localStorage for axios header injection with cross-origin Railway domains |
| JSON extraction from Claude | Three-strategy extractor (json_utils.py) | Claude Opus 4.6 does not support assistant prefill; responses often contain preamble prose |
| Test style | Pure function exports preferred | Component rendering tests timeout when async delays are present; pure functions never timeout |
| Adaptive difficulty | 2-up/1-down staircase | Well-validated psychophysics algorithm targeting ~70% success rate |

---

## 9. Known Limitations

- Symbol matching task hidden pending replacement with a new processing speed variant
- Executive Function and Episodic Memory domains not yet implemented (v1.1)
- `GET /api/feedback` has no authentication — acceptable for internal pipeline use, should be secured before any public-facing deployment
- `feedback_agent/pipeline.py` is project-specific code; will be replaced by the Agent Central orchestrator in a future migration
