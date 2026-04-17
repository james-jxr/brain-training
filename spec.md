# App Specification: Brain Training App

**Spec Version:** spec-v0.9
**Date:** 2026-04-15
**Status:** Approved
**Brief Reference:** Functional Requirements v1.0 (March 2026) + Design System v1 + Feedback Brief feedback-v1.0

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| v0.1 | 2026-04-02 | Initial spec from Design Agent |
| v0.2 | 2026-04-03 | All open questions resolved and closed; status set to Approved |
| v0.3 | 2026-04-03 | Platform confirmed as web-first for v1; native mobile explicitly out of scope |
| v0.4 | 2026-04-03 | Reduced launch scope to 3 domains and 6 exercise types; 2 domains deferred to v1.1 |
| v0.5 | 2026-04-03 | Added in-app feedback capture feature: FeedbackEntry entity, POST /api/feedback route, FeedbackWidget (persistent on all authenticated pages), PostGameFeedback (optional modal on SessionSummary) |
| v0.6 | 2026-04-03 | Added GET /api/feedback export route for pipeline use; added reference to Feedback Synthesis prompt as named pipeline artefact |
| v0.7 | 2026-04-10 | Symbol matching hidden (pending replacement); visual_categorisation replaced with Shape Sort (abstract rule-induction); free-play mode added; autonomous feedback agent documented; baseline results now seed DomainProgress (BHS); adaptive baseline 2-up/1-down algorithm documented; cookie policy updated to SameSite=None;Secure for cross-origin deployment; deployment target updated to Railway; test infrastructure documented |
| v0.7 | 2026-04-11 | No spec changes — code diff empty; spec reflects current implementation state |
| v0.8 | 2026-04-14 | Card memory exercise extended to multi-round format (minimum 3 rounds); auth token now dual-stored in httpOnly cookie and localStorage for cross-origin compatibility; axios client sends Bearer token header on every request and clears localStorage on 401; logout clears localStorage token even on failure; SessionSummary score label renamed from "Overall Score" to "Accuracy" with correct/total trial count sub-label; auth cookie set_cookie/delete_cookie refactored to shared helper (path="/" added); scoring tests expanded |
| v0.8 | 2026-04-14 | Dashboard responsive layout: sidebar hidden on mobile, BottomNav shown, all grid columns stack to single-column, padding reduced; §12 Responsive Design added |
| v0.9 | 2026-04-15 | Stroop result computation extracted into exported pure function `computeStroopResult`; frontend test suite expanded with 7 new Stroop unit tests; §11c test counts updated |

---

> **Design Agent — Thinking Record**
>
> *Problem and user:* A science-grounded cognitive training app for ambitious adults 25–45. The core problem is that consumer brain-training apps either oversell their benefits (regulatory risk) or fail to sustain engagement long enough (20+ hours) to produce meaningful near-transfer gains. This app must solve both: evidence integrity and long-term adherence.
>
> *Minimum viable feature set:* User accounts → onboarding baseline assessment (all 5 domains) → daily training session (adaptive, interleaved, 15–20 min) → progress dashboard (per-domain scores + trends + Brain Health Score) → lifestyle habit logging → streak tracking → About the Science. Everything else is post-MVP.
>
> *Data the app needs to store:* Users, domain performance scores (per session, per exercise attempt), session records, lifestyle log entries, streak state, baseline assessment results.
>
> *Main screens:* Onboarding/baseline, Dashboard, Session (exercise screens per domain), Post-session summary, Lifestyle log, Progress detail, About the Science, Settings.
>
> *Explicit scope exclusions:* Social/leaderboard features, dual-task modules, audio/rhythm tasks, offline mode, Apple Health/Google Fit integration, notifications — all deferred to v2. The functional requirements explicitly exclude neurostimulation, EEG, AI dementia screening.
>
> *Genuine ambiguities:* (1) Platform target — the functional requirements say iOS & Android; the design system says cross-platform including web. Resolved: build a responsive web app (PWA-ready) using the CSS design system as specified. This is deployable to mobile via browser or wrapped later. (2) Specific exercise implementations — the requirements define domain categories and variability rules but not individual game mechanics. Resolved: define one concrete task variant per domain for MVP (minimum 2 per domain required by spec §3.2 — see §11). (3) Authentication — requirements mention GDPR/CCPA consent but not the auth mechanism. Resolved: email + password with explicit consent checkbox at registration.

