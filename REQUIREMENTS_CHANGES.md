# Requirements Changes Log — Brain Training App

This log records every change made to the spec after its initial draft. Every entry must be completed before the spec version is updated.

**Rule:** Never update `spec.md` without adding an entry here first.

---

## How to Add an Entry

Copy the template below and fill it in. Classify the change type:

- **Discovery** — testing or building revealed the requirement was wrong or underspecified
- **Scope** — deliberate decision to add, remove, or defer a feature
- **Technical constraint** — the build couldn't implement the requirement as written
- **Clarification** — the requirement was ambiguous; this entry makes it precise without changing intent

---

## Change Template

```
### CHG-XXX — [Short title]
**Date:** YYYY-MM-DD
**Spec version before:** spec-vX.X
**Spec version after:** spec-vX.X
**Change type:** Discovery | Scope | Technical constraint | Clarification
**Triggered by:** [e.g. Q&A with James | Build Agent feedback | Test Agent finding BUG-XX | User testing session]

**What changed:**
[Describe what was changed in the spec — be specific about which section(s)]

**Why:**
[The reason for the change]

**Downstream impact:**
- Build Agent: [does this require a rebuild, a patch, or no code change?]
- Test Agent: [does this affect the test report criteria?]
- Prompt templates: [does this reveal a flaw in the Design Agent prompt that should be fixed?]
```

---

## Change Log

---

### CHG-001 — Open questions resolved; baseline made repeatable every 6 months
**Date:** 2026-04-03
**Spec version before:** spec-v0.1
**Spec version after:** spec-v0.2
**Change type:** Clarification
**Triggered by:** Q&A with James

**What changed:**
- §4 Feature #2: Baseline assessment changed from one-time to repeatable every 6 months. Original baseline always retained for long-term comparison; most recent baseline used for current-period progress and difficulty calibration.
- §6 Data model: `BaselineResult` entity gained `baseline_number` and `is_original` fields. `User` entity gained `next_baseline_eligible_date` field.
- §7 Routes: Added `GET /api/baseline/history`. Updated `GET /api/baseline/status` description.
- §11 Open Questions: All 6 questions resolved and closed. Table updated with resolutions.
- Spec status changed from Draft to Approved.

**Why:**
Six-monthly re-baselines serve as milestone check-ins and allow users to reset their improvement goals as they progress. Retaining the original baseline preserves the long-term progress record.

**Downstream impact:**
- Build Agent: Data model change is significant — ensure `baseline_number` auto-increment logic and `is_original` flag are correctly implemented. Dashboard needs to display both original and current-period comparisons.
- Test Agent: Add test case for re-baseline eligibility gate (should be blocked if < 6 months since last baseline). Add test that original baseline is never overwritten.
- Prompt templates: No change needed.

---

### CHG-002 — Platform confirmed as web-first (not native mobile)
**Date:** 2026-04-03
**Spec version before:** spec-v0.2
**Spec version after:** spec-v0.3
**Change type:** Scope
**Triggered by:** James — confirmed web app for initial user testing

**What changed:**
- §1 Purpose: Clarified platform as web application for v1, with native mobile as a future path.
- §2 Target User: Technical assumption updated — users access via desktop or mobile browser; no app installation required.
- §5 Out of Scope: Native iOS and Android apps explicitly listed as out of scope for v1.
- §8 Technology Stack: Stack confirmed as web-first (React + FastAPI). PWA capability noted as a v1.1 option.

**Why:**
Web-first is faster to build, easier to test with real users, and avoids app store submission overhead for initial validation. The design system is fully CSS-based and already includes mobile-responsive breakpoints and patterns, so the web app will work well on mobile browsers.

**Downstream impact:**
- Build Agent: No change to core stack — this was already the planned approach. Ensure the frontend is built mobile-first using the design system breakpoints.
- Test Agent: Add test that the app is usable at 390px viewport width (mobile breakpoint from Design System §8).
- Prompt templates: No change needed.

---

### CHG-003 — Reduced launch scope to 3 domains and 6 exercise types
**Date:** 2026-04-03
**Spec version before:** spec-v0.3
**Spec version after:** spec-v0.4
**Change type:** Scope
**Triggered by:** James — deliberate decision to reduce scope for initial user testing

**What changed:**
- §4 Feature #5: Exercise library reduced from 5 domains / 10 exercise types to 3 domains / 6 exercise types. Executive Function and Episodic Memory domains deferred to v1.1.
- §5 Out of Scope: Executive Function and Episodic Memory domains and their exercise variants explicitly added as out of scope for v1.
- §6 Data model: Domain enum updated to 3 values (processing_speed, working_memory, attention); exercise_type enum now explicitly lists the 6 v1 exercise types.

**Why:**
A tighter launch scope produces a more polished, testable product. Three domains with two solid exercise variants each is a complete and coherent experience. Executive Function and Episodic Memory can be added in v1.1 once the core pipeline is validated.

**Downstream impact:**
- Build Agent: Significantly reduces the exercise implementation workload. Only 6 exercise components needed instead of 10. Domain enum is now fixed — do not add placeholders for v1.1 domains.
- Test Agent: Feature coverage matrix should list 6 exercise types, not 10. Tests should confirm that only the 3 v1 domains are accessible in a training session.
- Prompt templates: No change needed, but worth noting for future Design Agent runs: explicitly ask the user to confirm domain count before spec is finalised.
