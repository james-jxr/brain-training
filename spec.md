# App Specification: Brain Training App

**Spec Version:** v1.3
**Date:** 2026-04-30
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
| v1.0 | 2026-04-21 | Password minimum length (8 characters) enforced on registration and account update via Pydantic validators. Feedback export endpoint (`GET /api/feedback`) is now admin-only (restricted to emails in `ADMIN_EMAILS` setting; returns 403 otherwise). Auth token storage migrated from `localStorage` to `sessionStorage` in `useAuth.jsx`; duplicate `useAuth.js` file removed. `BottomNav` no longer imports `useAuth`. `GoNoGoLegacy.jsx` retired and removed; the current Go/No-Go implementation lives in `GoNoGo.jsx`. `DomainProgress` null-safety fix: `total_attempts` and `total_correct` now coerce `None` to 0 before incrementing. Streak manager migrated to timezone-aware datetimes (`timezone.utc`); same-day sessions no longer increment streak count. `VisualCategorisation` internal helper renamed from `pick` to `pickRandom` (no user-facing change). `LifestyleLog` now logs errors to console on failed today-data fetch. |
| v1.1 | 2026-04-29 | Mindfulness exercise added (guided breathing, 2-minute session, no scoring, 10 breath cycles). Session planner now always includes mindfulness as a third domain in every planned session. Within-session adaptive difficulty staircase rule added (`adjust_difficulty_in_session`): difficulty increases by 1 above 80%, decreases by 1 below 50%, clamped to [1, 10]; `adjusted_difficulty` returned on exercise attempt response. `FeedbackEntry` gains `project_id` field (default "brain-training"). `UserResponse` schema gains `has_completed_baseline` field. New `GET /api/progress/streak/history` endpoint returns 14-day session completion history. New `GET /api/progress/game-history` endpoint returns per-game score history (last 20 attempts per exercise type). `TrendChart` component upgraded to bar chart visualisation with external data support and `GAME_TYPE_LABELS` map. `useGameHistory` and `useStreakData` hooks added. `StreakTracker` component added. Auth token storage confirmed as `sessionStorage` throughout axios client. Baseline tests added (`test_baseline.py`) covering `has_completed_baseline` flag. Mindfulness unit tests added (`Mindfulness.test.jsx`). |
| v1.2 | 2026-04-29 | Baseline router expanded: `POST /api/baseline/start` added (creates session, enforces eligibility via `next_baseline_eligible_date`, returns `baseline_number`); `POST /api/baseline/submit` extended (sets `onboarding_completed`, `has_completed_baseline`, `next_baseline_eligible_date = today + 180 days`, increments `baseline_number`, validates domain names, seeds/updates `DomainProgress`); `GET /api/baseline/next-eligible-date` added (returns `is_eligible` and `next_eligible_date`). Eligibility rule: request is blocked with HTTP 400 if `next_baseline_eligible_date` is strictly in the future; allowed when null or ≤ today. `BaselineResult.completed_at` migrated to timezone-aware `datetime.now(timezone.utc)`. Lifestyle history query corrected to filter on `logged_date` (date field) instead of `created_at` (datetime field), using `date.today() - timedelta(days=30)`. `BrainHealthScoreService.calculate_lifestyle_score` corrected to filter on `logged_date >= date.today() - timedelta(days=7)` instead of `created_at`. Streak manager constants extracted (`SECONDS_PER_HOUR = 3600`, `STREAK_EXPIRY_HOURS = 36`). Test suites substantially expanded: `test_baseline.py` now covers start/submit/next-eligible-date flows in full; `test_brain_health_score.py` rewritten with isolated test DB and full coverage of domain average, lifestyle score, and composite score; `test_lifestyle.py` added covering log creation/update, today endpoint, and 30-day history; `test_streak_manager.py` added. |
| v1.3 | 2026-04-30 | `useGameHistory` and `useStreakData` hooks refactored to use `progressAPI` from the centralised axios client instead of raw `fetch` calls. `progressAPI` gains two new methods: `getGameHistory()` (calls `GET /api/progress/game-history`) and `getStreakHistory()` (calls `GET /api/progress/streak/history`). `useStreakData` error handling improved: errors now prefer `err.response?.data?.detail`, fall back to `err.message`, then fall back to the static string `'Failed to fetch streak data'`. axios 401 interceptor public-page list reordered to `['/', '/login', '/register']` (no functional change). Test suites added: `client.test.js` covering all API client exports; `useGameHistory.test.js` and `useStreakData.test.js` covering loading state, success, error, and mount behaviour. |

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