---

## 1. Purpose & Problem Statement

The Brain Training App is a science-grounded cognitive training web application that helps adults build and sustain cognitive performance through daily, adaptive exercise sessions. Unlike consumer wellness apps that make unsupported claims, this app is built explicitly on peer-reviewed research, targets near-transfer gains (improvement on trained task types) as its honest promise, and is designed around the evidence that 20+ cumulative hours of sustained, varied, adaptive training is required before meaningful benefits emerge. The app exists to make that sustained commitment engaging enough to maintain. Version 1 is a web application (desktop and mobile browser); native iOS and Android apps are a future milestone once the core experience is validated with real users.

---

## 2. Target User

**Primary:** Ambitious professionals aged 25–45 who are motivated by evidence and self-improvement, comfortable with digital products, and willing to commit to a daily habit. They are not gamers seeking entertainment — they want to feel sharper and have the discipline to work for it. They read the footnotes. They will notice if claims are inflated.

**Secondary:** Adults aged 46–80 who are proactively managing cognitive health. The UI and difficulty calibration must support this cohort — font sizes, touch targets, and session pacing should accommodate older users without patronising the primary audience.

**Technical assumption:** Users access the app via a modern desktop or mobile browser (Chrome or Safari). No native app installation required. The app is built mobile-first and must be fully usable on a phone screen, but is not a native app.

---

## 3. User Stories

- As a new user, I want to complete a baseline cognitive assessment so that the app knows where I'm starting from and sets appropriate difficulty.
- As a returning user, I want to start a daily training session so that I can maintain my cognitive training streak.
- As a user mid-session, I want the exercises to adapt in difficulty as I improve so that I am always appropriately challenged.
- As a user completing a session, I want to see a summary of how I performed so that I understand my progress.
- As a user, I want to log my sleep, exercise, and stress each day so that the app can factor lifestyle into my Brain Health Score.
- As a user, I want to see my performance trend per cognitive domain over time so that I can track where I'm improving.
- As a user, I want to understand the science behind the app so that I can trust its claims and methodology.
- As a user, I want to control my notification preferences and account settings so that the app fits my routine.

---

## 4. MVP Feature List (In Scope)

1. **User registration and login** — email + password authentication with explicit GDPR/CCPA consent at registration. Password reset via email.
2. **Baseline assessment** — covers all five cognitive domains (Processing Speed, Working Memory, Attention & Inhibitory Control, Executive Function, Episodic Memory). Takes approximately 10 minutes. Results set adaptive difficulty starting points per domain. Completed once at onboarding, then repeatable every 6 months. Each re-baseline resets the current-period improvement reference and recalibrates difficulty; the original baseline is always retained for long-term comparison. The dashboard notifies users when they become eligible for re-baseline.
3. **Daily training session** — a guided 15–20 minute session covering exercises from 2–3 domains per session. Sessions are interleaved (not blocked on a single domain). Each session contains a minimum of 2 task variants per domain visited. On completion, the user sees a session summary screen.
4. **Adaptive difficulty per domain** — each domain tracks a rolling performance score (accuracy + speed) and adjusts task difficulty up or down to maintain a 70–80% success rate target. Difficulty cannot plateau — the system must continue to increase challenge for consistently high-performing users.
5. **Cognitive exercise library (v1 launch)** — two concrete task variants per domain across 3 domains at launch. Executive Function and Episodic Memory are deferred to v1.1. **Symbol matching is currently hidden** pending replacement with a new task variant (see §11 Q7):
   - *Processing Speed:* ~~Symbol matching task~~ *(hidden, replacement pending)*; Card memory task
   - *Working Memory:* N-back sequence task; digit span task
   - *Attention & Inhibitory Control:* Go/No-go reaction task; Stroop colour-word interference task
   - *All domains (baseline + free-play):* Shape Sort — abstract rule-induction task where users infer a sorting rule from examples (see §11a for design details)
