# Pipeline Run Log — Brain Training App

Each entry is appended by the daily feedback pipeline task.

---

<!-- Entries appended below by the daily pipeline task -->

## Run — 2026-04-15 11:56 (local)

**Status:** SKIPPED — backend not running
**Feedback processed:** 0 new entries (0 total processed to date)
**Themes identified:** N/A
**Spec version:** unchanged
**Test result:** smoke test skipped
**New bugs logged:** none
**Actions needed from James:** Start the backend server (`DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload` from `apps/brain-training/`) before the next pipeline run so feedback can be fetched.
**Errors during run:** HTTP GET http://localhost:8000/api/feedback failed — connection refused (backend not running)

---

## Run — 2026-04-09 (automated)

**Status:** SKIPPED — backend not running
**Feedback processed:** 0 new entries (0 total processed to date)
**Themes identified:** N/A
**Spec version:** unchanged
**Test result:** smoke test skipped
**New bugs logged:** none
**Actions needed from James:** Start the backend server (`DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload` from `apps/brain-training/`) before the next pipeline run so feedback can be fetched.
**Errors during run:** HTTP GET http://localhost:8000/api/feedback failed — connection refused (backend not running)

---

## Run — 2026-04-09 21:01 (local)

**Status:** SKIPPED — backend not running
**Feedback processed:** 0 new entries (0 total processed to date)
**Themes identified:** N/A
**Spec version:** unchanged
**Test result:** smoke test skipped
**New bugs logged:** none
**Actions needed from James:** Start the backend server (`DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload` from `apps/brain-training/`) before the next pipeline run so feedback can be fetched.
**Errors during run:** HTTP GET http://localhost:8000/api/feedback failed — connection refused (exit code 7, backend not running)

---

## Run — 2026-04-10 (automated)

**Status:** SKIPPED — backend not running
**Feedback processed:** 0 new entries (0 total processed to date)
**Themes identified:** N/A
**Spec version:** unchanged
**Test result:** smoke test skipped
**New bugs logged:** none
**Actions needed from James:** Start the backend server (`DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload` from `apps/brain-training/`) before the next pipeline run so feedback can be fetched.
**Errors during run:** HTTP GET http://localhost:8000/api/feedback failed — connection refused (exit code 7, backend not running)

---

## Run — 2026-04-12 12:07 (local)

**Status:** SKIPPED — backend not running
**Feedback processed:** 0 new entries (0 total processed to date)
**Themes identified:** N/A
**Spec version:** unchanged
**Test result:** smoke test skipped
**New bugs logged:** none
**Actions needed from James:** Start the backend server (`DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload` from `apps/brain-training/`) before the next pipeline run so feedback can be fetched.
**Errors during run:** HTTP GET http://localhost:8000/api/feedback failed — connection refused (exit code 7, backend not running)

---

## Run — 2026-04-17 12:08 (local)

**Status:** SKIPPED — backend not running
**Feedback processed:** 0 new entries (0 total processed to date)
**Themes identified:** N/A
**Spec version:** unchanged
**Test result:** smoke test skipped
**New bugs logged:** none
**Actions needed from James:** Start the backend server (`DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload` from `apps/brain-training/`) before the next pipeline run so feedback can be fetched.
**Errors during run:** HTTP GET http://localhost:8000/api/feedback failed — connection refused (exit code 7, backend not running)

---

