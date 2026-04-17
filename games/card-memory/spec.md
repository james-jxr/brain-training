# Game Specification: Card Memory Game

**Spec Version:** spec-v0.1
**Date:** 2026-04-04
**Status:** Draft
**Brief Reference:** Card Memorisation Game (Symbol Baffled)

---

## Thinking Record

**Problem and user:** The Card Memory Game (Symbol Baffled) is an exercise for the Episodic Memory cognitive domain. It trains the ability to encode, maintain, and retrieve spatial-temporal memories of visual symbols. The target user is a brain-training app user (adult 25–80) who completes daily cognitive training sessions. This game sits alongside other memory and attention exercises.

**Minimum viable feature set:** A single game round with configurable difficulty (Easy/Medium/Hard), card memorisation phase, card shuffle animation, target identification phase, scoring, and integration with the existing session flow.

**Data needed:** Card game session state (difficulty, cards, target, player answer, response time), exercise result (score, accuracy, speed metrics).

**Main interactions:** (1) Show memorisation screen with face-up cards and countdown timer, (2) Animate card flip and shuffle, (3) Show target symbol prompt, (4) Accept player tap on card, (5) Reveal result and score, (6) Return to session flow.

**Not in scope:** Leaderboards, achievements, difficulty progression within a single session, sound effects, mobile-specific touch haptics, undo/retry within a single round, multiplayer modes.

**Genuine ambiguities:** (1) How many rounds per session? The brief shows a single round; the existing app structure suggests one exercise per session slot. Resolved: one round per game invocation, consistent with other exercises. (2) Should cards stay revealed after the guess, or flip back face-down? Resolved: reveal correct card and target for 2 seconds to show the result, then return to next exercise or session summary. (3) Shuffle animation timing: should it be instant or animated? Resolved: animated over 0.5–1 second to match app style. (4) How is speed bonus calculated? Resolved: linear scale from 0–100 bonus points over the available response window (varies by difficulty).

---

## 1. Purpose & Problem Statement

The Card Memory Game (Symbol Baffled) is a cognitive exercise that trains episodic memory — the ability to encode and retrieve the spatial locations of visual symbols. Players view a set of face-up cards displaying abstract coloured shapes, memorise their positions during a countdown timer, watch the cards flip and shuffle (with animated motion), and then identify and tap the card containing a target symbol. The game produces a score based on accuracy and response speed, integrating into the broader brain training app's session and scoring systems.

---

## 2. Target User

Users of the brain training app (aged 25–80, comfortable with digital products, cognitively healthy). Players expect:
- Mobile-friendly responsive design (playable on phone, tablet, desktop)
- Accessibility support (touch targets, readable text, colour contrast AA)
- Clear game state and feedback (no ambiguous card states, immediate result display)
- Integration with the app's visual design system (card-based UI, consistent typography, matching colour palette)

No prior gaming experience assumed. The game is a single-round exercise, not a prolonged gameplay loop.

---

## 3. User Stories

- As a player, I want to see the cards face-up with a countdown timer so that I have a clear signal of how much time I have to memorise.
- As a player, I want to watch the cards animate as they flip and shuffle so that I understand the positions are changing.
- As a player, I want to see a clear target symbol displayed (e.g., "Find the red triangle") so that I know what to look for.
- As a player, I want to tap a card and immediately see if my choice was correct so that I get instant feedback.
- As a player, I want to see my score (accuracy + speed bonus) so that I understand how well I performed.
- As a player, I want the game to fit into a training session alongside other exercises so that my cognitive domains are trained together.

---

## 4. MVP Feature List (In Scope)

1. **Card memorisation phase** — display 4 (Easy), 8 (Medium), or 12 (Hard) cards face-up, each showing a unique coloured abstract shape. A countdown timer displays the memorisation duration (10s Easy, 7s Medium, 5s Hard). Timer reaches zero, game automatically advances to the flip-and-shuffle phase.

2. **Card flip animation** — all cards simultaneously flip from face-up to face-down with a smooth 3D flip animation over 0.3 seconds.

3. **Card shuffle animation** — after flipping, cards rearrange to new positions. Easy difficulty: no shuffle. Medium difficulty: shuffle once (all cards animate to new grid positions over 0.5 seconds). Hard difficulty: shuffle twice (first shuffle 0.5s, then all cards shuffle again 0.5s later). Shuffle uses a deterministic algorithm to ensure reproducibility.

4. **Target symbol display** — after cards are face-down and shuffles complete, display a large, clear target symbol prompt (e.g., "Find the red triangle") occupying the top 20% of the screen. Include the shape icon and colour label.

5. **Card tap interaction** — player taps any face-down card. The card immediately reveals its symbol. If the symbol matches the target, the card is highlighted green; if not, it is highlighted red. Both the target and the tapped card remain visible for 2 seconds.

6. **Score calculation** — points awarded as: (1) Accuracy: 100 points if correct, 0 if incorrect. (2) Speed bonus: linear scale from 0–100 points. Fastest possible response (0.5s) = 100 bonus points. Time window extends based on difficulty (Easy: 15s window, Medium: 12s window, Hard: 10s window). Points = (100 - (response_time_ms / window_ms) * 100). Total score = accuracy_points + speed_bonus_points. Range: 0–200 points per round.

7. **Backend session integration** — create a new CardMemoryGameResult entity in the database. Backend route POST /api/sessions/{session_id}/game-result accepts game result (difficulty, card_count, correct, response_time_ms, score) and logs it to the ExerciseAttempt table with exercise_type="card_memory". Score is integrated into adaptive difficulty calculation for the Episodic Memory domain.

8. **Frontend component** — single reusable React component CardMemoryGame.jsx that accepts props: difficulty (string), onComplete (callback with result object). Component manages full game state and animation lifecycle.