6. **Post-session summary** — displayed after every session: domains trained, performance vs. previous session per domain, current streak, and a one-line science-grounded observation about their result. The summary displays the user's **Accuracy** score (labelled as such) with a sub-label showing correct trials out of total trials attempted (e.g. "7 correct out of 10 trials").
7. **Streak and consistency tracking** — daily streak counter visible on the dashboard and post-session screen. Streak resets if no session is completed within a 36-hour window (allowing for timezone flexibility). Total cumulative training time displayed prominently with a milestone marker at 20 hours.
8. **Progress dashboard** — the main logged-in home screen showing: current streak, cumulative training time, per-domain performance scores (separate, not collapsed), a 30-day trend graph per domain, Brain Health Score, and lifestyle summary.
9. **Brain Health Score** — a composite score (0–100) derived from cognitive performance across all five domains (60% weight) and lifestyle inputs (40% weight: exercise, sleep, stress, mood). Recalculated after each session and after each lifestyle log entry. Score is accompanied by a breakdown showing the contribution of each factor.
10. **Lifestyle habit logging** — a daily log capturing five lifestyle factors: physical activity (minutes of aerobic exercise), sleep (hours + quality rating 1–5), social engagement (yes/no interaction today), stress level (1–5), and mood (1–5). Accessible from the dashboard. Users are prompted to log after each training session.
11. **About the Science section** — a static informational section explaining: the five cognitive domains and their evidence base, the near-transfer vs. far-transfer distinction, why 20+ hours matters, the role of lifestyle factors, and the research sources. Includes a clear statement of what the app can and cannot claim.
12. **Account settings** — ability to update email, password, notification time preference (daily reminder), and delete account (with data erasure per GDPR).
13. **Free-play mode** — users can launch any individual exercise directly from the dashboard Practice section. Starting a free-play session creates a real session, logs the result against domain progress, and navigates to the session summary on completion. Difficulty defaults to the user's current baseline-seeded level for that domain, or 1 if no baseline exists. All free-play results count towards cumulative training time and domain progress scores.
14. **In-app feedback capture** — users can submit free-text feedback from any authenticated page via a persistent floating button (bottom-right corner). Tapping the button opens a small modal with a text area (max 1000 characters) and a Submit button. On submit, a brief "Thank you for your feedback" confirmation appears and auto-dismisses. Additionally, a feedback prompt appears on the Session Summary screen after every completed training session — this is optional and includes a Skip button so it never blocks access to session results. All feedback is stored server-side tagged with the page context and, where applicable, the session ID.

---

## 5. Out of Scope

- Native iOS and Android apps — v1 is a web app; native apps deferred until core experience is validated with real users
- Executive Function domain and its exercise variants (task-switching card sort; planning/sequence task) — deferred to v1.1
- Episodic Memory domain and its exercise variants (word-pair association; spatial location memory) — deferred to v1.1
- Offline mode — all sessions require an internet connection in v1
- Push notifications — daily reminders are informational only; no push notification system in v1
- Apple Health / Google Fit integration — lifestyle data is self-reported only in v1
- Social features, friend leaderboards, and community streaks
- Audio/rhythm-based task variants and dual-task (physical + cognitive) modules
- Neurostimulation, EEG/biofeedback integration (excluded per functional requirements)
- AI-powered dementia screening or diagnostic features (excluded per functional requirements)
- Third-party research data export or anonymised data sharing (requires separate consent flow — deferred)
- Adolescent (under 18) specific modes
- Multilingual / localisation support beyond English
- In-app subscription or payment flow

