# App Specification: Baseline Test — Adaptive Skill Assessment

**Spec Version:** spec-v0.1
**Date:** 2026-04-04
**Status:** Draft
**Brief Reference:** A dedicated mode that runs the user through all games...

---

## 1. Purpose & Problem Statement

The Baseline Test is an adaptive assessment mode embedded in the Brain Training app. It runs the user through each mini-game using a 2-up/1-down staircase algorithm to locate their current skill level per game in approximately 8 rounds. The results are stored as a Skill Profile that sets default starting difficulty for future training sessions, replacing the current one-size-fits-all difficulty starting point.

---

## 2. Target User

Registered brain training users on their first login (prompted automatically) or any time they want to re-assess their skill level (via main menu or profile page). Users are comfortable with browser-based apps; no technical knowledge required. They may be of any age or cognitive ability — the adaptive algorithm meets them where they are.

---

## 3. User Stories

- As a new user, I want to be prompted to take a quick baseline test after logging in for the first time, so that the app personalises my starting difficulty without me having to configure anything.
- As a returning user, I want to retake the baseline test at any time from the dashboard or settings page, so that my skill profile reflects my current level after extended training.
- As a user taking the baseline test, I want to see a brief introduction before the games begin, so that I understand what to expect and how long it takes.
- As a user in the test, I want each game to adapt its difficulty round by round based on my answers, so that I am quickly assessed at my true level without too many trivially easy or impossible rounds.
- As a user who has completed the test, I want to see a clear Skill Profile screen summarising my assessed level per game, so that I know my starting point.
- As a user in a regular training session, I want each game to start at my assessed difficulty level automatically, so that sessions are appropriately challenging from the first round.
- As a user on the profile/settings page, I want to view my current Skill Profile at any time, so that I can track my assessed starting levels over time.

---

## 4. MVP Feature List (In Scope)

1. **First-login prompt**: After a user logs in for the first time (or when `has_completed_baseline` is `false`), the Dashboard shows a dismissible banner/modal inviting them to take the baseline test with a "Take Baseline Test" CTA and a "Skip for now" option.
2. **Baseline entry points**: The Dashboard and Settings page both expose a "Retake Baseline Test" button, navigating to `/baseline`.
3. **Intro screen**: The baseline route shows a screen explaining "We'll run you through each game to find your level. This takes about 5 minutes." with a "Begin" button before any game starts.
4. **Games run in fixed order**: The test covers all existing games (NBack, CardMemoryGame, DigitSpan, GoNoGo, Stroop, SymbolMatching, VisualCategorisation) played one at a time in a fixed sequence.
5. **8 rounds per game**: Each game is played for exactly 8 rounds in baseline mode. A "round" is one complete play of the game component (one `onComplete` callback from the game).
6. **2-up/1-down adaptive algorithm**: Difficulty starts at Easy for each game. Two consecutive correct answers step difficulty up; one incorrect answer steps difficulty down. Difficulty floors at Easy and caps at Hard. The algorithm runs entirely client-side.
7. **Difficulty levels**: Three levels — Easy (1), Medium (2), Hard (3) — mapped to existing numeric difficulty props: Easy → 2, Medium → 5, Hard → 8.
8. **"Correct" definition per game**: NBack: accuracy ≥ 60% (`trials_correct / trials_presented`). CardMemoryGame: `correct === true` from `onComplete`. For all other games: treated as always-correct (assessed level = final difficulty after 8 rounds; difficulty increases each step and stays put otherwise — conservative fallback).
9. **Between-game transition screen**: After each game completes 8 rounds, a short "Next: [Game Name]" transition screen is shown before the next game starts.
10. **Skill Profile result screen**: After all games complete, a Skill Profile screen shows each game name with its assessed level (Easy / Medium / Hard) with a "Save & Return to Dashboard" button.
11. **Persist assessed difficulty per game per user**: On baseline completion, the frontend POSTs results to the backend, which stores one `SkillAssessment` row per game per user (upserted — last result wins).
12. **First-login flag**: The `User` model gains a `has_completed_baseline` boolean (default `false`). Set to `true` when `POST /api/adaptive-baseline/complete` is called successfully.
13. **Skill Profile API**: `GET /api/adaptive-baseline/status` returns `has_completed` flag plus the current skill profile (list of game assessments). Used by the Dashboard to decide whether to show the first-login prompt and by the Skill Profile page to display results.
14. **Baseline rounds excluded from brain health score**: Rounds played during baseline mode do not submit to the existing session/exercise-attempt scoring pipeline. The `BaselineGameWrapper` component simply discards `onComplete` payloads after recording correctness.
15. **Session difficulty seeding**: When the user starts a regular training session, the frontend queries `GET /api/adaptive-baseline/status` and passes the assessed difficulty prop to each game component if a profile exists.
16. **Skill Profile on settings/profile page**: The Settings page displays the current Skill Profile (queried from `GET /api/adaptive-baseline/status`) with a "Retake Baseline Test" button.

