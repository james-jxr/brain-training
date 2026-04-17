You are updating the functional spec for the Brain Training app.

Current spec version: {current_version}
Today's date: {today}

## Code changes since spec was last updated

Files changed:
{changed_files}

Code diff (backend + frontend source, first 25 KB):
```diff
{code_diff}
```

Test diff (first 8 KB):
```diff
{test_diff}
```

## Current spec.md

{spec_content}

---

## Instructions

Analyse the diffs and update the spec above. Return the COMPLETE updated spec.md — no commentary, no preamble, no code fences. Just the raw markdown content starting with '# App Specification'.

Rules:
- Bump the minor version (e.g. v0.7 → v0.8) and update the date to {today} if there are meaningful spec-relevant changes
- Add a concise changelog entry summarising what changed
- Update only sections affected by the diffs — do not rewrite unchanged sections
- If §11c (test coverage) exists, update test counts if tests changed
- If there are no meaningful spec-relevant changes, do not bump the version — just note 'no spec changes' in a new changelog row
- Do NOT truncate any section — output the full document
