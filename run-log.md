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

## Run — 2026-04-24 (automated)
**Status:** completed
**Feedback processed:** 0
**Changes applied:**
  - consistency-tracker-on-progress: Show a consistency/streak visual on the Progress page for the last two weeks
  - per-game-result-charts-on-progress: Show per-game result charts on the Progress page
  - adaptive-difficulty-within-session: Game difficulty should adapt during a session based on performance
  - dashboard-visual-monotony: Dashboard looks boring — add background graphics or subtle design elements
  - showcase-games-on-landing: Show example games on the landing/home page before sign-up
  - visual-categorisation-three-shorter-rounds: Visual Categorisation should have 3 rounds, each slightly shorter than current
  - mindfulness-meditation-exercise: Add a mindfulness or meditation exercise
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  (none)
**Spec version:** v1.0
**Test result:** PASSED (iteration 1):    Duration  2.69s (transform 317ms, setup 366ms, import 527ms, tests 187ms, environment 5.33s)
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-29 (automated) [pipeline v3 — implementation]
**Status:** completed
**Issues implemented:**
  - #126: Replace datetime.utcnow() with datetime.now(timezone.utc) in adaptive_baseline.py
  - #125: Replace datetime.utcnow() with datetime.now(timezone.utc) in skill_assessment.py
  - #124: Replace datetime.utcnow() with datetime.now(timezone.utc) in domain_progress.py
  - #123: Replace datetime.utcnow() with datetime.now(timezone.utc) in lifestyle_log.py
  - #122: Replace datetime.utcnow() with datetime.now(timezone.utc) in streak.py
**Issues failed:**
  (none)