## Run — 2026-04-13 (automated)
**Status:** completed
**Feedback processed:** 7
**Changes applied:**
  - mobile-login-safari-bug: Login fails on mobile Safari after registration
  - session-scoring-accuracy: Session scoring appears lower than actual accuracy
  - card-memory-minimum-rounds: Ensure Card Memory has at least three rounds per session
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  - https://github.com/james-jxr/app-dev-capability/issues/9
**Spec version:** v0.7
**Test result:** PASSED (iteration 1): [2m   Duration [22m 3.22s[2m (transform 190ms, setup 185ms, import 239ms, tests 19ms, environment 2.27s)[22m
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-14 (automated)
**Status:** completed
**Feedback processed:** 6
**Changes applied:**
  - baseline-adaptive-length: Shorten baseline game to 10 turns max with adaptive sequence length (2-up/1-down)
  - session-scoring-inaccurate: Fix session scoring to use correct formula: accurate moves / total moves
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  - https://github.com/james-jxr/app-dev-capability/issues/14
  - https://github.com/james-jxr/app-dev-capability/issues/15
**Spec version:** v0.8
**Test result:** PASSED (iteration 1):    Duration  3.14s (transform 174ms, setup 177ms, import 235ms, tests 19ms, environment 2.22s)
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-14 (automated)
**Status:** completed
**Feedback processed:** 2
**Changes applied:**
  - baseline-rules-after-round: Show rule summary at end of each baseline round
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  (none)
**Spec version:** v0.8
**Test result:** PASSED (iteration 1):    Duration  2.88s (transform 161ms, setup 146ms, import 222ms, tests 18ms, environment 2.01s)
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-15 (automated)
**Status:** completed
**Feedback processed:** 3
**Changes applied:**
  - digit-span-scoring-formula: Update DigitSpan scoring to combine accuracy percentage and max length recalled
  - stroop-scoring-accuracy-bug: Fix inaccurate Stroop scoring — correct answers being counted as wrong
  - card-memory-session-score-bug: Fix CardMemory session score showing 0/1 instead of tracking all rounds played
  - baseline-card-colours-shapes: Improve card colour contrast and increase shape size in baseline card memory game
  - onboarding-intro-copy: Rewrite onboarding intro copy to mention academic basis, benefits, and regular practice
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  (none)
**Spec version:** v0.9
**Test result:** PASSED (iteration 1):    Duration  5.15s (transform 189ms, setup 332ms, import 278ms, tests 32ms, environment 3.70s)
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-21 (automated)
**Status:** completed
**Feedback processed:** 15
**Changes applied:**
  - sidebar-overlaps-mobile: Sidebar takes up most of the screen on mobile
  - remove-brain-icon-everywhere: Remove the brain icon from all screens
  - stroop-answer-button-colors: Stroop answer buttons should show word text in randomized colors
  - digit-span-progressive-length: Digit Span should start short, increase on correct, hold on first error, decrease on second consecutive error
  - card-game-five-turns: Card Memory Game should have exactly 5 turns per session
  - visual-categorisation-three-shorter-rounds: Visual Categorisation should have 3 rounds, each slightly shorter
  - digit-span-max-length-shows-zero: Digit Span score shows max length as 0 even when user answered correctly
  - nback-increase-max-to-5: N-Back should support up to 5-back
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  (none)
**Spec version:** v1.0
**Test result:** PASSED (iteration 3):    Duration  2.25s (transform 332ms, setup 377ms, import 387ms, tests 41ms, environment 4.12s)
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-22 (automated)
**Status:** completed
**Feedback processed:** 1
**Changes applied:**
  - card-memory-difficulty-not-advancing: Card Memory Game not advancing difficulty despite perfect performance
  - consistency-tracker-on-progress: Show a streak/consistency visual on the Progress page for the last two weeks
  - per-game-result-charts-on-progress: Show per-game result charts on Progress page titled 'Recent performance'
  - adaptive-difficulty-within-session: Show level-up message at end of session instead of mid-session difficulty adaptation
  - dashboard-visual-monotony: Add background graphics and subtle design elements to the Dashboard
  - showcase-games-on-landing: Show example games on the landing page before sign-up
  - visual-categorisation-three-shorter-rounds: Change Visual Categorisation to 3 rounds of 5 trials each
  - mindfulness-meditation-exercise: Add a standalone mindfulness/meditation exercise as a new 'Relaxation' domain
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  (none)
**Spec version:** v1.0
**Test result:** PASSED (iteration 1):    Duration  2.52s (transform 346ms, setup 374ms, import 452ms, tests 40ms, environment 4.58s)
**PR:** (none)
**Errors:** (none)
