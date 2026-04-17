# Brain Training

A scientifically-designed cognitive training application that helps users strengthen their mental abilities through adaptive exercises.

## Requirements

- Python 3.11–3.13 (Python 3.14 is not supported — see Notes)
- Node.js 18+ with npm

## Backend Setup

All backend commands must be run from the `brain-training/` directory (not from inside `backend/`).

### 1. Create and activate a virtual environment

```bash
~/.pyenv/versions/3.13.3/bin/python3 -m venv backend/venv
source backend/venv/bin/activate
```

If you are not using pyenv, replace the first line with whichever Python 3.11–3.13 binary you have:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | JWT signing secret — use a long random string | **required** |
| `DATABASE_URL` | SQLite path — must be on local filesystem | `sqlite:////tmp/brain_training.db` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes | `1440` |

To generate a suitable `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run the backend

```bash
DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive API docs (Swagger UI): `http://localhost:8000/docs`

**Important:** Always use `python -m uvicorn`, not bare `uvicorn`. On macOS with Homebrew, the bare command resolves to a system-level binary and will fail with `ModuleNotFoundError`.

---

## Frontend Setup

From the `brain-training/` directory:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Running Tests

From the `brain-training/` directory, with the venv active:

```bash
source backend/venv/bin/activate
DATABASE_URL="sqlite:////tmp/brain_training_test.db" python -m pytest backend/tests/ -v
```

**Important:** Always use `python -m pytest`, not bare `pytest`, for the same reason as uvicorn above.

---

## Features

- **Three Cognitive Domains:** Processing Speed, Working Memory, Attention
- **Six Exercise Types:** Symbol Matching, Visual Categorisation, N-Back, Digit Span, Go/No-Go, Stroop
- **Adaptive Difficulty:** Adjusts per domain to maintain 70–80% success rate (difficulty 1–10)
- **Baseline Assessment:** Repeatable every 6 months; original baseline retained for long-term comparison
- **Brain Health Score:** 0–100 composite score (60% cognitive average, 40% lifestyle)
- **Progress Dashboard:** Per-domain scores, 30-day trend, streak, Brain Health Score
- **Lifestyle Logging:** Daily log of exercise, sleep, sleep quality, stress, mood, social engagement
- **Streak Tracking:** 36-hour window; longest streak recorded

---

## API Endpoints

### Authentication
| Method | Path | Auth |
|---|---|---|
| POST | `/api/auth/register` | No |
| POST | `/api/auth/login` | No |
| POST | `/api/auth/logout` | Yes |
| GET | `/api/auth/me` | Yes |

### Baseline Assessment
| Method | Path | Auth |
|---|---|---|
| POST | `/api/baseline/start` | Yes |
| POST | `/api/baseline/submit` | Yes |
| GET | `/api/baseline/next-eligible-date` | Yes |

### Training Sessions
| Method | Path | Auth |
|---|---|---|
| POST | `/api/sessions/start` | Yes |
| GET | `/api/sessions/{id}/next` | Yes |
| POST | `/api/sessions/{id}/exercise-result` | Yes |
| POST | `/api/sessions/{id}/complete` | Yes |
| GET | `/api/sessions/{id}` | Yes |
| GET | `/api/sessions` | Yes |
| POST | `/api/sessions/plan-next` | Yes |

### Progress & Dashboard
| Method | Path | Auth |
|---|---|---|
| GET | `/api/progress/dashboard` | Yes |
| GET | `/api/progress/summary` | Yes |
| GET | `/api/progress/brain-health` | Yes |
| GET | `/api/progress/streak` | Yes |
| GET | `/api/progress/domain/{domain}` | Yes |
| GET | `/api/progress/trend/{domain}` | Yes |

### Lifestyle Logging
| Method | Path | Auth |
|---|---|---|
| POST | `/api/lifestyle/log` | Yes |
| GET | `/api/lifestyle/today` | Yes |
| GET | `/api/lifestyle/history` | Yes |

### Account
| Method | Path | Auth |
|---|---|---|
| GET | `/api/account/profile` | Yes |
| PATCH | `/api/account/account` | Yes |
| DELETE | `/api/account/account` | Yes |

---

## Project Structure

```
brain-training/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Database configuration
│   ├── security.py          # JWT auth utilities
│   ├── requirements.txt     # Python dependencies
│   ├── pytest.ini           # Test configuration
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── routers/             # API route handlers
│   └── tests/               # Test suite (24 tests)
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── pages/           # Page components
    │   ├── hooks/           # Custom React hooks
    │   ├── api/             # API client
    │   ├── styles/          # CSS design system
    │   ├── App.jsx
    │   └── main.jsx
    └── package.json
```

---

## Notes

- **Python 3.14 is not supported.** The `pydantic-core` package uses PyO3 bindings that do not yet support CPython 3.14. Use Python 3.11, 3.12, or 3.13.
- JWT tokens are stored in httpOnly cookies. The API also returns the token in the response body for API client use (e.g. Swagger UI).
- SQLite database files must be on a local filesystem — network-mounted paths will cause disk I/O errors. The `DATABASE_URL` env var controls this.
- Executive Function and Episodic Memory domains are deferred to v1.1. v1 covers Processing Speed, Working Memory, and Attention only.
- Password reset via email is not yet implemented (requires SMTP configuration).
- The About the Science page is not yet implemented.

## License

Proprietary — All rights reserved
