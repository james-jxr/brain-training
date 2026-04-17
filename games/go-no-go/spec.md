# Feature Specification: Go / No-Go Task

**Spec Version:** spec-v0.1
**Date:** 2026-04-04
**Status:** Approved
**Brief Reference:** Replace Reaction Testing game with Go/No-Go task (processing speed + inhibitory control)
**Parent App Spec:** brain-training/spec.md spec-v0.6

---

> **Design Agent — Thinking Record**
>
> *Problem:* The existing `GoNoGo.jsx` (used as the Attention & Inhibitory Control exercise) is a minimal implementation:
> it uses only red/green circles, exposes the No-Go stimulus by displaying "DO NOT PRESS" text (removing
> the inhibition challenge), uses an approximate timing formula (`1500ms - difficulty*100`) not aligned with
> validated Go/No-Go paradigm timings, scores only accuracy without false-alarm penalty, and has no result
> breakdown. It is referred to as the "Reaction Test" in the original brief context.
>
> *Goal:* Replace it with a properly designed Go/No-Go task that measures both processing speed and
> inhibitory control, matching the well-validated clinical paradigm: rapid stimulus presentation, player
> must press for Go and actively withhold for No-Go, scored by signal detection logic.
>
> *Minimum feature set:* 20 stimuli per round, coloured shapes (circle/square/triangle), single Go target,
> one–three No-Go types by difficulty level, fixed display durations, ISI blank, four-outcome scoring
> (hits + correct rejections − false alarms − misses), result breakdown screen, instruction screen with
> Go stimulus highlighted.
>
> *Retirement strategy:* Rename existing `GoNoGo.jsx` → `GoNoGoLegacy.jsx` with a comment explaining it
> was superseded. Do not delete — it preserves the original session data format and serves as a reference.
> All wiring in `Session.jsx` and `BaselineTest.jsx` already points to `GoNoGo`, so only the component
> file itself changes; no route or session-recording changes are needed.
>
> *Genuine ambiguities:* (1) Shape rendering: SVG inline or CSS shapes? → SVG inline for precision and
> mobile tap targets. (2) How to track "first play only" hint: localStorage or prop? → Local component
> state (one `hasEverResponded` flag), since the component is re-mounted per round in baseline and per
> session in the session flow — "first play" therefore means the first stimulus of the current component
> instance. (3) False alarm feedback: silent or visible? → Brief colour flash (red border on the tap zone)
> to signal the error without adding a distracting full-screen overlay.

---

## 1. Purpose & Problem Statement

The Go/No-Go Task is the Attention & Inhibitory Control exercise in the Brain Training App. It replaces
a minimal prior implementation with a properly designed rapid-response paradigm: the player taps for a
single target shape/colour (Go) and withholds all responses for distractor shapes (No-Go). It measures
both processing speed (how quickly the player responds to Go stimuli) and inhibitory control (how
successfully the player suppresses responses to No-Go stimuli), which are the two components the
Attention & Inhibitory Control domain was defined to train.

---

## 2. Integration Context

This is a feature replacement within the existing brain training app — not a standalone app. The
component must:

- Accept props `{ difficulty: number (1–10), onComplete: (payload) => void }`
- Call `onComplete` with a payload shape-compatible with the existing session recording API:
  `{ trials_presented, trials_correct, avg_response_ms, accuracy, hits, misses, false_alarms, correct_rejections }`
- Work inside both `Session.jsx` (regular training) and `BaselineGameWrapper.jsx` (baseline assessment),
  both of which pass `difficulty` and `onComplete` and expect the payload above

No backend changes are required. The existing `POST /api/sessions/{id}/exercise-result` route with
`exercise_type: "go_no_go"` handles persistence. The `BaselineGameWrapper` already reads `payload.accuracy`
to determine correctness for the adaptive algorithm.

---

## 3. User Stories

- As a player, I want to see clear instructions showing the target stimulus before each round, so I know
  exactly what to tap for.
- As a player, I want each stimulus to appear and disappear quickly, so the game genuinely challenges my
  reaction speed rather than being trivially easy.