1. **User registration and login** — email + password authentication with explicit GDPR/CCPA consent at registration. Password reset via email. **Passwords must be at least 8 characters** — enforced at both registration and account password update; shorter passwords are rejected with a validation error.
2. **Baseline assessment** — covers all five cognitive domains (Processing Speed, Working Memory, Attention & Inhibitory Control, Executive Function, Episodic Memory). Takes approximately 10 minutes. Results set adaptive difficulty starting points per domain. Completed once at onboarding, then repeatable every 6 months. Each re-baseline resets the current-period improvement reference and recalibrates difficulty; the original baseline is always retained for long-term comparison. The dashboard notifies users when they become eligible for re-baseline. Once a user submits baseline results, the `has_completed_baseline` flag on their user profile is set to `true`, `onboarding_completed` is set to `true`, and `next_baseline_eligible_date` is set to 180 days from today. A user may not start a new baseline if `next_baseline_eligible_date` is set and is strictly in the future — such attempts are rejected with HTTP 400 and a message of the form `"Next baseline eligible on <date>"`. Eligibility is allowed when the field is null (new users) or when `next_baseline_eligible_date` is today or in the past.
3. **Daily training session** — a guided 15–20 minute session covering exercises from 2–3 domains per session. Sessions are interleaved (not blocked on a single domain). Each session contains a minimum of 2 task variants per domain visited. Every planned session includes a mindfulness (guided breathing) exercise in addition to the two cognitive domains selected by the session planner. On completion, the user sees a session summary screen.
4. **Adaptive difficulty per domain** — each domain tracks a rolling performance score (accuracy + speed) and adjusts task difficulty up or down to maintain a 70–80% success rate target. Difficulty cannot plateau — the system must continue to increase challenge for consistently high-performing users. **Within-session staircase rule:** after each exercise attempt the backend computes an `adjusted_difficulty` for the next exercise of the same type using a simple staircase: if the accuracy score exceeds 80%, difficulty increases by 1; if below 50%, difficulty decreases by 1; otherwise it stays the same. The result is clamped to [1, 10] and returned in the exercise attempt response as `adjusted_difficulty`.
5. **Cognitive exercise library (v1 launch)** — two concrete task variants per domain across 3 domains at launch, plus a mindfulness exercise included in every session. Executive Function and Episodic Memory are deferred to v1.1. **Symbol matching is currently hidden** pending replacement with a new task variant (see §11 Q7). `GoNoGoLegacy.jsx` has been retired and removed; the current Go/No-Go implementation lives in `GoNoGo.jsx`:
   - *Processing Speed:* ~~Symbol matching task~~ *(hidden, replacement pending)*; Card memory task
   - *Working Memory:* N-back sequence task; digit span task
   - *Attention & Inhibitory Control:* Go/No-go reaction task; Stroop colour-word interference task
   - *All domains (baseline + free-play):* Shape Sort — abstract rule-induction task where users infer a sorting rule from examples (see §11a for design details)
   - *Mindfulness (every session):* Guided breathing exercise — a 2-minute session of 10 breath cycles (inhale 4s → hold 4s → exhale 4s). No accuracy score is produced. The user is shown the current breath phase label and an animated circle. On completion the user optionally rates how they feel (1–5 scale) before dismissing. The feeling rating is submitted alongside the completion result. Mindfulness is treated as a no-scoring exercise by the session planner and is not factored into domain accuracy calculations.