---

## 6. Data Model

### Entity: User

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| email | string | Required, unique, max 255 chars |
| password_hash | string | Required, bcrypt hashed |
| created_at | datetime | Required, auto-set |
| consent_given_at | datetime | Required — must be set at registration |
| notification_time | time | Optional, default 09:00 |
| baseline_completed | boolean | Default false |
| total_training_seconds | integer | Default 0 |
| next_baseline_eligible_date | date | Nullable; set to 6 months after each baseline completion |

### Entity: BaselineResult

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, required |
| domain | enum | One of: processing_speed, working_memory, attention (executive_function and episodic_memory reserved for v1.1) |
| score | float | 0.0–100.0 |
| completed_at | datetime | Required |
| baseline_number | integer | 1 = original, 2 = first re-baseline, etc. Auto-incremented per user |
| is_original | boolean | True only for baseline_number = 1; never changes |

> **Note (Q6 resolution):** Baseline is repeatable every 6 months. The original baseline (is_original = true) is always retained as the long-term reference. The most recent baseline is used for adaptive difficulty calibration and current-period progress comparisons. Progress dashboard shows both original and current-period comparisons.

### Entity: Session

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, required |
| started_at | datetime | Required |
| completed_at | datetime | Nullable — null if session abandoned |
| duration_seconds | integer | Set on completion |
| domains_trained | string | JSON array of domain names |

### Entity: ExerciseAttempt

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| session_id | UUID | Foreign key → Session, required |
| domain | enum | One of: processing_speed, working_memory, attention |
| exercise_type | string | One of: symbol_matching, visual_categorisation, n_back, digit_span, go_no_go, stroop, card_memory |
| difficulty_level | integer | 1–10 |
| trials_presented | integer | Required |
| trials_correct | integer | Required |
| avg_response_ms | integer | Average response time in milliseconds |
| score | float | 0.0–100.0, computed from accuracy + speed |

### Entity: DomainProgress

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, required |
| domain | enum | One of: processing_speed, working_memory, attention |
| current_difficulty | integer | 1–10, updated after each session |
| latest_score | float | 0.0–100.0 |
| updated_at | datetime | Required |

### Entity: LifestyleLog

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, required |
| logged_date | date | Required, one entry per user per day |
| exercise_minutes | integer | Nullable, 0–1440 |
| sleep_hours | float | Nullable, 0–24 |
| sleep_quality | integer | Nullable, 1–5 |
| social_engagement | boolean | Nullable |
| stress_level | integer | Nullable, 1–5 |
| mood | integer | Nullable, 1–5 |
| created_at | datetime | Required |

### Entity: FeedbackEntry

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Nullable, foreign key → User — null for anonymous submissions |
| page_context | string | Required, max 100 chars — identifies the page or surface where feedback was submitted (e.g. "dashboard", "session_summary", "progress", "lifestyle_log", "settings") |
| session_id | UUID | Nullable, foreign key → Session — only set when submitted from the post-game prompt on SessionSummary |
| feedback_text | string | Required, max 1000 chars |
| created_at | datetime | Required, auto-set |
| processed | boolean | Default false — set to true after the autonomous feedback agent processes the entry |

### Entity: SkillAssessment

| Field | Type | Constraints |
|---|---|---|
| id | integer | Primary key |
| user_id | integer | Foreign key → User, required |
| game_key | string | One of: stroop, go_no_go, symbol_matching, nback, digit_span, card_memory, visual_categorisation |
| assessed_level | integer | 1–3, the staircase-converged difficulty level |
| assessed_at | datetime | Required, auto-set on creation, updated on re-baseline |
| baseline_count | integer | Default 1, incremented on each re-baseline |

### Entity: Streak

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, unique |
| current_streak | integer | Default 0 |
| longest_streak | integer | Default 0 |
| last_session_date | date | Nullable |

