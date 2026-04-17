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
**Status:** tests_failed
**Feedback processed:** 3
**Changes applied:**
  - stroop-scoring-accuracy-bug: Fix Stroop exercise scoring reporting incorrect results despite perfect performance
  - card-memory-score-count-bug: Fix CardMemory session score showing incorrect round count and correct count
  - baseline-card-colours-shapes: Improve card colour contrast and increase shape size in baseline card memory game
  - onboarding-intro-copy: Rewrite onboarding intro copy to mention academic basis, benefits, and regular practice
**Skipped implementations (GitHub issues created):**
  (none)
**Issues created:**
  - https://github.com/james-jxr/app-dev-capability/issues/20
**Spec version:** unchanged
**Test result:** FAILED after 3 iteration(s)
**PR:** (none)
**Errors:** ".
 ❯ src/test/Stroop.test.jsx:244:3
    242|   });
    243|
    244|   it('tracks trials_correct count accurately in onComplete result', as…
       |   ^
    245|     const onComplete = vi.fn();
    246|     render(<Stroop difficulty={5} onComplete={onComplete} />);

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[20/23]⎯

 FAIL  src/test/Stroop.test.jsx > Stroop component > avg_response_ms is a non-negative number
Error: Test timed out in 5000ms.
If this is a long-running test, pass a timeout value as the last argument or configure it globally with "testTimeout".
 ❯ src/test/Stroop.test.jsx:272:3
    270|   });
    271|
    272|   it('avg_response_ms is a non-negative number', async () => {
       |   ^
    273|     const onComplete = vi.fn();
    274|     render(<Stroop difficulty={5} onComplete={onComplete} />);

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[21/23]⎯

 FAIL  src/test/Stroop.test.jsx > Stroop component > number of option buttons depends on difficulty
Error: Test timed out in 5000ms.
If this is a long-running test, pass a timeout value as the last argument or configure it globally with "testTimeout".
 ❯ src/test/Stroop.test.jsx:298:3
    296|   });
    297|
    298|   it('number of option buttons depends on difficulty', async () => {
       |   ^
    299|     // difficulty=1: numOptions = min(4, 2 + floor(1/3)) = min(4,2) = 2
    300|     const { unmount } = render(<Stroop difficulty={1} onComplete={vi.f…

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[22/23]⎯

 FAIL  src/test/Stroop.test.jsx > Stroop component > with difficulty=9 shows 4 color options
Error: Test timed out in 5000ms.
If this is a long-running test, pass a timeout value as the last argument or configure it globally with "testTimeout".
 ❯ src/test/Stroop.test.jsx:314:3
    312|   });
    313|
    314|   it('with difficulty=9 shows 4 color options', async () => {
       |   ^
    315|     // difficulty=9: numOptions = min(4, 2 + floor(9/3)) = min(4,5) = 4
    316|     render(<Stroop difficulty={9} onComplete={vi.fn()} />);

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[23/23]⎯