6. **Post-session summary** — displayed after every session: domains trained, performance vs. previous session per domain, current streak, and a one-line science-grounded observation about their result. The summary displays the user's **Accuracy** score (labelled as such) with a sub-label showing correct trials out of total trials attempted (e.g. "7 correct out of 10 trials").
7. **Streak and consistency tracking** — daily streak counter visible on the dashboard and post-session screen. Streak resets if no session is completed within a 36-hour window (allowing for timezone flexibility). The streak expiry threshold is defined as `STREAK_EXPIRY_HOURS = 36` in the streak manager service. Multiple sessions on the same calendar day do not increment the streak beyond 1 for that day. Total cumulative training time displayed prominently with a milestone marker at 20 hours.
8. **Progress dashboard** — the main logged-in home screen showing: current streak, cumulative training time, per-domain performance scores (separate, not collapsed), a 30-day trend graph per domain, Brain Health Score, and lifestyle summary. The `TrendChart` component renders data as a bar chart (one bar per session, height proportional to score relative to the session maximum). Charts can be driven either by domain (fetching from `/api/progress/:domain`) or by externally supplied data arrays. The `StreakTracker` component displays a 14-day calendar view of session completion using data from `/api/progress/streak/history`.
9. **Brain Health Score** — a composite score (0–100, returned as integer) derived from cognitive performance across all domains (60% weight) and lifestyle inputs (40% weight). The lifestyle component is calculated from `LifestyleLog` entries where `logged_date >= date.today() - timedelta(days=7)` (i.e. the last 7 calendar days based on the date field, not the created_at timestamp). The domain component is calculated as the average of `last_score` across all `DomainProgress` rows for the user; if any row has a null `last_score` the average returns 0.0. Recalculated after each session and after each lifestyle log entry. Score is accompanied by a breakdown showing the contribution of each factor. The composite formula is: `round(domain_avg * 0.6 + lifestyle_score * 0.4)`.
10. **Lifestyle habit logging** — a daily log capturing five lifestyle factors: physical activity (minutes of aerobic exercise), sleep (hours + quality rating 1–5), social engagement (yes/no interaction today), stress level (1–5), and mood (1–5). Accessible from the dashboard. Users are prompted to log after each training session. The 30-day history endpoint filters on `logged_date >= date.today() - timedelta(days=30)` (date field comparison, not timestamp).
11. **About the Science section** — a static informational section explaining: the five cognitive domains and their evidence base, the near-transfer vs. far-transfer distinction, why 20+ hours matters, the role of lifestyle factors, and the research sources. Includes a clear statement of what the app can and cannot claim.
12. **Account settings** — ability to update email, password (minimum 8 characters enforced), notification time preference (daily reminder), and delete account (with data erasure per GDPR).
13. **Free-play mode** — users can launch any individual exercise directly from the dashboard Practice section. Starting a free-play session creates a real session, logs the result against domain progress, and navigates to the session summary on completion. Difficulty defaults to the user's current baseline-seeded level for that domain, or 1 if no baseline exists. All free-play results count towards cumulative training time and domain progress scores.
14. **In-app feedback capture** — users can submit free-text feedback from any authenticated page via a persistent floating button (bottom-right corner). Tapping the button opens a small modal with a text area (max 1000 characters) and a Submit button. On submit, a brief "Thank you for your feedback" confirmation appears and auto-dismisses. Additionally, a feedback prompt appears on the Session Summary screen after every completed training session — this is optional and includes a Skip button so it never blocks access to session results. All feedback is stored server-side tagged with the page context and, where applicable, the session ID. Every feedback entry is tagged with `project_id = "brain-training"` server-side.

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
| has_completed_baseline | boolean | Default false — set to true when baseline results are submitted via `POST /api/baseline/submit`; exposed on `GET /api/auth/me` response |
| onboarding_completed | boolean | Default false — set to true when baseline results are submitted via `POST /api/baseline/submit` |
| total_training_seconds | integer | Default 0 |
| next_baseline_eligible_date | date | Nullable; set to `date.today() + timedelta(days=180)` after each baseline submission. When null, the user is always eligible. When set, the user is eligible only if the date is today or in the past. |

### Entity: BaselineResult

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, required |
| domain | enum | One of: processing_speed, working_memory, attention (executive_function and episodic_memory reserved for v1.1). Submitting an unrecognised domain value returns HTTP 400 with `"Invalid domain"` in the error message. |
| score | float | 0.0–100.0 |
| completed_at | datetime | Required; stored as timezone-aware UTC (`datetime.now(timezone.utc)`) |
| baseline_number | integer | 1 = original, 2 = first re-baseline, etc. Auto-incremented per user; each submission increments by 1 regardless of domain count in that submission |
| is_original | boolean | True only for baseline_number = 1; never changes after first submission |

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
| domain | enum | One of: processing_speed, working_memory, attention, mindfulness |
| exercise_type | string | One of: symbol_matching, visual_categorisation, n_back, digit_span, go_no_go, stroop, card_memory, mindfulness |
| difficulty_level | integer | 1–10; mindfulness attempts always use difficulty 1 |
| trials_presented | integer | Required; 0 for mindfulness |
| trials_correct | integer | Required; 0 for mindfulness |
| avg_response_ms | integer | Average response time in milliseconds; nullable for mindfulness |
| score | float | 0.0–100.0, computed from accuracy + speed; null for mindfulness (no-scoring exercise) |