---

## 5. Out of Scope

- Collecting per-round response times or partial correctness signals beyond the binary correct/incorrect judgement already provided by each game's `onComplete`.
- Running baseline rounds against the existing brain health scoring pipeline or storing them as training sessions.
- Showing historical baseline results (only the most recent assessed level per game is stored and displayed).
- Allowing users to pause and resume a baseline test mid-way through a game sequence.
- Email notifications or push notifications prompting users to retake the baseline after a time interval.
- Admin tooling to view or reset baseline assessments across users.
- Per-game difficulty sub-levels beyond the three (Easy / Medium / Hard) already supported by the existing game components.

---

## 6. Data Model

### Existing model change: `User`

Add one column to the existing `users` table:

| Field | Type | Constraints |
|---|---|---|
| `has_completed_baseline` | Boolean | default False, not null |

> **Note:** `onboarding_completed` (existing) is set by the original domain-score baseline and is unrelated to this feature. The new flag tracks only adaptive game-based baseline completion.

### New entity: `SkillAssessment`

One row per (user, game). Upserted on each baseline completion so there is always at most one current assessment per game per user.

| Field | Type | Constraints |
|---|---|---|
| `id` | Integer | primary key, auto-increment |
| `user_id` | Integer | FK → users.id, not null, indexed |
| `game_key` | String | not null — e.g. `"nback"`, `"card_memory"`, `"digit_span"`, `"go_no_go"`, `"stroop"`, `"symbol_matching"`, `"visual_categorisation"` |
| `assessed_level` | Integer | not null — 1 = Easy, 2 = Medium, 3 = Hard |
| `assessed_at` | DateTime | default utcnow, updated on each upsert |
| `baseline_count` | Integer | default 1, incremented on each retake |

Unique constraint: `(user_id, game_key)` — enforced at the DB level so upsert logic works cleanly.

---

## 7. API / Route Map

The new router prefix is `/api/adaptive-baseline` to avoid collision with the existing `/api/baseline` router.

| Method | Path | Description | Auth required? |
|---|---|---|---|
| GET | `/api/adaptive-baseline/status` | Returns `{has_completed: bool, profile: [{game_key, game_name, assessed_level, difficulty_label}]}`. Empty `profile` list if no assessments exist yet. | Y |
| POST | `/api/adaptive-baseline/complete` | Accepts `{results: [{game_key, assessed_level}]}`. Upserts one `SkillAssessment` per game, sets `user.has_completed_baseline = true`. Returns updated profile. | Y |

---

## 8. Technology Stack

Matches the existing brain training app stack with no deviations.

| Layer | Choice | Reason |
|---|---|---|
| Frontend | React (Vite) | Existing stack |
| Backend | Python / FastAPI | Existing stack |
| Database | SQLite (dev) | Existing stack |
| Testing | pytest (backend) | Existing stack |
| Key libraries | SQLAlchemy, Pydantic, python-jose | Already in requirements.txt |

---

## 9. File & Folder Structure

Files that are **new** are marked `[NEW]`. Files that require **modification** are marked `[MOD]`.