---

## 7. API / Route Map

### Authentication

| Method | Path | Description | Auth required? |
|---|---|---|---|
| POST | /api/auth/register | Register new user (email, password, consent) | N |
| POST | /api/auth/login | Login, returns session token | N |
| POST | /api/auth/logout | Invalidate session token | Y |
| POST | /api/auth/reset-password | Request password reset email | N |
| POST | /api/auth/reset-password/confirm | Confirm reset with token + new password | N |

### Onboarding & Baseline

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | /api/adaptive-baseline/status | Returns whether baseline is complete and per-game SkillAssessment profile | Y |
| POST | /api/adaptive-baseline/complete | Submit adaptive baseline results (array of `{ game_key, assessed_level }`); seeds DomainProgress | Y |

### Training Sessions

| Method | Path | Description | Auth required? |
|---|---|---|---|
| POST | /api/sessions/start | Begin a new training session; returns first exercise | Y |
| GET | /api/sessions/:id/next | Get next exercise in the session | Y |
| POST | /api/sessions/:id/attempt | Submit result for one exercise attempt | Y |
| POST | /api/sessions/:id/complete | Mark session complete; returns summary | Y |
| GET | /api/sessions/history | List past sessions (paginated, 20 per page) | Y |

### Free-Play

Free-play uses the same session API as structured training. The frontend (`FreePlay.jsx`) handles the single-game flow: start session → log single attempt → complete session → navigate to summary. No separate backend routes required.

### Dashboard & Progress

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | /api/dashboard | Returns streak, total time, Brain Health Score, domain scores, lifestyle summary | Y |
| GET | /api/progress/:domain | 30-day trend data for one domain | Y |
| GET | /api/progress/brain-health-score | Score breakdown (cognitive + lifestyle factors) | Y |

### Lifestyle Logging

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | /api/lifestyle/today | Get today's lifestyle log (or empty) | Y |
| POST | /api/lifestyle/log | Create or update today's lifestyle log | Y |
| GET | /api/lifestyle/history | Last 30 days of lifestyle logs | Y |

### Account

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | /api/account | Get current user profile | Y |
| PATCH | /api/account | Update email, password, or notification_time | Y |
| DELETE | /api/account | Delete account and erase all personal data (GDPR) | Y |

### Feedback

| Method | Path | Description | Auth required? |
|---|---|---|---|
| POST | /api/feedback | Submit free-text feedback. Body: `{ page_context: string, feedback_text: string, session_id?: string }`. Response: `{ id: string, created_at: datetime }` | Y |
| GET | /api/feedback | Export all feedback entries, grouped by `page_context`. Query params: `from_date` (ISO date, optional), `to_date` (ISO date, optional). Response: `{ total: int, groups: [{ page_context, entries: [{ id, user_id, feedback_text, session_id, created_at }] }] }`. Intended for pipeline use — feeds the Feedback Synthesis step. | Y |

### Static / Content

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | /about-the-science | About the Science page | N |

---

## 8. Technology Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | React (Vite) | Component model suits the exercise UI well; design system is CSS custom properties — integrates cleanly with React; Vite is fast for development |
| Styling | Plain CSS with the provided design system tokens | Design System v1 is fully specified as CSS custom properties and class patterns — use it directly, no CSS framework |
| Backend | Python / FastAPI | Project default; clean async support for session state; auto-generated OpenAPI docs aid testing |
| Database | SQLite (dev) / PostgreSQL (prod) | Project default; zero-config for development |
| ORM | SQLAlchemy | Mature, works with both SQLite and PostgreSQL |
| Authentication | JWT tokens stored in httpOnly cookies (`SameSite=None; Secure=True`) **and** mirrored to localStorage for cross-origin Bearer token auth. The axios client reads the token from localStorage and sends it as `Authorization: Bearer <token>` on every request. localStorage is cleared on logout, on 401 responses, and on failed `/api/auth/me` checks. | Required because frontend and backend are deployed on different Railway subdomains (cross-origin). Cookie provides session continuity; Bearer header satisfies FastAPI JWT middleware. |
| Fonts | Google Fonts — Instrument Serif + Inter | As specified in Design System v1 |
| Icons | Lucide React | As specified in Design System v1 |
| Testing | pytest (backend) + Vitest (frontend) | Project defaults |
| Deployment target | Railway (both backend and frontend) | Single platform, environment variables managed per service |