### Entity: DomainProgress

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, required |
| domain | enum | One of: processing_speed, working_memory, attention |
| current_difficulty | integer | 1–10, updated after each session |
| last_score | float | 0.0–100.0; used by BrainHealthScoreService for domain average calculation. If null, the domain average calculation returns 0.0. Updated to the latest submitted score on each baseline submission. |
| total_attempts | integer | Nullable in DB; treated as 0 when null — coerced before incrementing |
| total_correct | integer | Nullable in DB; treated as 0 when null — coerced before incrementing |
| updated_at | datetime | Required |

### Entity: LifestyleLog

| Field | Type | Constraints |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | Foreign key → User, required |
| logged_date | date | Required, one entry per user per day. Used as the filter field for history queries (not `created_at`). |
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
| project_id | string | Required, default "brain-training" — set server-side, not user-supplied |
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
| POST | /api/auth/register | Register new user (email, password ≥ 8 chars, consent) | N |
| POST | /api/auth/login | Login, returns session token | N |
| POST | /api/auth/logout | Invalidate session token | Y |
| POST | /api/auth/reset-password | Request password reset email | N |
| POST | /api/auth/reset-password/confirm | Confirm reset with token + new password | N |
| GET | /api/auth/me | Returns current user profile including `has_completed_baseline` | Y |

### Onboarding & Baseline

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | /api/adaptive-baseline/status | Returns whether baseline is complete and per-game SkillAssessment profile | Y |
| POST | /api/adaptive-baseline/complete | Submit adaptive baseline results (array of `{ game_key, assessed_level }`); seeds DomainProgress | Y |
| POST | /api/baseline/start | Begin a new baseline session. Checks `next_baseline_eligible_date` — if set and strictly in the future, returns HTTP 400 with `{ "message": "Next baseline eligible on <ISO date>" }`. Otherwise creates a baseline session record and returns `{ baseline_number, is_baseline, domain_1, domain_2, ... }`. `baseline_number` reflects how many baselines the user has started (increments on each call). | Y |
| POST | /api/baseline/submit | Submit domain baseline scores (array of `{ domain, score }`). Validates each domain name — unknown domains return HTTP 400 with `"Invalid domain"` in the error message. On success: stores `BaselineResult` rows (with `baseline_number` auto-incremented, `is_original = true` only for the first submission), updates or creates `DomainProgress` rows (setting `last_score`), sets `user.has_completed_baseline = true`, `user.onboarding_completed = true`, and `user.next_baseline_eligible_date = date.today() + timedelta(days=180)`. Response: `{ message, baseline_number, is_original, results: [{ domain, score, baseline_number, is_original }] }`. | Y |
| GET | /api/baseline/next-eligible-date | Returns `{ is_eligible: bool, next_eligible_date: ISO date string or null }`. `is_eligible` is true when `next_baseline_eligible_date` is null, today, or in the past. | Y |

### Training Sessions

| Method | Path | Description | Auth required? |
|---|---|---|---|
| POST | /api/sessions/start | Begin a new training session; returns first exercise | Y |
| GET | /api/sessions/:id/next | Get next exercise in the session | Y |
| POST | /api/sessions/:id/attempt | Submit result for one exercise attempt. Response includes `accuracy_score` (rounded to 2 dp) and `adjusted_difficulty` (integer 1–10, computed by within-session staircase rule) | Y |
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
| GET | /api/progress/streak/history | Returns `current_streak`, `longest_streak`, and a `days` array covering the last 14 calendar days. Each day entry: `{ date: ISO string, completed: boolean, is_today: boolean }`. Used by the `StreakTracker` component via the `useStreakData` hook (calls `progressAPI.getStreakHistory()`). | Y |
| GET | /api/progress/game-history | Returns per-exercise-type score history. Response: `{ games: { [exercise_type]: [{ date, score, difficulty }] } }`. Last 20 attempts per exercise type, oldest-first. Score is computed from `trials_correct / trials_presented * 100` where available, else from `attempt.score`, else 0. Used by the `useGameHistory` hook (calls `progressAPI.getGameHistory()`). | Y |

### Lifestyle Logging

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | /api/lifestyle/today | Get today's lifestyle