```
apps/brain-training/
├── baseline-test/
│   └── spec.md                                              [NEW — this file]
│
├── backend/
│   ├── models/
│   │   ├── skill_assessment.py                              [NEW]
│   │   ├── user.py                                          [MOD — add has_completed_baseline]
│   │   └── __init__.py                                      [MOD — add SkillAssessment]
│   ├── routers/
│   │   ├── adaptive_baseline.py                             [NEW]
│   │   └── __init__.py                                      [MOD — add adaptive_baseline_router]
│   ├── schemas/
│   │   ├── adaptive_baseline.py                             [NEW]
│   │   └── __init__.py                                      [MOD — add new schemas]
│   ├── database.py                                          [MOD — import skill_assessment in init_db]
│   ├── main.py                                              [MOD — include adaptive_baseline_router]
│   └── tests/
│       └── test_adaptive_baseline.py                        [NEW]
│
└── frontend/src/
    ├── pages/
    │   └── BaselineTest.jsx                                 [NEW — orchestrator page]
    ├── components/
    │   └── baseline/
    │       ├── BaselineIntro.jsx                            [NEW]
    │       ├── BaselineGameWrapper.jsx                      [NEW — adaptive algo + 8-round loop]
    │       ├── BaselineTransition.jsx                       [NEW]
    │       ├── SkillProfileScreen.jsx                       [NEW — result screen after all games]
    │       └── BaselinePrompt.jsx                           [NEW — first-login modal/banner]
    ├── pages/
    │   ├── Dashboard.jsx                                    [MOD — show BaselinePrompt on first login]
    │   └── Settings.jsx                                     [MOD — show Skill Profile + Retake button]
    ├── api/
    │   └── client.js                                        [MOD — add adaptiveBaseline API calls]
    └── App.jsx                                              [MOD — add /baseline route]
```

---

## 10. Non-Functional Requirements

- **Performance:** Baseline status API (`GET /api/adaptive-baseline/status`) must respond in under 300 ms on a local SQLite database with ≤10,000 users.
- **Security:** All new endpoints require a valid JWT (same `get_current_user` dependency as existing routes). No sensitive data stored. Assessed difficulty levels are not sensitive but are user-specific and must not be readable by other users.
- **Accessibility:** All baseline screens must have appropriate heading hierarchy and button labels. Difficulty transitions must not rely on colour alone.
- **Browser support:** Chrome and Firefox latest (same as existing app).
- **Error handling:** If `POST /api/adaptive-baseline/complete` fails, the frontend shows a user-friendly error message ("Could not save your results — please try again") and does not navigate away from the Skill Profile screen.
- **Baseline rounds do not pollute scoring:** The `BaselineGameWrapper` must not call any existing session or exercise-attempt endpoints during baseline play.
- **No duplicate data:** The `SkillAssessment` table enforces a unique constraint on `(user_id, game_key)` and the router uses an upsert (query-then-update or merge) pattern, not a blind insert.

---

## 11. Open Questions

| ID | Question | Assumption made |
|---|---|---|
| Q1 | What is "correct" for DigitSpan, GoNoGo, Stroop, SymbolMatching, and VisualCategorisation games? Their `onComplete` signatures are not identical to NBack/CardMemoryGame. | Assumption: for all games beyond the two specified in the brief, use a conservative fallback — treat the round as "correct" if accuracy ≥ 60% where available, otherwise always-correct. The assessed level will still reflect difficulty stepped up over 8 rounds. This can be refined once each game's `onComplete` payload is audited. |
| Q2 | Should the first-login prompt appear only once (skipped = never shown again), or re-appear on each login until the baseline is completed? | Assumption: the prompt re-appears on each login until `has_completed_baseline` is `true`. "Skip for now" only dismisses it for the current session (handled in React state, not persisted). |
| Q3 | Should the baseline test be interruptible? (User closes browser mid-test.) | Assumption: no resume support in MVP. If interrupted, the test must be restarted. Partial results are not saved. |
| Q4 | Should "Retake Baseline Test" be available immediately after completing the test, or only after a cooldown? | Assumption: no cooldown for the adaptive baseline test. It can be retaken immediately. (The existing 180-day cooldown in `/api/baseline/` applies only to the old domain-score baseline and is unrelated.) |
| Q5 | What game order should the other 5 games follow after NBack and CardMemoryGame? | Assumption: alphabetical by component name — DigitSpan, GoNoGo, Stroop, SymbolMatching, VisualCategorisation. |