**Deviation note:** The functional requirements specify iOS & Android mobile apps. This spec targets a responsive web app (mobile-first, PWA-capable) as the v1 platform, using the CSS design system as specified. The design system explicitly includes mobile breakpoints (390px) and bottom navigation patterns, confirming the web approach is compatible with the intended mobile experience.

---

## 9. File & Folder Structure

```
brain-training/
├── README.md
├── backend/
│   ├── main.py                        # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   ├── database.py                    # SQLAlchemy setup, session factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── exercise_attempt.py
│   │   ├── domain_progress.py
│   │   ├── lifestyle_log.py
│   │   ├── streak.py
│   │   └── feedback_entry.py              # FeedbackEntry model
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── baseline.py
│   │   ├── sessions.py
│   │   ├── progress.py
│   │   ├── lifestyle.py
│   │   ├── account.py
│   │   └── feedback.py                    # POST /api/feedback
│   ├── services/
│   │   ├── __init__.py
│   │   ├── adaptive_difficulty.py     # Per-domain difficulty adjustment logic
│   │   ├── brain_health_score.py      # Brain Health Score calculation
│   │   ├── exercise_generator.py      # Exercise/stimulus generation per type
│   │   ├── session_planner.py         # Domain selection + session sequencing
│   │   └── streak_manager.py          # Streak calculation and update
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── session.py
│   │   ├── progress.py
│   │   ├── lifestyle.py
│   │   └── feedback.py                    # FeedbackInput, FeedbackResponse schemas
│   └── tests/
│       ├── test_auth.py
│       ├── test_sessions.py
│       ├── test_adaptive_difficulty.py
│       └── test_brain_health_score.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env.example
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── styles/
        │   ├── design-system.css      # All CSS custom properties from Design System v1
        │   ├── components.css         # Button, card, input, nav patterns
        │   └── global.css             # Resets, base, focus, reduced-motion
        ├── components/
        │   ├── ui/                    # Reusable: Button, Card, Input, Badge, ProgressBar, FeedbackWidget, PostGameFeedback
        │   ├── nav/                   # Sidebar, BottomNav, TopNav
        │   ├── exercises/             # One component per exercise type (10 total)
        │   └── charts/                # TrendChart, DomainScoreCard, BrainHealthGauge
        ├── pages/
        │   ├── Landing.jsx
        │   ├── Register.jsx
        │   ├── Login.jsx
        │   ├── Onboarding.jsx         # Baseline assessment flow
        │   ├── Dashboard.jsx
        │   ├── Session.jsx            # Active training session
        │   ├── SessionSummary.jsx
        │   ├── Progress.jsx
        │   ├── LifestyleLog.jsx
        │   ├── AboutScience.jsx
        │   └── Settings.jsx
        ├── hooks/
        │   ├── useAuth.js
        │   ├── useAuth.jsx
        │   ├── useSession.js
        │   └── useDashboard.js
        ├── api/
        │   └── client.js              # Axios instance + Bearer token interceptor + all API call functions
        ├── utils/
        │   ├── scoring.js             # Score display helpers
        │   └── time.js                # Duration formatting helpers
        └── test/
            ├── Dashboard.test.jsx
            ├── Session.test.jsx
            └── Stroop.test.jsx        # Unit tests for computeStroopResult pure function
```

---

### §9a. Feedback Feature Integration Points (added v0.5)

