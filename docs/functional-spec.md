# Functional Spec: Brain Training App

**Version:** 1.0
**Date:** 2026-04-16
**Status:** Approved
**Based on:** product-brief v1.0, spec-v0.8

---

## Changelog

| Version | Date | Summary |
|---|---|---|
| 1.0 | 2026-04-16 | Extracted and structured from spec-v0.8 |

---

## 1. User Stories

| ID | Story | Priority |
|---|---|---|
| US-01 | As a new user, I want to create an account so that my progress is saved. | Must Have |
| US-02 | As a new user, I want to complete a baseline assessment so the app knows my starting level. | Must Have |
| US-03 | As a returning user, I want to start a daily session so I can maintain my streak. | Must Have |
| US-04 | As a user mid-session, I want difficulty to adapt as I improve so I am always appropriately challenged. | Must Have |
| US-05 | As a user completing a session, I want to see my accuracy and streak so I understand my progress. | Must Have |
| US-06 | As a user, I want to log my sleep, exercise, and stress so these feed into my Brain Health Score. | Must Have |
| US-07 | As a user, I want to see per-domain trends over 30 days so I can track where I'm improving. | Must Have |
| US-08 | As a user, I want to read about the science behind the exercises so I can trust the app's claims. | Must Have |
| US-09 | As a user, I want to launch any individual exercise from the dashboard so I can practice freely. | Should Have |
| US-10 | As a user, I want to submit feedback from any page so I can report issues or suggestions. | Should Have |

---

## 2. Feature List (MVP)

### Authentication

**Description:** Email/password registration and login with explicit consent. Dual-token storage for cross-origin Railway deployment.

**Acceptance criteria:**
- Registration requires email, password, and explicit consent checkbox tick. Submission without consent is blocked.
- On successful login, a JWT is stored in an httpOnly cookie (`SameSite=None;Secure`) AND in `localStorage`.
- Every API request includes `Authorization: Bearer <token>` header via axios interceptor.
- On 401 response, `localStorage` token is cleared and user is redirected to `/login`.
- Logout clears the httpOnly cookie (server-side) and removes the `localStorage` token. Logout succeeds locally even if the server call fails.
- Password reset via email is in scope but the email send mechanism is a stub in v1.

---

### Baseline Assessment

**Description:** One-time assessment on first login. Covers all five cognitive domains. Takes ~10 minutes. Results seed adaptive difficulty starting points.