- As a player starting my first round, I want a subtle tap hint on the first stimulus, so I understand
  the interaction mechanic without needing to re-read instructions.
- As a player completing a round, I want to see my accuracy percentage and a breakdown of hits, misses,
  and false alarms, so I understand what I did well and what to improve.
- As a player, I want the difficulty to feel meaningfully different between Easy, Medium, and Hard, so
  I notice progress as I improve.

---

## 4. MVP Feature List (In Scope)

1. **Stimulus set** — Go stimulus is always a green circle. No-Go stimuli are drawn from: red circle
   (Easy), plus blue square (Medium), plus orange triangle (Hard). All shapes rendered as SVG, 160px,
   centred in a 280×280px tap zone.

2. **Difficulty levels** — mapped from the numeric difficulty prop (1–10):
   - Easy (difficulty 1–3): display window 1000ms, 1 No-Go type (red circle), Go ratio 75%
   - Medium (difficulty 4–6): display window 700ms, 2 No-Go types, Go ratio 70%
   - Hard (difficulty 7–10): display window 450ms, 3 No-Go types, Go ratio 65%

3. **Round structure** — 20 stimuli per round. Stimuli generated by shuffling a sequence of
   `round(20 × goRatio)` Go items and `20 − numGo` No-Go items, with No-Go types distributed evenly
   across the available No-Go variants for the current difficulty.

4. **Inter-stimulus interval (ISI)** — 400ms blank screen between stimuli. The tap zone shows a subtle
   neutral dot during ISI to prevent confusion.

5. **Response handling** — the entire tap zone (280×280px minimum, filling available width on mobile)
   is clickable/tappable during a stimulus. Tapping during the display window records the response;
   tapping during ISI is ignored.

6. **Four-outcome scoring**:
   - **Hit**: player taps during a Go stimulus window → counted correct
   - **Miss**: Go stimulus window expires without a tap → counted incorrect
   - **False alarm**: player taps during a No-Go stimulus window → counted incorrect
   - **Correct rejection**: No-Go stimulus window expires without a tap → counted correct
   - `trials_correct = hits + correct_rejections`
   - `trials_presented = 20`
   - `raw_score = hits + correct_rejections − false_alarms − misses`
   - `accuracy = max(0, raw_score) / 20` (range 0.0–1.0)
   - `avg_response_ms = mean of response times for hits only` (0 if no hits)

7. **Instruction screen** — shown before the round begins. Displays the Go stimulus prominently with
   the label "Tap for this →" and the No-Go stimuli with "Ignore these". Shows difficulty level and
   round duration. "I'm ready" button starts the sequence.

8. **First-play tap hint** — on the very first Go stimulus of a component instance, a subtle "tap! →"
   label appears below the shape until the player responds or the window closes. Hidden on all
   subsequent stimuli.

9. **Result screen** — shown after all 20 stimuli. Displays: accuracy % (large), average RT in ms
   (hits only), and a four-row breakdown table (Hits / Misses / False Alarms / Correct Rejections)
   with counts and a colour indicator (green = good, amber = neutral, red = bad). A "Done" button
   calls `onComplete`.

10. **Retirement of GoNoGoLegacy** — the original `GoNoGo.jsx` is renamed to `GoNoGoLegacy.jsx` and
    given a file-top comment: "RETIRED — superseded by the full Go/No-Go implementation (2026-04-04).
    Kept for reference. Do not use in new features."

---

## 5. Out of Scope

- Audio feedback (sounds on hit/miss) — deferred; no audio system in v1
- Animated shape entrance/exit transitions — kept minimal to avoid timing interference
- Adaptive ISI duration — fixed at 400ms for predictability
- Session-level "first play ever" tracking across component instances — hint shows on first stimulus of
  each new component mount (good enough for the UX goal)
- Detailed response-time histogram — aggregate average only in v1
- Keyboard support — primary interaction is mouse click / touch tap; keyboard support is a v2 concern

---

## 6. Data Model

No new backend entities are required. Results are stored in the existing `ExerciseAttempt` model using
`exercise_type = "go_no_go"`. The following fields map to the new payload:

| ExerciseAttempt field | Maps to Go/No-Go payload field          |
|----------------------|-----------------------------------------|
| `trials_presented`   | 20 (constant per round)                 |
| `trials_correct`     | `hits + correct_rejections`             |
| `avg_response_ms`    | Mean RT for hit responses (0 if no hits)|
| `score`              | Not used for this exercise type         |
| `difficulty`         | Not used (stored via DomainProgress)    |

Additional payload fields (`accuracy`, `hits`, `misses`, `false_alarms`, `correct_rejections`) are
returned to `Session.jsx` and `BaselineGameWrapper` but are not persisted to the backend — they are
used for frontend logic (adaptive difficulty correctness check) and display only.

---

## 7. API / Route Map

No new backend routes. All existing routes already support this exercise type:

| Method | Path                                       | Used for                        | Auth |
|--------|--------------------------------------------|---------------------------------|------|
| POST   | /api/sessions/{id}/exercise-result         | Record round result              | Y    |
| GET    | /api/sessions/{id}/next                    | Determine which exercise is next | Y    |
| GET    | /api/adaptive-baseline/status              | Load skill profile for difficulty| Y    |

---

## 8. Technology Stack

Inherits the parent app stack. No deviations.

| Layer       | Choice            | Reason                                   |
|-------------|-------------------|------------------------------------------|
| Frontend    | React 18 / Vite   | Matches existing app                     |
| Shapes      | Inline SVG        | Precise sizing, no asset loading, mobile-friendly |
| Timers      | setTimeout / useRef | Standard browser API; refs prevent stale closure issues |
| Testing     | pytest (backend)  | Ports component logic to Python for unit testing alongside existing suite |

---

## 9. File & Folder Structure

Files created or modified by this feature:

```
apps/brain-training/
├── frontend/src/components/exercises/
│   ├── GoNoGoLegacy.jsx          ← renamed from GoNoGo.jsx (archived, add retirement comment)
│   └── GoNoGo.jsx                ← NEW full implementation (replaces the above)
├── backend/tests/
│   └── test_go_no_go.py          ← NEW unit + smoke tests
└── games/go-no-go/
    ├── spec.md                   ← THIS FILE
    └── test-report.md            ← Test Agent output
```

Files that do NOT need modification (already correctly wired):
- `frontend/src/pages/Session.jsx` — imports `GoNoGo`, maps to `go_no_go` type under `attention` domain
- `frontend/src/components/baseline/BaselineTest.jsx` — includes `GoNoGo` in `BASELINE_GAMES` array
- `frontend/src/components/baseline/BaselineGameWrapper.jsx` — reads `payload.accuracy` for correctness

---

## 10. Non-Functional Requirements

- **Performance:** Stimulus display timer must be accurate to within ±50ms of the specified display
  window. A `performance.now()`-based timing reference is used for response time measurement.
- **Mobile usability:** Tap zone must be a minimum of 280×280px. Font sizes for instructions must be
  ≥16px. No hover-only affordances.
- **Colour accessibility:** Go (green `#3D9E72`) and No-Go (red `#D95F5F`, blue `#4A90C4`,
  orange `#C9973A`) are drawn from the existing design system palette. Shape (not just colour)
  distinguishes Go from No-Go to avoid colour-blind exclusion; green circle vs. differently-shaped
  or differently-coloured variants.
- **Browser support:** Chrome and Safari latest (same as parent app).
- **Error handling:** The component must not crash if `onComplete` is called with an unexpected payload
  shape. All stats default to 0 if no responses are recorded.

---

## 11. Open Questions

| ID | Question | Assumption made |
|----|----------|-----------------|
| Q1 | Should the false alarm produce immediate visual feedback, or silent scoring? | Silent for now — brief red flash on tap zone introduced as Low-priority UX improvement in test report |
| Q2 | Should the result screen show a "Try again" option? | No — `onComplete` is always called after results, consistent with other game components. Parent component controls flow. |
| Q3 | The spec says "one specific shape+colour combo" for Go — should it ever vary across rounds? | No. Green circle is always the Go stimulus. Spec simplicity > novelty for v1. |