| File | Change |
|---|---|
| `frontend/src/App.jsx` | Mount `<FeedbackWidget />` inside the authenticated route wrapper — renders on all logged-in pages |
| `frontend/src/pages/SessionSummary.jsx` | Render `<PostGameFeedback sessionId={sessionId} />` below summary content; includes Skip button |
| `frontend/src/api/client.js` | Add `submitFeedback(pageContext, feedbackText, sessionId = null)` function |
| `backend/main.py` | Register `feedback` router with prefix `/api/feedback` |

**FeedbackWidget behaviour:** Floating button fixed to bottom-right (above bottom nav on mobile). On click, opens an overlay modal with a textarea (placeholder: "Share your thoughts…"), a Submit button, and a close (×) button. On successful submit, replaces form with "Thank you for your feedback!" and closes after 2 seconds. Sends `page_context` derived from `window.location.pathname`.

**PostGameFeedback behaviour:** Rendered as a card section at the bottom of the SessionSummary page with heading "How did that feel?" and a textarea. Has Submit and Skip buttons side by side. Skip closes/hides the component without submitting. On submit, shows inline confirmation "Thanks!" and hides the form. Always sends `session_id` of the completed session.

**Feedback pipeline (v0.7 — autonomous):** Raw entries exported via `GET /api/feedback` are processed by the **Feedback Synthesis prompt** (`agent-prompts/feedback-synthesis.md`). The synthesis step groups feedback by theme, maps themes to spec sections, and produces a structured digest. An autonomous **feedback agent** (`feedback_agent/pipeline.py`) then:
1. Fetches unprocessed feedback via `GET /api/feedback`
2. Passes entries to Claude Opus 4.6 (synthesizer) to produce a `feedback-digest.md`
3. Passes `spec.md` + `feedback-digest.md` to Claude Opus 4.6 (implementer) to generate code changes
4. Creates a git branch, commits changes, and opens a pull request via the `gh` CLI
5. Marks each processed feedback entry to prevent re-processing

The pipeline supports a `DRY_RUN` mode that executes synthesis but does not commit, open a PR, or mark items as processed. See `feedback_agent/` for implementation details.

---

## 10. Non-Functional Requirements

- **Performance:** Dashboard must load within 2 seconds on a standard mobile connection. Exercise screens must render the next trial within 200ms of a response (no perceptible lag between trials, as response timing is a measured variable).
- **Security:** Passwords hashed with bcrypt (cost factor ≥ 12). JWT tokens stored in httpOnly cookies with `SameSite=None; Secure=True` — required because the frontend and backend are deployed on different subdomains (cross-origin). The token is also mirrored to localStorage solely to support the `Authorization: Bearer` header required by the cross-origin FastAPI deployment; localStorage is cleared on logout, on 401 responses, and when `/api/auth/me` fails. All API endpoints require authentication except register, login, reset-password, and about-the-science. Account deletion must purge all personal data within 30 days (GDPR Article 17).
- **Accessibility:** All interactive elements minimum 44×44px touch target (as specified in Design System §11). WCAG AA contrast compliance (body text 14:1, secondary text 6:1 — confirmed by Design System §2). Focus rings always visible. `prefers-reduced-motion` media query must be included (provided in Design System §7). Progress bar elements must include `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`. Navigation uses `<nav aria-label="Primary">` (sidebar) and `<nav aria-label="Mobile">` (bottom bar).
- **Browser / environment support:** Chrome and Safari latest two major versions, on iOS and Android. Python 3.11+, Node 20+.
- **Error handling:** All API errors return JSON with a `message` field. No stack traces in production responses. Frontend displays user-friendly error messages for all failure states (network error, session timeout, invalid input).
- **Data integrity:** Exercise attempt scores are computed server-side, not client-side, to prevent manipulation. Lifestyle log enforces one entry per user per day at the database level (unique constraint on user_id + logged_date).
- **