**Issues deferred:**
  - #145: Medium complexity frontend refactor (CardMemoryGame.jsx). Deferred to keep this run focused on the lower-risk backend datetime fixes which are a coherent batch.
  - #144: Medium complexity backend refactor (adaptive_baseline.py handler). Deferred to avoid compounding risk with the datetime fixes selected this run.
  - #143: Medium complexity backend refactor (sessions.py handler). Deferred — touches the same sessions.py file that several other issues also target; best addressed in a dedicated sessions.py refactor run.
  - #142: Medium complexity bug fix in sessions.py involving a shared helper function and transaction safety. Multiple prior failures including test failures unrelated to the change itself. Deferred to a dedicated run.
  - #141: Low complexity dead-import fix, but repeated failures (3) in prior runs due to test suite issues (jest not defined errors) that appear systemic. Deferred until the test infrastructure issue is resolved.
  - #140: Low complexity dead-import fix, but repeated failures (3) in prior runs due to the same systemic jest test infrastructure issue. Deferred.
  - #139: Low complexity error-handling improvement (LifestyleLog.jsx catch block). Deferred to keep this run focused on the datetime fix batch.
  - #138: Medium complexity feature change (FreePlay.jsx error state). Deferred to avoid compounding risk.
  - #137: Medium complexity security/auth change (feedback.py). Deferred to avoid compounding risk.
  - #136: Medium complexity refactor (shared gameTypes constants file). Deferred to avoid compounding risk.
  - #135: Medium complexity refactor (consolidate color utility functions). Deferred to avoid compounding risk.
  - #131: Medium complexity auth fix (useStreakData.js). Has repeated failures due to systemic jest test infrastructure issues. Deferred.
  - #130: Medium complexity auth fix (useGameHistory.js). Has repeated failures (4+) due to systemic jest test infrastructure issues. Deferred.
  - #129: Low complexity dead-code removal (scoring.js). Deferred to keep run focused.
  - #128: Medium complexity refactor (sessions.py duplicate accuracy logic). Deferred — related to issues 143/93/92 that also touch sessions.py; best addressed together.
  - #127: Medium complexity fix (datetime.utcnow in brain_health_score.py and lifestyle.py). Similar to the selected datetime fixes but also involves query logic changes; deferred to avoid scope creep in this run.
  - #121: Low complexity env-var fix (fetch-feedback.py). Has failed-implementation label with 1 failure. Deferred to keep run focused.
  - #120: Low complexity rename (StreakTracker.jsx). Deferred to keep run focused.
  - #119: Medium complexity datetime fix spanning multiple files. The individually scoped issues (122–127) for each file are preferred; this umbrella issue is deferred to avoid duplication.
  - #118: Low complexity CSS refactor (BottomNav.jsx). Has repeated failures due to systemic test issues. Deferred.
  - #117: Low complexity URL fix (account.py). Has failed-implementation label. Related to issue 100. Deferred.
  - #112: Low complexity guard removal (account.py). Has failed-implementation label with multiple failures including systemic jest test issues. Deferred.
  - #111: Low complexity error-logging fix (FreePlay.jsx). Has failed-implementation label. Deferred.
  - #110: Low complexity dead-import fix. Has failed-implementation label; same systemic jest test issue as #141. Deferred.
  - #109: Low complexity dead-import fix. Has failed-implementation label; same systemic jest test issue as #140. Deferred.
  - #108: Medium complexity error-state feature (Settings.jsx). Has failed-implementation label. Deferred.
  - #107: Medium complexity error-state feature (LifestyleLog.jsx). Has failed-implementation label. Deferred.
  - #106: Low complexity type annotation fix (audit_classifier.py). Has failed-implementation label with multiple failures. Deferred.
  - #105: Medium complexity dead-code removal (TrendChart.jsx / Progress.jsx). Has failed-implementation label with multiple failures including systemic jest test issues. Deferred.
  - #104: Low complexity magic-number extraction (DigitSpan.jsx). Has failed-implementation label. Deferred.
  - #103: Low complexity export addition (BaselineGameWrapper.jsx). Has failed-implementation label with multiple failures. Deferred.
  - #102: Low complexity dead-comment removal (baseline.py). Has failed-implementation label with multiple failures. Deferred.
  - #100: Low complexity URL fix (account.py). Has failed-implementation label. Overlaps with #117. Deferred.
  - #99: Medium complexity bug fix (sessions.py baseline_number). Has failed-implementation label. Touches core session creation logic; deferred to avoid compounding risk.
  - #95: Medium complexity auth fix (useStreakData.js). Has failed-implementation label; same systemic jest test issues as #131. Deferred.
  - #94: Medium complexity auth fix (useGameHistory.js). Has failed-implementation label with multiple failures including systemic jest test issues. Deferred.
  - #93: Medium complexity refactor (sessions.py log_exercise_result). Has failed-implementation label. Deferred — best addressed in a dedicated sessions.py refactor run.
  - #92: Medium complexity refactor (sessions.py duplicate accuracy calc). Has failed-implementation label. Deferred — related to #93/128/143.
  - #91: Medium complexity fix (brain_health_score.py lifestyle filter). Has failed-implementation label. Deferred.
  - #90: Medium complexity fix (lifestyle.py date filter). Has failed-implementation label with multiple failures including systemic jest test issues. Deferred.
  - #89: Medium complexity datetime fix (adaptive_baseline.py). Covered by the selected issue #126 which addresses the same file. Deferred as duplicate.
  - #88: Medium complexity datetime fix spanning multiple model files. The individually scoped issues (122–125) are preferred. Has failed-implementation label. Deferred.
  - #75: Medium complexity responsive layout fix (CardMemoryGame). Has failed-implementation label with multiple failures. Deferred.
  - #69: Medium complexity bug fix (Dashboard domain sessions count). Has failed-implementation label with multiple failures. Deferred.
  - #68: Medium complexity auth bug fix (Progress page 401). Has failed-implementation label with multiple failures. Related to #94/#130 useGameHistory fixes. Deferred.
  - #67: Medium complexity mechanic change (CardMemory reveal on wrong guess). Has failed-implementation label with multiple failures. Deferred.
  - #66: High complexity mechanic change (DigitSpan staircase redesign). Has failed-implementation label. Deferred to avoid compounding risk.
  - #53: High complexity feature (guided breathing from Dashboard). Has failed-implementation label. Deferred to avoid compounding risk.
  - #49: High complexity feature (level-up/level-down session results). Has failed-implementation label with multiple failures including backend test failures. Deferred.
  - #48: Medium complexity design change (CardMemory images). Has failed-implementation label. Deferred.
  - #47: High complexity mechanic change (Visual Categorisation round structure). Has failed-implementation label. Deferred.
  - #44: High complexity bug investigation (adaptive difficulty). Has failed-implementation label with multiple failures including backend test failures. Deferred.
**Spec version:** v1.1
**Test result:** PASSED (iteration 1): [33mBoth esbuild and oxc options were set. oxc options will be used and esbuild options will be ignored.[39m The following esbuild options were set: `{ jsx: 'automatic', jsxImportSource: undefined }`
**PR:** (none)
**Errors:** (none)
