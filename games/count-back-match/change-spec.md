# Change Spec: Count Back Match (N-Back Game)

**Spec Version:** change-spec-v0.1
**Date:** 2026-04-04
**Status:** Approved for build
**Source file:** `frontend/src/components/exercises/NBack.jsx`

---

## 1. Current State Summary

The existing NBack.jsx implements an N-back task where:
- The letter sequence is generated randomly with no match balance guarantee
- Letters advance automatically on a 1500ms interval via `useEffect`
- No lead-in phase — buttons are rendered from letter 1 (disabled when `!displayedLetter`)
- N is derived from `difficulty` (1–10 numeric): `difficulty <= 3 → 1-back`, `≤6 → 2-back`, else `3-back`
- The `onComplete` callback emits `{ trials_presented, trials_correct, avg_response_ms }`, where `avg_response_ms` encodes response speed and is implicitly used as a speed signal
- Progress bar is hardcoded to max 8 (inconsistent with sequence length)

---

## 2. Changes Required

### Change 1 — Self-Paced Letter Advancement

**Current behaviour:** After the lead-in phase (new, see Change 2), letters advance on player action.

**Target behaviour:**
- Remove the `useEffect` timer that auto-advances `currentIndex` during the active (post-lead-in) phase
- Button presses (`handleMatch` / `handleNoMatch`) both record the answer AND call `advanceLetter()` which increments `currentIndex` and sets `displayedLetter`
- The active phase is therefore blocked waiting for a button press after each letter

**State changes:**
- Remove timer-based `currentIndex` advancement from `useEffect`
- New `advanceLetter()` function: sets `displayedLetter = sequence[currentIndex]`, increments `currentIndex`, records `trialStartTime`
- Buttons trigger: record response → advance to next letter → if no more letters, call `finishGame()`

---

### Change 2 — Automatic Lead-In Phase

**Definition:** The first `n` letters of each round are the "lead-in" — there is no valid N-back target to compare them to, so buttons must be unavailable.

**Target behaviour:**
- New state variable: `phase` — either `'leadin'` or `'active'`
- When `startSequence()` is called: set `phase = 'leadin'`, start auto-advancing from index 0
- During lead-in: display letters automatically at 1.5s intervals. Show a clearly labelled indicator (e.g. `"Memorising..."`) in place of the Match/No Match buttons
- After the Nth letter (index `n - 1`) has been displayed for 1.5s, set `phase = 'active'` and display letter at index `n` (the first letter the player must judge)
- During active phase: no timer — wait for button press

**UX details:**
- Lead-in letters display normally in the large letter area
- Buttons replaced by: `<p style={{ textAlign: 'center', color: 'var(--color-text-secondary)' }}>Memorising…</p>`
- Active phase: buttons appear/unhide; instruction text changes to match/no-match prompt

---

### Change 3 — Difficulty = N-Back Level

**Current mapping:** `difficulty` (1–10 int) → `n = difficulty <= 3 ? 1 : difficulty <= 6 ? 2 : 3`

**Target mapping:** The `difficulty` prop passed from `Session.jsx` is a 1–10 integer derived from the adaptive difficulty system. Map it to N-back level as follows:

| Difficulty value | N-back level |
|---|---|
| 1–3 (easy band) | 1-back |
| 4–6 (medium band) | 2-back |
| 7–10 (hard band) | 3-back |

**Note:** This mapping is unchanged from the current implementation. The change brief specifies Easy/Medium/Hard → 1/2/3-back. The current mapping achieves this correctly. **No code change required for the mapping itself.** However, the instruction text shown to the player should reflect this clearly: `"This is a {n}-back task. Press Match when the current letter matches the letter shown {n} step(s) ago."`

---

### Change 4 — Balanced Match Ratio

**Current behaviour:** `generateSequence()` creates a purely random sequence — no guarantee of match ratio. In practice, a 15-letter sequence from 15 letters gives ~1/15 chance of any spontaneous match, which is far too low.

**Target behaviour:** Sequence generation guarantees 40–60% of judgeable trials are matches.

**Algorithm:**

```
function generateBalancedSequence(n, totalLength):
  judgeableCount = totalLength - n          # letters the player actually judges
  targetMatches = round(judgeableCount * 0.5)  # aim for 50% with ±10% acceptable

  letters = ['A'..'O']  # 15 letters
  sequence = []

  # Generate lead-in letters freely (they are never judged)
  for i in 0..n-1:
    sequence.push(randomLetter(letters))

  # Build judgeable portion
  matchesRemaining = targetMatches
  noMatchesRemaining = judgeableCount - targetMatches

  for i in n..totalLength-1:
    # Decide: should this position be a match?
    matchProbability = matchesRemaining / (matchesRemaining + noMatchesRemaining)
    shouldMatch = (random() < matchProbability)

    if shouldMatch:
      sequence.push(sequence[i - n])   # copy the letter from N positions ago
      matchesRemaining -= 1
    else:
      # Pick a letter that is NOT the same as sequence[i - n]
      candidate = randomLetter(letters excluding sequence[i - n])
      sequence.push(candidate)
      noMatchesRemaining -= 1

  return sequence
```

