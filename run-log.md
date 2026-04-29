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

## Run — 2026-04-29 (automated) [pipeline v3 — implementation] (PR #199)
**Status:** completed
**Issues implemented:**
  - #194: Remove unused GAME_TYPE_LABELS dead code from TrendChart.jsx
  - #193: Remove unused GAME_TYPE_LABELS dead code from Progress.jsx
  - #185: Replace magic numbers in StreakManagerService with named constants
  - #160: Replace datetime.utcnow() with datetime.now(timezone.utc) in lifestyle.py router
  - #127: Replace datetime.utcnow() with datetime.now(timezone.utc) in brain_health_score.py
**Issues failed:**
  (none)
**Issues deferred:**
  - #195: Requires a human decision: whether to fully implement multi-file support for SPEC_CANDIDATES/DESIGN_CANDIDATES in review_pipeline.py or simplify to a single path. The classifier flagged it as needing human review.
  - #190: Medium complexity rename across 5 files (synthesizer.py, audit_classifier.py, prioritiser.py, design_reviewer.py, pipeline_reviewer.py). Touching that many feedback-agent files at once risks compounding with other changes; deferred to a focused rename run.
  - #189: Duplicate BASELINE_LEVEL_TO_DIFFICULTY constant across FreePlay.jsx and Session.jsx — linked to issue #188 (same finding). Deferred to avoid partial extraction without the full shared-constants refactor.
  - #188: BASELINE_LEVEL_TO_DIFFICULTY duplication across three files (BaselineGameWrapper.jsx, Session.jsx, FreePlay.jsx). Medium complexity shared-constants refactor; deferred to a dedicated run to avoid partial state.
  - #187: Medium complexity — adding named constants for magic floats/ints across multiple methods in brain_health_score.py. Deferred to avoid scope creep alongside the utcnow fix already selected for that file.
  - #186: Medium complexity — named constants for magic numbers in adaptive_difficulty.py across two methods. Deferred; can be combined with a future adaptive_difficulty refactor run.
  - #184: Requires confirming whether calculateBrainHealthScore in scoring.js is truly dead (never imported). Related to issues #129 and #135 which have failed implementations. Deferred until the scoring.js test failures seen in related issues are understood.
  - #183: Magic number 8 in Stroop.jsx — low complexity but part of a cross-file pattern (also SymbolMatching.jsx, DigitSpan.jsx). Better addressed as a batch refactor with issue #182 and #104 in a dedicated run.
  - #182: Magic number 8 in SymbolMatching.jsx — should be addressed in the same run as Stroop.jsx (#183) and DigitSpan.jsx (#104) for consistency. Deferred to a batch run.
  - #178: BottomNav.jsx inline style duplication — overlaps with issue #118 (same file, same problem). Both should be fixed together in one run to avoid conflicts.
  - #177: BaselinePrompt.jsx gradient uses hardcoded #8b5cf6 — low complexity design token fix, but deferred to a dedicated design token cleanup run alongside issues #176, #175, #174, #173, #172, #171.
  - #176: Stroop.jsx colorMap hardcoded hex — part of a cluster of design token fixes (#171–#177). Deferred to a dedicated design token run.
  - #175: VisualCategorisation.jsx COLORS array hardcoded hex — part of the design token cluster. Deferred to a dedicated design token run.
  - #174: CardMemoryGame.jsx colors array hardcoded hex — part of the design token cluster. Deferred to a dedicated design token run.
  - #173: GoNoGo.jsx hardcoded hex values — part of the design token cluster. Deferred to a dedicated design token run.
  - #172: DomainScoreCard.jsx hardcoded hex values — covered by the design agent decision in issue #135. Part of the design token cluster. Deferred.
  - #171: BrainHealthGauge.jsx hardcoded hex values — covered by the design agent decision in issue #135. Part of the design token cluster. Deferred.
  - #168: useGameHistory.js naming and localStorage/sessionStorage inconsistency — overlaps with issues #130 and #94 which are more precisely described. Deferred to avoid conflicting changes to the same file.
  - #167: SessionPlannerService dead/no-op logic — requires careful analysis of whether the condition is wrong or intentional. Medium risk for a logic change; requires human review of intent.
  - #166: review_pipeline.py >400 lines refactor — high complexity, touches core pipeline orchestration. Deferred to avoid compounding risk.
  - #165: implementation_pipeline.py >500 lines refactor — high complexity, core pipeline orchestration. Deferred to a dedicated refactor run.
  - #164: NBack.jsx >200 lines complexity refactor — medium/high complexity frontend component restructure. Deferred to a dedicated component refactor run.
  - #163: VisualCategorisation.jsx >300 lines complexity refactor — high complexity. Related to issue #47 (mechanic change) which also affects this component. Should be addressed after #47 is stable.
  - #162: GoNoGo.jsx >200 lines complexity refactor — medium complexity component restructure. Deferred to a dedicated exercise component refactor run.
  - #154: skill_assessment.py datetime.utcnow column default — overlaps with issue #88 (broader model-level fix across multiple model files). Should be fixed together in a batch run.
  - #152: Onboarding.jsx handleComplete missing error state — medium complexity UX change requiring error state design. Deferred; no design spec provided yet.
  - #146: Pipeline version upgrade — administrative action requiring running orchestrator.py from Agent Central, not a code change. Not implementable by the build agent.
  - #145: CardMemoryGame.jsx complexity refactor — 1 prior failed empty response. Medium complexity component restructure; deferred to a run focused on component refactoring.
  - #144: adaptive_baseline.py handler refactor — 1 prior failed empty response. Medium complexity; deferred.
  - #143: sessions.py log_exercise_result handler refactor — 1 prior failed empty response. Related to issues #92, #93, #128 which all touch sessions.py. Should be addressed as a batch in one run.
  - #142: sessions.py baseline_number hardcoded to 1 — 4 failed attempts including test failures with jest-not-defined errors. The test infrastructure issue appears unresolved; deferred until test environment is stable.
  - #141: SkillProfileScreen.jsx unused Badge import — 4 failed attempts, failed_impl_count=1 with label. Persistent test failures (jest not defined) suggest a test config issue. Deferred until test environment is resolved.
  - #140: BaselineTransition.jsx unused useEffect import — 3 failed attempts. Persistent jest-not-defined test failures unrelated to this change. Deferred until test environment is resolved.
  - #139: LifestyleLog.jsx error message extraction — 1 prior failed empty response. Low complexity; can be retried but deferred this run to keep scope focused.
  - #138: FreePlay.jsx session start error surfacing — design agent decision provided. Medium complexity UX change; deferred to a dedicated error-handling run.
  - #137: feedback.py authentication requirement — design agent decision provided. Medium complexity backend security change touching auth and data model. Deferred to a dedicated security fix run.
  - #136: GAME_TYPE_LABELS shared constants file — failed_impl_count=1. Design agent decision provided. Medium complexity cross-file refactor; deferred until the simpler dead-code removals (#193, #194) are merged first.
  - #135: getDifficultyColor/getGaugeColor consolidation — failed_impl_count=1, persistent scoring.js test failures (TypeError: calculateBrainHealthScore is not a function). Test environment issue blocks this. Deferred.
  - #131: useStreakData.js localStorage/axios fix — 3 failed attempts with jest-not-defined test errors. Overlaps with #95 (same issue, different audit number). Deferred until test environment is stable.
  - #130: useGameHistory.js localStorage/axios fix — 4 failed attempts with persistent jest-not-defined errors. Deferred until test environment is resolved.
  - #129: calculateBrainHealthScore dead code removal — failed_impl_count=1, persistent scoring.js TypeError. Test references this function; deleting it breaks tests. Deferred until scoring.js tests are updated.
  - #128: card_memory accuracy calculation duplication in sessions.py — 1 prior failed empty response. Part of the sessions.py cluster (#92, #93, #143). Should be addressed as a batch.
  - #121: fetch-feedback.py hardcoded BACKEND_URL — failed_impl_count=1, 5 failed attempts including backend test failures and scoring.js TypeErrors. Infrastructure issues compound this. Deferred.
  - #120: StreakTracker.jsx formatMonthDay rename — 1 prior failed empty response. Low complexity; can be retried in a future low-risk run.
  - #119: datetime.utcnow model files batch fix — failed_impl_count=1, persistent scoring.js TypeErrors in test run. The broader model fix should be done separately; the lifestyle.py and brain_health_score.py fixes selected this run are the highest-impact subset.
  - #118: BottomNav.jsx inline styles to CSS class — 2 failed attempts with VisualCategorisation test failure (onComplete called 4 times instead of 1). The VisualCategorisation test failure appears to be a pre-existing bug blocking this file. Deferred.
  - #117: account.py doubled /account path — failed_impl_count=1, 4 failed attempts with persistent jest-not-defined errors. Overlaps with #100 (same finding). Deferred until test environment is resolved.
  - #112: account.py misleading if(response) guard — failed_impl_count=1, 4 failed attempts. Related to #117 (same file). Deferred to a batch fix with #100 and #117.
  - #111: FreePlay.jsx silent catch blocks — failed_impl_count=1. Related to issue #138 (FreePlay error surfacing with design spec). Should be addressed together with #138.
  - #110: SkillProfileScreen.jsx unused Badge import — failed_impl_count=1, same as #141 (duplicate finding). Persistent jest-not-defined test failures. Deferred.
  - #109: BaselineTransition.jsx unused useEffect import — failed_impl_count=1, same as #140. Persistent test failures. Deferred.
  - #108: Settings.jsx silent error swallow — failed_impl_count=1. Design agent decision provided (detailed error card spec). Medium complexity UX; deferred to a dedicated error-handling run.
  - #107: LifestyleLog.jsx silent loadTodayData error — failed_impl_count=1. Design agent decision provided (inline warning banner spec). Medium complexity UX; deferred to a dedicated error-handling run.
  - #106: audit_classifier.py return type annotation fix — failed_impl_count=1, 4 failed attempts. Some failures due to VisualCategorisation test bug and backend test failures. Low complexity change but blocked by test environment issues.
  - #105: GAME_TYPE_LABELS dead code removal — failed_impl_count=1, 3 failed attempts. Replaced by issues #193 and #194 which are cleaner, more focused versions of the same fix. The simpler targeted removals are selected instead.
  - #104: DigitSpan.jsx MAX_TRIALS named constant — failed_impl_count=1. Part of a cross-file pattern with Stroop.jsx (#183) and SymbolMatching.jsx (#182). Should be addressed as a batch.
  - #103: BaselineGameWrapper.jsx export isRoundCorrect — failed_impl_count=1, 4 failed attempts including VisualCategorisation test bug and backend test failures blocking the run. Deferred until test environment is stable.
  - #102: baseline.py truncated comment removal — failed_impl_count=1, 4 failed attempts with persistent test failures. Very low risk change but blocked by test environment issues.
  - #100: account.py doubled /account path — failed_impl_count=1, duplicate of #117. Deferred with #117.
  - #99: sessions.py baseline_number always 1 — failed_impl_count=1. Design agent decision provided. Medium complexity backend fix; related to #142. Should be addressed in the same run as #142.
  - #98: DomainScoreCard.jsx getDifficultyColor hardcoded hex — design agent provided partial unparseable response. Related to #97 and #135. Deferred to the design token cluster run.
  - #97: BrainHealthGauge.jsx getGaugeColor hardcoded hex — design agent provided partial unparseable response. Related to #98 and #135. Deferred to the design token cluster run.
  - #95: useStreakData.js localStorage/axios fix — failed_impl_count=1. Duplicate of #131. Persistent jest-not-defined test failures. Deferred.
  - #94: useGameHistory.js localStorage/axios fix — failed_impl_count=1. Duplicate of #130. Persistent jest-not-defined test failures. Deferred.
  - #93: sessions.py log_exercise_result over 40 lines — failed_impl_count=1. Part of the sessions.py cluster with #92, #128, #143. Should be addressed as a batch.
  - #92: sessions.py duplicate card_memory accuracy block — failed_impl_count=1. Part of sessions.py cluster. Deferred to batch run.
  - #91: brain_health_score.py calculate_lifestyle_score datetime.utcnow — failed_impl_count=1. The utcnow fix for brain_health_score.py is being handled in the selected issue #127 which covers the same file. Deferred as duplicate coverage.
  - #90: lifestyle.py get_lifestyle_history datetime filter — failed_impl_count=1. The fix for this is covered in selected issue #160 which addresses the same file and same root cause. Deferred as duplicate coverage.
  - #89: adaptive_baseline.py datetime.utcnow — failed_impl_count=1. Medium complexity; can be addressed in a future batch datetime fix run covering remaining occurrences.
  - #88: Multiple model files datetime.utcnow batch fix — failed_impl_count=1, 3 failed attempts. High scope (4 model files). Deferred to a dedicated model-level datetime fix run.
  - #75: CardMemory grid mobile overflow — failed_impl_count=1, 6 failed attempts including infrastructure failures (pytest missing) and adaptive_difficulty signature errors from other changes. High priority user bug but blocked by compound test failures. Deferred.
  - #69: Dashboard domain boxes show 0 sessions — failed_impl_count=1, 5 failed attempts including infrastructure failures. Medium complexity bug fix; deferred until test environment is stable.
  - #68: Progress page 401 error on game history — failed_impl_count=1, 6 failed attempts. Root cause (localStorage vs sessionStorage) is the same as #130/#94. Deferred until that cluster is resolved.
  - #67: CardMemory reveal correct card on wrong guess — failed_impl_count=1, 5 failed attempts. Medium complexity mechanic change; infrastructure issues have been cited as fixed but most recent attempt still produced empty response. Deferred.
  - #66: DigitSpan staircase starting at 5 digits — failed_impl_count=1. Medium complexity mechanic change touching both frontend component and potentially backend. Deferred.
  - #53: Guided breathing session from Dashboard — failed_impl_count=1. Product owner decisions have been provided but implementation is complex (new session type, lifestyle logging integration, Dashboard quick-launch). High complexity feature; deferred to a dedicated feature run.
  - #49: Level Up/Down message on session results — failed_impl_count=1, 3 failed attempts. Product owner decisions provided but touches adaptive_difficulty.py, sessions.py, and SessionSummary.jsx. Medium/high complexity; deferred.
  - #48: CardMemory more interesting images (letters/numbers) — failed_impl_count=1. Product owner decisions provided. Medium complexity design change. Deferred to a dedicated visual/design run.
  - #47: Visual Categorisation three rounds structure — failed_impl_count=1. Product owner decisions provided. High complexity mechanic change affecting both frontend and potentially backend. Deferred to a dedicated mechanic refactor run.
  - #44: Adaptive difficulty not progressing across sessions — failed_impl_count=1, 3 failed attempts including adjust_difficulty_in_session signature errors. High priority bug but the previous attempt introduced a breaking signature change. Deferred until the signature issue is investigated.