9. **Game result reporting** — component calls onComplete with an object containing: { difficulty, correct (boolean), response_time_ms, score (0–200) }. The parent session component (e.g., ExerciseSelector or SessionFlow) receives this result and posts it to the backend.

---

## 5. Out of Scope

- **Multiple rounds per game invocation** — each exercise slot plays one round only.
- **Difficulty progression within a round** — difficulty is fixed at session start; no mid-game adjustment.
- **Customisable card symbols or themes** — cards always use the fixed shape/colour palette (5 shapes × multiple colours).
- **Animated hint or card peek** — once memorisation phase ends, no additional reveals until the player makes a choice.
- **Sound effects or audio feedback** — the game is silent (sound effects deferred to v2).
- **Leaderboards, achievements, or streaks specific to this game** — scoring integrates with the app's global Brain Health Score and session streak, not a per-game leaderboard.
- **Native app gesture support** — haptic feedback and iOS/Android specific interactions are out of scope.
- **Session save/resume** — games are not paused; a single round must be completed in one session.
- **Undo or retry within a round** — once a card is tapped, the result is final; no second chance.

---

## 6. Data Model

### Entity: CardMemoryGameResult

This entity extends the existing ExerciseAttempt model. A single game round produces one ExerciseAttempt record.

| Field | Type | Constraints |
|---|---|---|
| id | integer | primary key, auto-increment |
| session_id | integer | foreign key to Session, required |
| domain | string | always "episodic_memory" |
| exercise_type | string | always "card_memory" |
| difficulty | string | one of "easy", "medium", "hard"; required |
| card_count | integer | 4 (easy), 8 (medium), or 12 (hard); required |
| correct | boolean | true if player found correct card, false otherwise; required |
| response_time_ms | integer | milliseconds from target display to tap; required |
| score | integer | 0–200 points; required |
| created_at | timestamp | auto-set to current time |

Notes:
- All game results are logged to the existing ExerciseAttempt table with exercise_type="card_memory".
- The backend service AdaptiveDifficultyService will treat this exercise like any other, calculating a performance score and adjusting Episodic Memory difficulty.

---

## 7. API / Route Map

| Method | Path | Description | Auth required? |
|---|---|---|---|
| POST | /api/sessions/{session_id}/game-result | Log a card memory game result and return updated exercise attempt record | Y |
| GET | /api/sessions/{session_id}/next | (existing route, no change) Returns next exercise details including difficulty for card_memory | Y |

**Notes:**
- The POST /api/sessions/{session_id}/game-result route must accept a CardMemoryGameResult schema and create an ExerciseAttempt record with all fields populated.
- The GET /api/sessions/{session_id}/next route already exists and will correctly return exercise_type="card_memory" when it is the next exercise in the session.
- No new routes are strictly required; the game integrates via the existing exercise result logging route (or a minor extension of ExerciseAttempt to support the new fields).

---

## 8. Technology Stack

| Layer | Choice | Reason for choice / deviation |
|---|---|---|
| Frontend | React (existing) | Matches existing app stack. CardMemoryGame.jsx component integrated into the session flow. |
| Animation | CSS 3D Transforms + CSS Animations | No external animation library; leverages native browser capabilities for flip and shuffle animations. Simpler and faster than Framer Motion or Three.js. |
| Backend | FastAPI (existing) | Extends existing session and exercise logging routes. No new backend framework. |
| Database | SQLite / PostgreSQL (existing) | Reuses existing schema; CardMemoryGameResult data fits into ExerciseAttempt table with exercise_type discriminator. |
| Testing | pytest (existing) | Existing test infrastructure used for backend tests. Frontend testing via smoke test or visual inspection. |
| Key libraries | None new required | Uses existing react, fastapi, sqlalchemy. No new dependencies. |

---

## 9. File & Folder Structure

```
apps/brain-training/
├── frontend/
│   └── src/
│       └── components/
│           └── exercises/
│               └── CardMemoryGame.jsx       (new)
├── backend/
│   ├── models/
│   │   └── (ExerciseAttempt updated to support card_memory fields)
│   ├── routers/
│   │   └── sessions.py                     (updated to handle card_memory results)
│   ├── schemas/
│   │   └── (ExerciseAttemptCreate updated to include difficulty, card_count, correct, response_time_ms, score)
│   └── services/
│       └── (AdaptiveDifficultyService uses existing scoring logic)
└── games/card-memory/
    └── spec.md                             (this file)
```

---

## 10. Non-Functional Requirements

- **Responsiveness:** Game must display correctly on screens 320px wide (mobile) to 1920px wide (desktop). Card grid scales proportionally. Touch targets (cards) are minimum 44px × 44px on mobile.

- **Performance:** Card flip and shuffle animations must complete in under 1 second with smooth 60 FPS on standard devices (iPhone 12, Android Galaxy S10 or newer, desktop with 2-year-old GPU). No frame drops during animation.

- **Accessibility:** (1) All text (timer, target symbol, score) has WCAG AA colour contrast (4.5:1 minimum). (2) Cards are distinguishable by shape alone (colour is secondary). (3) Cards have focus indicators for keyboard navigation (tab and Enter to select). (4) Game state and results announced to screen readers.

- **Browser / environment support:** Chrome, Safari, Firefox latest versions. Mobile browsers (Chrome Mobile, Safari iOS 13+). No IE11 support.

- **Error handling:** If a card is tapped twice, the second tap is ignored. If the response window expires (e.g., player leaves the page), the game times out gracefully and returns a null result. Network errors on result POST are retried once automatically.

- **Data integrity:** All game results are persisted server-side; no data loss on client refresh or navigation away.

---

## 11. Open Questions

None — all ambiguities have been resolved in the Thinking Record section above. The spec is ready to build from.