**Acceptance criteria:**
- Baseline is offered immediately after first login and on the onboarding flow.
- User cannot skip baseline without explicitly dismissing (confirming they understand they'll start at difficulty 1 in all domains).
- Baseline covers all five domains: Processing Speed, Working Memory, Attention & Inhibitory Control, Executive Function (hidden pending v1.1), Episodic Memory (hidden pending v1.1). At launch, three domains are active.
- On completion, results are stored in `baseline_results` and seed `domain_progress.current_difficulty` for each active domain.
- Baseline can be repeated after 6 months. The dashboard shows a prompt when eligible. Original baseline is always retained for long-term comparison.

---

### Daily Training Session

**Description:** Guided 15–20 minute session, 2–3 domains per session, interleaved exercises, adaptive difficulty.

**Acceptance criteria:**
- Session covers 2–3 domains per run (not all domains every session).
- Each session contains at minimum 2 task variants per domain visited.
- Exercises are interleaved (alternating domains), not blocked.
- Difficulty per exercise reflects the user's current `domain_progress.current_difficulty` for that domain.
- After each exercise, difficulty is updated using the 2-up/1-down staircase: correct twice in a row → difficulty +1; incorrect once → difficulty -1. Difficulty is clamped to 1–10.
- On session completion, navigate to Session Summary.
- Session creates a record in `sessions` and one `exercise_attempt` per exercise completed.
- Session counts toward cumulative training time (sum of `duration_seconds` across all sessions for this user).

---

### Cognitive Exercise Library

**Description:** Two task variants per domain, three domains at launch.

#### Processing Speed — Card Memory Task
- A grid of face-down cards is displayed. Cards are flipped one pair at a time.
- The user must find matching pairs by memory.
- Each round completes when all pairs are matched. A session contains minimum 3 rounds.
- Score = accurate moves / total moves × 100. Accurate move = correct pair selected on first attempt.
- `onComplete` payload: `{ rounds_played, total_moves, correct_moves, score }`.

#### Working Memory — Digit Span Task
- A sequence of digits is displayed one at a time, then hidden.
- User types the sequence from memory.
- Correct → sequence length increases. Two consecutive correct → difficulty +1. One incorrect → difficulty -1.
- Score = (correct recalls / total attempts) × 100.

#### Working Memory — N-back Sequence Task
- A sequence of items is shown. User indicates when the current item matches the item N positions back.
- N = difficulty level (N-1 for difficulty 1, up to N-4 for difficulty 7+).

#### Attention & Inhibitory Control — Stroop Task
- A color word is displayed in an ink color that differs from the word. User clicks the button matching the ink color.
- 8 trials per exercise. Options shown depend on difficulty (2 options at difficulty 1, up to 4 at difficulty 7+): `numOptions = min(4, 2 + floor(difficulty / 3))`.
- `onComplete` payload: `{ trials_presented, trials_correct, avg_response_ms }`.
- Scoring: exported as `computeStroopResult({ trialsPresented, trialsCorrect, responseTimes })`.

#### Attention & Inhibitory Control — Go/No-go Task
- Go stimuli (80%): user must tap/click as fast as possible.
- No-go stimuli (20%): user must withhold response.
- Score uses `computeResult` exported from `GoNoGo.jsx`: `accuracy = (hits + correctRejections - falseAlarms) / totalTrials`, clamped ≥0.
- `onComplete` payload: `{ accuracy, trials_presented, trials_correct, avg_response_ms, false_alarms, correct_rejections }`.

#### All domains — Shape Sort (Baseline + Free-play)
- User infers an abstract sorting rule from example pairs and applies it to new items.
- Used in baseline assessment across all active domains and available in free-play.

---

### Post-session Summary

**Description:** Displayed after every session (training, baseline, or free-play).

**Acceptance criteria:**
- Shows domains trained in this session.
- Shows **Accuracy** (labelled "Accuracy", not "Score") with sub-label: "X correct out of Y trials".
- Shows current streak count.
- Shows a one-line science-grounded observation about the result.
- Displays a prompt to log lifestyle habits (with a Skip option).
- A "Back to Dashboard" button returns to the dashboard.

---

### Progress Dashboard

**Description:** Main logged-in home screen.

**Acceptance criteria:**
- Displays: current streak, cumulative training time, Brain Health Score.
- Per-domain performance scores shown as separate cards (not collapsed).
- 30-day trend graph per domain (line graph, one point per session day).
- Milestone marker at 20 hours cumulative training time.
- Re-baseline prompt shown when user is ≥6 months from last baseline.
- Practice section shows all available exercises as tappable cards.
- **Mobile layout (< 768px):** sidebar hidden, BottomNav shown at bottom, all grid columns single-column, padding reduced to `--space-4`.
- **Desktop layout (≥ 768px):** sidebar visible, BottomNav hidden, grid columns multi-column.

---

### Brain Health Score

**Description:** Composite 0–100 score.

**Acceptance criteria:**
- Score = (cognitive_score × 0.6) + (lifestyle_score × 0.4), rounded to nearest integer.
- `cognitive_score`: average of current domain scores across all active domains.
- `lifestyle_score`: composite of last 7 days of lifestyle logs (exercise, sleep quality, stress, mood, social engagement).
- Recalculated after every session and every lifestyle log submission.
- Dashboard shows overall score plus breakdown by factor.

---

### Lifestyle Habit Logging

**Description:** Daily log, five factors.

**Acceptance criteria:**
- Accessible from dashboard and prompted after each session.
- Fields: exercise minutes (integer), sleep hours (decimal), sleep quality (1–5 rating), stress level (1–5), mood (1–5), social engagement (yes/no).
- One log per user per calendar day. Resubmitting overwrites the existing entry for that day.
- Submitted data stored in `lifestyle_logs`.

---

### In-App Feedback Capture

**Description:** Persistent floating button + post-session optional prompt.

**Acceptance criteria:**
- Floating button fixed at `bottom: --space-6, right: --space-6` on all authenticated pages.
- Clicking opens a modal with: text area (max 1000 characters), Submit button, Cancel button.
- On submit: "Thank you for your feedback" confirmation shown for 2 seconds, then auto-dismissed.
- Post-session prompt on Session Summary: optional text area with Submit and Skip buttons. Skip never blocks access to session results.
- All feedback stored in `feedback_entries` with `page_context` (current route) and `session_id` where applicable.

---

### Free-Play Mode

**Description:** Direct exercise launch from dashboard.

**Acceptance criteria:**
- Each exercise card in the Practice section launches that exercise directly.
- Free-play creates a real `session` record (type = 'free_play').
- Difficulty defaults to `domain_progress.current_difficulty` for that domain, or 1 if no baseline exists.
- All free-play attempts count toward cumulative training time and domain progress.
- On completion, navigate to Session Summary.

---

### Account Settings

**Acceptance criteria:**
- User can update email (requires password confirmation).
- User can change password (requires current password).
- User can set a daily reminder time (stored preference; send mechanism is v2).
- User can delete account — triggers deletion of all user data (GDPR erasure). Confirmation dialog required.

---

## 3. User Flows

### New User Onboarding

1. User visits app → sees marketing/welcome screen
2. Clicks "Get started" → Registration form (email, password, consent checkbox)
3. Submits → account created → auto-logged in
4. Onboarding intro screen: explains cognitive domains and what to expect
5. "Start baseline assessment" → Baseline assessment flow
6. Baseline completes → Session Summary (baseline results)
7. "Go to dashboard" → Dashboard

### Daily Training Session

1. User on Dashboard → clicks "Start Session"
2. Session created, exercise sequence determined (2–3 domains, interleaved)
3. For each exercise: instructions shown → user completes exercise → brief result shown → next exercise
4. All exercises complete → Session Summary shown
5. Lifestyle log prompt → user submits or skips
6. "Back to Dashboard" → Dashboard (streak and scores updated)

### Free-Play

1. User on Dashboard → clicks an exercise card in Practice section
2. Exercise loads at current difficulty
3. User completes exercise → Session Summary
4. "Back to Dashboard"

### Feedback Submission

1. User on any authenticated page → clicks floating feedback button
2. Modal opens → user types feedback (≤1000 chars) → clicks Submit
3. "Thank you" confirmation shown for 2 seconds → modal closes

---

## 4. Edge Cases and Error Handling

- **No baseline yet:** Domain progress defaults to difficulty 1. Dashboard shows "Complete your baseline" prompt.
- **Empty lifestyle log:** Brain Health Score lifestyle component uses 50 (neutral) until at least 3 days of logs exist.
- **Session interrupted:** Partial sessions are stored with `completed_at = null`. They do not count toward streak but do count toward cumulative time if >2 minutes.
- **API error during session:** Show "Something went wrong, please try again" inline. Do not lose exercise results already recorded.
- **Duplicate lifestyle log:** Overwrite existing entry for the same user+date. No error shown.
- **401 on any API call:** Clear localStorage token, redirect to `/login`.

---

## 5. Non-Functional Requirements

- **Performance:** Dashboard loads in <2 seconds on a standard mobile connection (3G or better).
- **Accessibility:** WCAG AA contrast for all text. All interactive elements keyboard-navigable. Focus outline visible (`2px solid --color-primary`).
- **Browser support:** Chrome and Safari (last 2 major versions each). Firefox supported but not primary.
- **Mobile:** Fully functional at 375px viewport width and above. Touch targets minimum 44×44px.
- **Security:** No hardcoded secrets. PostgreSQL queries use parameterised statements. No `dangerouslySetInnerHTML` in React. Auth cookie `httpOnly`, `Secure`, `SameSite=None`.

---

## 6. Open Questions

All open questions resolved at spec-v0.8. None blocking.
