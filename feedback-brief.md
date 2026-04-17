# Design Agent Brief: In-App Feedback Feature
**Brief version:** feedback-v1.0
**Date:** 2026-04-03
**Target spec:** brain-training spec-v0.4 → spec-v0.5 (amendment only)
**Scope:** Additive only — do not alter any existing spec sections except changelog, §4, §6, §7, §9

---

## Feature Summary

Add a lightweight, free-text feedback mechanism to the Brain Training App that captures user feedback in two contexts:

1. **Always-available widget** — a persistent floating button on every authenticated page that opens a small feedback form
2. **Post-game prompt** — a modal that appears on the Session Summary screen after every completed training session, prompting the user for immediate in-context feedback before they leave

Feedback is free text only. No ratings, no categories. The goal is to capture spontaneous, contextual user thoughts that can be compiled into a feedback digest and fed back into future design iterations.

---

## Design Decisions (Pre-resolved)

These decisions are final — the Design Agent should not re-open them:

- **Free text only** — no star ratings, thumbs, or categories in v1
- **Auth required** — feedback is only available to logged-in users; no anonymous submissions
- **Post-game prompt is optional** — user can skip it; it must not block access to session results
- **Widget placement** — floating button, bottom-right of screen, must not obscure the bottom navigation bar on mobile
- **Confirmation** — show a brief "Thank you for your feedback" confirmation on submit; auto-dismiss after 2 seconds
- **No admin UI in v1** — feedback is stored in the database and retrievable via API; no in-app admin dashboard

---

## What the Design Agent Must Produce

A spec amendment covering exactly these sections:

### 1. New MVP feature entry (§4)
Add item 13: In-app feedback capture. One paragraph describing the feature as it will appear to the user.

### 2. New entity: FeedbackEntry (§6)
Define the data model with these fields:
- id, user_id (FK → User), page_context (string — the page or context where feedback was submitted, e.g. "dashboard", "session_summary", "progress"), session_id (nullable FK → Session — only set when submitted from the post-game prompt), feedback_text (string, max 1000 chars), created_at (datetime)

### 3. New API route (§7)
Add a Feedback section with:
- `POST /api/feedback` — submit feedback (auth required). Request body: page_context, session_id (optional), feedback_text. Response: id, created_at.

### 4. New frontend components (§9)
Add to the file structure:
- `src/components/ui/FeedbackWidget.jsx` — persistent floating button + modal, rendered in App.jsx so it is available on all authenticated pages
- `src/components/ui/PostGameFeedback.jsx` — post-session modal, rendered within SessionSummary.jsx
- `backend/routers/feedback.py` — new router
- `backend/models/feedback_entry.py` — new model
- `backend/schemas/feedback.py` — new schema

### 5. Changelog entry
Add v0.5 to the changelog table.

---

## Integration Points

- `App.jsx` — mount `<FeedbackWidget />` inside the authenticated route wrapper so it appears on all logged-in pages
- `SessionSummary.jsx` — render `<PostGameFeedback sessionId={sessionId} />` after the summary content; it is optional/dismissible
- `client.js` — add `submitFeedback(pageContext, feedbackText, sessionId)` API function
- `backend/main.py` — register the new feedback router

---

## What Is Explicitly Out of Scope for This Amendment

- Admin dashboard to view/triage feedback
- Feedback tagging, categorisation, or sentiment analysis
- Email notifications on new feedback
- Feedback export
- Any changes to existing spec sections beyond what is listed above
