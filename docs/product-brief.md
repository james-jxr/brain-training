# Product Brief: Brain Training App

**Version:** 1.0
**Date:** 2026-04-16
**Status:** Approved

---

## 1. Purpose and Problem Statement

Adults who want to maintain or improve their cognitive performance have no honest, engaging tool to do it with. Consumer brain-training apps either overclaim their benefits (raising regulatory and trust problems) or fail to sustain engagement long enough for meaningful gains to occur — the evidence requires 20+ cumulative hours of sustained, varied, adaptive training before near-transfer benefits emerge.

The Brain Training App solves both problems: it makes evidence-backed claims only, and it is designed around the engagement mechanics that drive sustained daily practice.

## 2. Target User

**Primary user:** Ambitious professionals aged 25–45, motivated by evidence and self-improvement, comfortable with digital products, willing to commit to a daily habit. They read the footnotes. They will notice inflated claims.

**Secondary user:** Adults aged 46–80 proactively managing cognitive health. The UI must support this cohort without patronising the primary audience.

**What they currently do instead:** Nothing structured. Some use apps like Lumosity or Elevate but lose trust when the claims feel unsupported, or lose interest when difficulty stops adapting to them.

**Key insight:** The commitment required (20+ hours) is longer than any consumer app has managed to retain users. Honest claims + genuine adaptive difficulty + visible evidence of progress is the retention mechanism.

## 3. Core Value Proposition

The only cognitive training app that is honest about what the science actually shows — and designed to keep you training long enough for the evidence to matter.

## 4. MVP Scope

- User accounts with email/password authentication
- Baseline cognitive assessment across all five domains, setting adaptive difficulty starting points
- Daily training sessions (15–20 min), covering 2–3 domains per session with adaptive difficulty
- Cognitive exercise library: 2 tasks per domain for 3 domains at launch (Processing Speed, Working Memory, Attention & Inhibitory Control)
- Post-session summary with accuracy score and streak
- Progress dashboard: per-domain scores, 30-day trend, streak counter, Brain Health Score
- Brain Health Score combining cognitive performance (60%) and lifestyle inputs (40%)
- Lifestyle habit logging (exercise, sleep, stress, mood, social)
- About the Science section with research references
- In-app feedback capture (persistent floating button + post-session prompt)
- Free-play mode (launch any exercise directly from dashboard)
- Account settings (email, password, notifications, delete account)

## 5. Out of Scope (MVP)

- Native iOS and Android apps (web app only in v1)
- Executive Function and Episodic Memory domains (deferred to v1.1)
- Symbol matching task (hidden pending replacement)
- Offline mode (requires internet connection)
- Social features, leaderboards, multiplayer
- Apple Health / Google Fit integration
- Audio or rhythm-based tasks
- Push notifications (preference stored, send mechanism deferred)
- Far-transfer claims (only near-transfer claimed)

## 6. Success Criteria

- Users complete at least 3 sessions per week after their first week
- Fewer than 5% of users who complete baseline abandon before their third session
- Brain Health Score moves meaningfully (>5 points) for users with 10+ sessions completed

## 7. Constraints

- **Stack:** React + Vite frontend, FastAPI backend, PostgreSQL (Railway)
- **Deployment:** Railway (frontend static + backend service + managed PostgreSQL)
- **Platform:** Web-first, fully functional on mobile browsers at 375px+ width
- **CI/CD:** GitHub Actions nightly feedback pipeline
- **Auth:** httpOnly cookie + localStorage dual-storage for cross-origin Railway deployment

## 8. Open Questions

All open questions resolved. Spec at v0.8 Approved.