**Spec version:** v1.1
**Test result:** PASSED (iteration 1):     at [90mfile:///home/runner/work/brain-training/brain-training/frontend/[39mnode_modules/[4m@vitest/runner[24m/dist/chunk-artifact.js:2955:64
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-29 (automated) [pipeline v3 — implementation] (PR #203)
**Status:** completed
**Issues implemented:**
  - #102: Remove truncated dead comment in baseline.py
  - #140: Remove unused useEffect import from BaselineTransition.jsx
  - #110: Remove unused Badge import from SkillProfileScreen.jsx
  - #121: Read BACKEND_URL from environment variable in fetch-feedback.py
  - #106: Fix return type annotation and docstring in audit_classifier.py
  - #88: Replace datetime.utcnow with datetime.now(timezone.utc) in model defaults
  - #90: Fix lifestyle history filter to use logged_date instead of created_at
  - #104: Extract MAX_TRIALS constant in DigitSpan.jsx, SymbolMatching.jsx, and Stroop.jsx
**Issues failed:**
  (none)
**Issues deferred:**
  - #195: Audit finding flagged for human review — involves an architectural decision about SPEC_CANDIDATES/DESIGN_CANDIDATES list structure that agents cannot make autonomously.
  - #190: Naming refactor across 5+ files (synthesizer.py, audit_classifier.py, prioritiser.py, design_reviewer.py, pipeline_reviewer.py) — medium complexity touching pipeline internals; deferred to avoid compounding risk with selected backend fixes.
  - #189: Duplicate constant consolidation in FreePlay.jsx — depends on shared constants file creation which overlaps with issue #188; deferred to keep run focused.
  - #188: DRY refactor requiring creation of a new shared constants file and updates to Session.jsx, FreePlay.jsx, and BaselineGameWrapper.jsx — medium complexity, deferred to a dedicated run.
  - #187: Magic numbers in brain_health_score.py — medium complexity, touches scoring logic; deferred to avoid compounding risk with other backend changes in this run.
  - #186: Magic numbers in adaptive_difficulty.py — medium complexity; deferred to avoid compounding risk with other backend service changes.
  - #184: Dead code in frontend/src/utils/scoring.js — has a known test blocker (scoring.test.js expects calculateBrainHealthScore to be a function) that has caused repeated failures; deferred until test suite issue is resolved.
  - #183: Magic number in Stroop.jsx — overlaps with issue #104 which handles this in the same file; issue #104 is selected, making this redundant for this run.
  - #182: Magic number in SymbolMatching.jsx — overlaps with issue #104 which handles this in the same file; issue #104 is selected, making this redundant for this run.
  - #178: BottomNav.jsx style function extraction — overlaps with issue #118 which handles the same file; deferring to keep BottomNav changes cohesive in a future run.
  - #177: Hardcoded hex in BaselinePrompt.jsx gradient — low severity design inconsistency; deferred to a dedicated design token cleanup run.
  - #176: Hardcoded hex colors in Stroop.jsx colorMap — part of a broader design token cleanup needed across multiple exercise files; deferred to a dedicated run.
  - #175: Hardcoded hex colors in VisualCategorisation.jsx — part of broader design token cleanup; deferred.
  - #174: Hardcoded hex colors in CardMemoryGame.jsx — part of broader design token cleanup; deferred.
  - #173: Hardcoded hex colors in GoNoGo.jsx — part of broader design token cleanup; deferred.
  - #172: Hardcoded hex colors in DomainScoreCard.jsx — part of broader design token cleanup; deferred.
  - #171: Hardcoded hex colors in BrainHealthGauge.jsx — overlaps with issues #97 and #98 which cover the same files; deferred pending those issues.
  - #168: Naming fix in useGameHistory.js — overlaps with issue #130 which handles the same file's auth fix; deferred to avoid conflicting changes to the same file.
  - #167: Dead/no-op logic in session_planner.py — requires careful inspection of the ternary condition to determine correct fix; deferred to avoid inadvertent behaviour change.
  - #166: review_pipeline.py over 400 lines — high complexity refactor of pipeline internals; deferred to avoid compounding risk.
  - #165: implementation_pipeline.py over 500 lines — high complexity refactor; deferred to its own dedicated run.
  - #164: NBack.jsx complexity refactor — high complexity frontend change touching deeply nested useEffect chains; deferred.
  - #163: VisualCategorisation.jsx 300+ line refactor — high complexity; has a known test failure (onComplete called 4 times instead of 1) that has blocked previous attempts; deferred.
  - #162: GoNoGo.jsx refactor — medium-high complexity; deferred to avoid compounding risk.
  - #154: Duplicate of issue #88 (datetime.utcnow in skill_assessment.py) — issue #88 is selected and covers this file.
  - #152: Onboarding.jsx error handling — medium complexity UI change; deferred to allow backend fixes to land first.
  - #146: Pipeline version upgrade — administrative/environmental issue requiring CLI command from Agent Central, not a code change.
  - #145: CardMemoryGame.jsx large refactor — medium-high complexity; has had failed implementation attempts; deferred.
  - #144: adaptive_baseline.py handler refactor — medium complexity; deferred to avoid compounding risk with backend changes in this run.
  - #143: sessions.py log_exercise_result handler refactor — medium-high complexity; overlaps with issues #92, #93, #128 covering the same file; better handled together in a dedicated run.
  - #142: baseline_number auto-increment in sessions.py — medium complexity with design decision resolved; overlaps with issue #99 covering same logic; deferred to coordinate with #99.
  - #141: Duplicate of issue #110 (unused Badge import in SkillProfileScreen.jsx) — #110 is selected.
  - #139: LifestyleLog.jsx error message improvement — low complexity but overlaps with issue #107 covering the same file's error handling; deferred to handle together.
  - #138: FreePlay.jsx session-start error handling — medium complexity; has design decision from interaction design agent; deferred to keep this run focused on backend fixes.
  - #137: feedback.py authentication change — medium complexity security fix; has had repeated failures; deferred to a dedicated run.
  - #136: GAME_TYPE_LABELS consolidation — medium complexity with design decision resolved; failed-implementation label present; deferred.
  - #135: getDifficultyColor/getGaugeColor deduplication — medium complexity; failed-implementation label present; has known test failures (scoring.test.js); deferred.
  - #131: useStreakData.js auth fix — overlaps with issue #95 and #130 covering same pattern; all three should be handled together in one run.
  - #130: useGameHistory.js auth fix — medium complexity; has had repeated failures with test suite issues (jest not defined); deferred until test infrastructure issues are resolved.
  - #129: Dead calculateBrainHealthScore in scoring.js — has known test blocker (scoring.test.js expects the function); failed-implementation label; deferred.
  - #128: Duplicate card_memory accuracy calculation in sessions.py — overlaps with issues #92 and #93 covering same file; deferred to handle all sessions.py refactors together.
  - #120: formatMonthDay rename in StreakTracker.jsx — low priority naming change; deferred.
  - #119: Duplicate of issue #88 which is selected — #88 covers all datetime.utcnow() model files including baseline_result.py.
  - #118: BottomNav.jsx inline styles to CSS class — low complexity but has had repeated test failures (VisualCategorisation.test.jsx unrelated failure blocking CI); deferred.
  - #117: account.py double-segment URL fix — failed-implementation label; medium risk as URL change could break frontend API calls; deferred.
  - #112: Remove misleading if (response) guard in account.py — failed-implementation label (1 time); low complexity but overlaps with issue #117 in same file; deferred.
  - #111: FreePlay.jsx silent catch blocks — failed-implementation label; overlaps with issue #138 covering broader FreePlay error handling; deferred to handle together.
  - #109: Duplicate of issue #140 (unused useEffect in BaselineTransition.jsx) — #140 is selected.
  - #108: Settings.jsx load error state — medium complexity UI change; failed-implementation label; deferred.
  - #107: LifestyleLog.jsx loadTodayData error handling — medium complexity; failed-implementation label; deferred.
  - #105: GAME_TYPE_LABELS dead code removal — failed-implementation label; has known test suite issues; deferred.
  - #103: Export isRoundCorrect from BaselineGameWrapper.jsx — failed-implementation label; has known test failures (VisualCategorisation unrelated); deferred.
  - #100: account.py double URL segment fix — duplicate of issue #117; same file, same fix; deferred with #117.
  - #99: sessions.py baseline_number always set to 1 — failed-implementation label; medium complexity backend change; deferred.
  - #98: DomainScoreCard.jsx getDifficultyColor hardcoded hex — overlaps with issue #135; deferred.
  - #97: BrainHealthGauge.jsx hardcoded hex colors — overlaps with issue #135; deferred.
  - #95: useStreakData.js localStorage vs sessionStorage fix — failed-implementation label; overlaps with issues #130 and #131; deferred to handle all auth hook fixes together.
  - #94: useGameHistory.js localStorage vs sessionStorage fix — failed-implementation label; overlaps with issues #130 and #131; deferred.
  - #93: log_exercise_result refactor in sessions.py — failed-implementation label; medium complexity; deferred.
  - #92: Duplicate card_memory accuracy block in sessions.py — failed-implementation label; deferred.
  - #91: brain_health_score.py datetime.utcnow and wrong filter field — medium complexity; overlaps with issue #90 (lifestyle filter fix is selected); deferred to follow-up run.
  - #89: adaptive_baseline.py datetime.utcnow fix — failed-implementation label; similar to #88 which is selected; deferred to avoid conflicting changes.
  - #75: CardMemoryGame mobile scroll bug — failed-implementation label; medium complexity responsive layout change; deferred.
  - #69: Dashboard domain sessions count showing 0 — failed-implementation label; medium complexity requiring investigation of multiple files; deferred.
  - #68: Progress page 401 error on game history — failed-implementation label; overlaps with useGameHistory.js auth fixes; deferred to handle with auth hook fixes.
  - #67: CardMemory reveal correct card on wrong guess — failed-implementation label; medium complexity mechanic change; deferred.
  - #66: DigitSpan staircase change — failed-implementation label; medium complexity mechanic change touching multiple files; deferred.
  - #53: Guided breathing dashboard launch — failed-implementation label; medium-high complexity feature touching multiple files; design decisions provided but implementation is substantial.
  - #49: Level up/down message on session results — failed-implementation label; medium-high complexity touching frontend and backend; deferred.
  - #48: Card memory images change to letters/numbers — failed-implementation label; medium complexity UI change; deferred.
  - #47: Visual categorisation three rounds restructure — failed-implementation label; high complexity mechanic change; deferred.
  - #44: Adaptive difficulty not progressing — failed-implementation label; medium-high complexity bug in backend services; design decision provided but implementation is risky; deferred.
**Spec version:** v1.1
**Test result:** PASSED (iteration 1): [33mBoth esbuild and oxc options were set. oxc options will be used and esbuild options will be ignored.[39m The following esbuild options were set: `{ jsx: 'automatic', jsxImportSource: undefined }`
**PR:** (none)
**Errors:** (none)

## Run — 2026-04-29 (automated) [pipeline v3 — implementation]
**Status:** completed
**Issues implemented:**
  - #109: Remove unused useEffect import from BaselineTransition.jsx
  - #141: Remove unused Badge import from SkillProfileScreen.jsx
  - #117: Fix doubled /account/account path in account.py router
  - #112: Remove misleading `if response:` guard in delete_account handler
  - #139: Improve error message extraction in LifestyleLog.jsx handleSubmit
  - #89: Replace datetime.utcnow() with datetime.now(timezone.utc) in adaptive_baseline.py
**Issues failed:**
  (none)
**Issues deferred:**
  - #195: Technical debt requiring human judgment on whether to implement multi-file support or simplify to single path — not purely mechanical.
  - #190: Rename of `raw` variable across 5+ files (synthesizer.py, audit_classifier.py, prioritiser.py, design_reviewer.py, pipeline_reviewer.py) — medium complexity touching multiple feedback_agent files; deferred to avoid scope creep in this run.
  - #189: Duplicate constant refactor — depends on issue #188 (shared constants file creation); deferred as a dependency of #188.
  - #188: Creating a shared constants file for BASELINE_LEVEL_TO_DIFFICULTY across Session.jsx, FreePlay.jsx, and BaselineGameWrapper.jsx is medium complexity touching 3+ files; deferred to keep this run focused on low-risk fixes.
  - #187: Introducing named constants for magic numbers in brain_health_score.py is medium complexity; deferred for a focused run.
  - #186: Introducing named constants for magic numbers in adaptive_difficulty.py is medium complexity; deferred for a focused run.
  - #184: Requires investigating whether calculateBrainHealthScore in scoring.js is truly dead code or used somewhere — medium risk given scoring.test.js failures observed in prior runs.
  - #183: Magic number fix in Stroop.jsx — low complexity but deferred as run is already at capacity.
  - #182: Magic number fix in SymbolMatching.jsx — low complexity but deferred as run is already at capacity.
  - #178: BottomNav inline style extraction — low complexity but deferred; run is at capacity.
  - #177: BaselinePrompt.jsx gradient token inconsistency — low complexity but deferred; run is at capacity.
  - #176: Stroop.jsx colorMap hardcoded hex values — deferred; design token names need verification and run is at capacity.
  - #175: VisualCategorisation.jsx COLORS array hardcoded hex — deferred; design token names need verification.
  - #174: CardMemoryGame.jsx colors array hardcoded hex — deferred; design token names need verification.
  - #173: GoNoGo.jsx hardcoded hex colors — deferred; design token names need verification.
  - #172: DomainScoreCard.jsx hardcoded hex colors — covered by issue #135 which has a more detailed design decision; deferred.
  - #171: BrainHealthGauge.jsx hardcoded hex colors — covered by issue #135 which has a detailed design decision; deferred.
  - #168: useGameHistory.js naming and localStorage inconsistency — medium complexity; superseded by the more complete fix in #130/#94 which cover the axios client migration.
  - #167: Dead/no-op logic in SessionPlannerService — medium complexity requiring careful logic analysis to determine which branch is correct; deferred.
  - #166: review_pipeline.py 400+ line refactor — high complexity touching pipeline orchestration; deferred.
  - #165: implementation_pipeline.py 500+ line refactor — high complexity touching pipeline orchestration; deferred.
  - #164: NBack.jsx complexity refactor — high complexity with useRef/useEffect chains; deferred.
  - #163: VisualCategorisation.jsx component split — high complexity; deferred.
  - #162: GoNoGo.jsx component split — high complexity; deferred.
  - #154: datetime.utcnow in skill_assessment.py — part of the broader #119 sweep; addressed separately to avoid overlapping with #89 in this run.
  - #152: Onboarding.jsx missing error state on handleComplete — medium complexity requiring UI error state design; deferred.
  - #146: Pipeline version upgrade is an administrative/CLI action, not a code change; cannot be implemented by the build agent.
  - #145: CardMemoryGame.jsx large refactor — medium/high complexity; deferred.
  - #144: adaptive_baseline.py GAME_DOMAIN_MAP extraction — medium complexity; deferred.
  - #143: sessions.py log_exercise_result refactor — medium/high complexity; depends on #128/#92/#93 and touches core session logic.
  - #142: baseline_number auto-increment in sessions.py — medium complexity touching authentication/session core; deferred.
  - #138: FreePlay.jsx error handling for session start failure — medium complexity with specific UI requirements from design decision; deferred.
  - #137: feedback.py unauthenticated submission — medium complexity touching authentication; deferred.
  - #136: GAME_TYPE_LABELS consolidation to shared constants file — medium complexity; failed-implementation label present, deferred.
  - #135: getDifficultyColor/getGaugeColor consolidation — medium complexity touching multiple chart components; failed-implementation label, scoring.test.js failures are a pre-existing blocker.
  - #131: useStreakData.js axios client migration — medium complexity; same root cause as #130/#95/#94; should be done in a single coordinated fix rather than piecemeal.
  - #130: useGameHistory.js localStorage→sessionStorage + axios migration — medium complexity; repeated failures suggest a test infrastructure issue that needs resolving first.
  - #129: calculateBrainHealthScore dead code in scoring.js — failed-implementation label present; scoring.test.js failures indicate tests actively test this function, so removing it without fixing the test first would break CI.
  - #128: card_memory accuracy calculation deduplication in sessions.py — medium complexity; closely related to #143/#92/#93; deferred to handle together.
  - #120: StreakTracker.jsx formatMonthDay rename — low complexity but deferred; run is at capacity.
  - #119: datetime.utcnow sweep across multiple model files — medium complexity touching 6+ files; failed-implementation label present; deferred in favour of the single-file fix in #89.
  - #118: BottomNav.jsx inline styles to CSS class — low complexity but has a pre-existing VisualCategorisation test failure that blocks it; deferred.
  - #111: FreePlay.jsx silent catch blocks — failed-implementation label present; overlaps with #138 which has a more complete design decision; deferred.
  - #108: Settings.jsx error state on load failure — medium complexity with detailed design spec; failed-implementation label; deferred.
  - #107: LifestyleLog.jsx loadTodayData silent error — medium complexity with detailed design spec; failed-implementation label; deferred.
  - #105: GAME_TYPE_LABELS dead code removal from TrendChart.jsx and Progress.jsx — failed-implementation label; repeated test infrastructure failures (jest not defined) blocking it; deferred until test infra is fixed.
  - #103: Export isRoundCorrect from BaselineGameWrapper.jsx — failed-implementation label; prior attempts showed VisualCategorisation test failures as a blocker; deferred.
  - #100: Same fix as #117 (doubled account path) — duplicate issue; resolved by selecting #117.
  - #99: start_session baseline_number handling — failed-implementation label; touches core session/auth boundary; deferred.
  - #98: DomainScoreCard.jsx getDifficultyColor hardcoded hex — medium complexity; covered by issue #135's design decision; deferred.
  - #97: BrainHealthGauge.jsx getGaugeColor hardcoded hex — medium complexity; covered by issue #135's design decision; deferred.
  - #95: useStreakData.js axios client migration — failed-implementation label; test infrastructure issues blocking; deferred.
  - #94: useGameHistory.js localStorage→axios migration — failed-implementation label; test infrastructure issues blocking; deferred.
  - #93: log_exercise_result 40-line violation — failed-implementation label; high complexity touching core session logic; deferred.
  - #92: card_memory accuracy duplication — failed-implementation label; closely related to #93/#128; deferred to handle together.
  - #91: brain_health_score.py datetime.utcnow + logged_date filter — failed-implementation label; medium complexity; deferred.
  - #75: CardMemoryGame mobile scroll overflow — failed-implementation label; pytest infrastructure issues were blocking previous runs; medium complexity UI/CSS fix.
  - #69: Dashboard domain sessions count showing 0 — failed-implementation label; requires investigating field mapping across Dashboard.jsx, client.js, and progress.py; deferred.
  - #68: Progress page 401 on game history — failed-implementation label; root cause is the useGameHistory localStorage issue (#94/#130); fix those first.
  - #67: CardMemory reveal correct card on wrong guess — failed-implementation label; mechanic change touching core game logic; deferred.
  - #66: DigitSpan staircase mechanic change — failed-implementation label; high complexity touching game logic and adaptive difficulty; deferred.
  - #53: Guided breathing dashboard quick-launch — failed-implementation label; feature with product owner decisions recorded but implementation involves multiple files and a new feature path; deferred.
  - #49: Level up/down message on session results — failed-implementation label; touches adaptive_difficulty.py and SessionSummary.jsx with inter-service coordination; deferred.
  - #48: Card memory images (letters/numbers) — failed-implementation label; requires asset/icon library changes and significant CardMemoryGame rework; deferred.
  - #47: Visual Categorisation 3-round mechanic — failed-implementation label; significant mechanic change with 300+ line component; deferred.
  - #44: Adaptive difficulty stuck — failed-implementation label; high complexity touching adaptive_difficulty.py and session_planner.py core logic; deferred.
**Spec version:** v1.2
**Test result:** PASSED (iteration 1):     at [90mfile:///home/runner/work/brain-training/brain-training/frontend/[39mnode_modules/[4m@vitest/runner[24m/dist/chunk-artifact.js:2955:64
**PR:** (none)
**Errors:** (none)
