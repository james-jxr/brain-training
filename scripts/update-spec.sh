#!/usr/bin/env bash
# Autonomously update spec.md to reflect the current state of the codebase.
#
# How it works:
#   1. Finds the git commit where spec.md was last modified
#   2. Computes a diff of code changes since that commit
#   3. Runs `claude -p` with spec.md content + diff inline in the prompt
#      Claude outputs the full updated spec to stdout — no file tools needed
#   4. Writes stdout directly to spec.md
#
# Usage:
#   ./scripts/update-spec.sh           # update spec.md in place
#   DRY_RUN=1 ./scripts/update-spec.sh # print the prompt Claude will receive, don't run it

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
SPEC="$ROOT/spec.md"
REPO_ROOT=$(git -C "$ROOT" rev-parse --show-toplevel)
APP_REL="${ROOT#$REPO_ROOT/}"
PROMPT_FILE=$(mktemp /tmp/spec-update-prompt.XXXXXX)
trap 'rm -f "$PROMPT_FILE"' EXIT

# ── Current spec version ───────────────────────────────────────────────────────
CURRENT_VERSION=$(grep "^\*\*Spec Version:\*\*" "$SPEC" | grep -oE 'v[0-9]+\.[0-9]+')
echo "Current spec: spec-$CURRENT_VERSION"

# ── Find commit where spec.md was last changed ────────────────────────────────
SPEC_COMMIT=$(git -C "$REPO_ROOT" log --follow -1 --format="%H" -- "$APP_REL/spec.md")
SPEC_COMMIT_DATE=$(git -C "$REPO_ROOT" log -1 --format="%ci" "$SPEC_COMMIT")
echo "Spec last updated: $SPEC_COMMIT (${SPEC_COMMIT_DATE%% *})"

# ── Compute diffs since that commit ───────────────────────────────────────────
CODE_DIFF=$(git -C "$REPO_ROOT" diff "$SPEC_COMMIT" HEAD -- \
  "$APP_REL/backend/routers/" \
  "$APP_REL/backend/models/" \
  "$APP_REL/backend/services/" \
  "$APP_REL/backend/schemas/" \
  "$APP_REL/backend/main.py" \
  "$APP_REL/frontend/src/components/" \
  "$APP_REL/frontend/src/pages/" \
  "$APP_REL/frontend/src/hooks/" \
  "$APP_REL/frontend/src/api/" \
  "$APP_REL/frontend/src/utils/" \
  2>/dev/null | head -c 25000 || echo "(no code changes)")

TEST_DIFF=$(git -C "$REPO_ROOT" diff "$SPEC_COMMIT" HEAD -- \
  "$APP_REL/backend/tests/" \
  "$APP_REL/frontend/src/test/" \
  2>/dev/null | head -c 8000 || echo "(no test changes)")

CHANGED_FILES=$(git -C "$REPO_ROOT" diff --name-only "$SPEC_COMMIT" HEAD \
  -- "$APP_REL/" ':!'"$APP_REL/spec.md" 2>/dev/null || echo "(none)")

SPEC_CONTENT=$(cat "$SPEC")
TODAY=$(date +%Y-%m-%d)

# ── Write prompt to temp file ──────────────────────────────────────────────────
{
  echo "You are updating a functional spec document."
  echo ""
  echo "Current spec version: spec-$CURRENT_VERSION"
  echo "Today's date: $TODAY"
  echo ""
  echo "## Code changes since spec was last updated"
  echo ""
  echo "Files changed:"
  echo "$CHANGED_FILES"
  echo ""
  echo "Code diff (backend + frontend source, first 25 KB):"
  echo '```diff'
  echo "$CODE_DIFF"
  echo '```'
  echo ""
  echo "Test diff (first 8 KB):"
  echo '```diff'
  echo "$TEST_DIFF"
  echo '```'
  echo ""
  echo "## Current spec.md"
  echo ""
  echo "$SPEC_CONTENT"
  echo ""
  echo "---"
  echo ""
  echo "## Instructions"
  echo ""
  echo "Analyse the diffs and update the spec above. Return the COMPLETE updated spec.md — no commentary, no preamble, no code fences. Just the raw markdown content starting with '# App Specification'."
  echo ""
  echo "Rules:"
  echo "- Bump the minor version (e.g. v0.7 → v0.8) and update the date to $TODAY if there are meaningful spec-relevant changes"
  echo "- Add a concise changelog entry summarising what changed"
  echo "- Update only sections affected by the diffs — do not rewrite unchanged sections"
  echo "- If §11c (test coverage) exists, update test counts if tests changed"
  echo "- If there are no meaningful spec-relevant changes, do not bump the version — just note 'no spec changes' in a new changelog row"
  echo "- Do NOT truncate any section — output the full document"
} > "$PROMPT_FILE"

# ── Dry run: just print the prompt ────────────────────────────────────────────
if [ "${DRY_RUN:-0}" = "1" ]; then
  echo ""
  echo "=== DRY RUN — prompt that would be sent to Claude ==="
  cat "$PROMPT_FILE"
  exit 0
fi

# ── Run Claude — spec content in prompt, updated spec on stdout ────────────────
echo "Running Claude to update spec.md..."

UPDATED=$(claude -p --model sonnet "$(cat "$PROMPT_FILE")")

if [ -z "$UPDATED" ]; then
  echo "Error: Claude returned empty output"
  exit 1
fi

# Write result back to spec.md
echo "$UPDATED" > "$SPEC"

echo ""
NEW_VERSION=$(grep "^\*\*Spec Version:\*\*" "$SPEC" | grep -oE 'v[0-9]+\.[0-9]+')
echo "Done: spec-$CURRENT_VERSION → spec-$NEW_VERSION"