**Key constraint:** When generating a no-match letter, the candidate must not equal `sequence[i - n]` (to avoid accidental matches). Since we have 15 letters (A–O), there are always at least 14 non-matching options available.

**Sequence length:** Keep total length at `15 + n` (current value). Judgeable count = `15`.

---

### Change 5 — Accuracy-Only Scoring

**Current behaviour:** The `onComplete` payload includes `avg_response_ms`, which the adaptive difficulty system uses as a speed signal. Session.jsx sends this to the backend as `trials_presented / trials_correct / avg_response_ms`.

**Target behaviour:**
- Remove `responseTimes` state and `trialStartTime` state
- Remove response time recording from `handleMatch` and `handleNoMatch`
- The `onComplete` payload changes to: `{ trials_presented, trials_correct, avg_response_ms: 0 }`
  - Sending `avg_response_ms: 0` maintains compatibility with the existing backend schema (`ExerciseAttempt.avg_response_ms`) without requiring backend changes
  - `trials_presented` = count of judgeable trials (letters where the player was asked Match/No Match)
  - `trials_correct` = count of correct responses

**Session.jsx compatibility:** No changes needed — it already handles the `trials_presented / trials_correct / avg_response_ms` payload for non-card_memory exercises.

---

## 3. Updated Component State

| State variable | Type | Purpose | Change |
|---|---|---|---|
| `n` | int | N-back level (1/2/3) | Unchanged |
| `sequence` | string[] | Full letter sequence | Updated by new generator |
| `phase` | `'idle'│'leadin'│'active'│'done'` | Game phase | **New** |
| `currentIndex` | int | Next letter to show | Unchanged |
| `displayedLetter` | string | Letter shown in large display | Unchanged |
| `trials` | int | Judgeable trial count | Unchanged |
| `correct` | int | Correct answer count | Unchanged |
| `feedback` | `'correct'│'incorrect'│null` | Per-trial feedback | Unchanged |
| ~~`responseTimes`~~ | ~~number[]~~ | ~~Speed tracking~~ | **Removed** |
| ~~`trialStartTime`~~ | ~~number~~ | ~~Per-trial timer~~ | **Removed** |
| ~~`started`~~ | ~~bool~~ | ~~Game started flag~~ | **Replaced by `phase`** |

---

## 4. Updated Game Flow

```
[Idle screen] → player presses Start
  → phase = 'leadin'
  → display letter 0 (lead-in 1 of N)
  → 1.5s timer → display letter 1 ... → display letter N-1 (last lead-in)
  → 1.5s timer → phase = 'active'
  → display letter N (first judgeable)
  → [wait for button press]
    → record correct/incorrect
    → show feedback (300ms)
    → advance to letter N+1
    → [wait for button press]
    → ...repeat until sequence exhausted...
  → call onComplete({ trials_presented, trials_correct, avg_response_ms: 0 })
```

---

## 5. UI Specification

| Phase | Letter display | Buttons | Status label |
|---|---|---|---|
| Idle | — | Start button | — |
| Lead-in | Current lead-in letter (large) | Hidden | "Memorising… (N of N)" |
| Active | Current judgeable letter (large) | Match / No Match (enabled) | "{n}-Back: press Match if this = letter {n} step(s) ago" |
| Feedback (300ms) | Letter remains | Buttons disabled | "Correct!" or "Incorrect" |
| Done | — | — | (onComplete fires, Session.jsx takes over) |

---

## 6. Files to Change

| File | Change |
|---|---|
| `frontend/src/components/exercises/NBack.jsx` | Full rewrite of component logic and render |
| `frontend/src/components/exercises/NBack.test.js` (new) | Unit tests for sequence generation and game logic |
| `apps/brain-training/games/count-back-match/test-report.md` (new) | Test report for this change set |

**No backend changes required.** The `onComplete` payload shape is unchanged (same field names, `avg_response_ms` set to 0). Session.jsx is unchanged.

---

## 7. Open Questions

| ID | Question | Resolution |
|---|---|---|
| Q1 | Should incorrect responses carry a point penalty? | No — the brief says "correct = points, incorrect = no points". No penalty implemented. The component scores via `trials_correct / trials_presented`. |
| Q2 | Should feedback be shown after button press? | Yes — brief implies this. Show "Correct!" / "Incorrect" for 300ms then advance. |
| Q3 | Should the progress bar reflect judged trials or total sequence position? | Judged trials (0 to `judgeableCount`). More meaningful to the player. |
