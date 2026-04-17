#!/usr/bin/env bash
# Run all regression tests for the Brain Training app.
# Exits 0 if all pass, 1 if any fail.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

FAILED=0
BACKEND_RESULT=""
FRONTEND_RESULT=""

echo ""
echo "Brain Training — Regression Tests"
echo "=================================="

# ── Backend ────────────────────────────────────────────────────────────────────
echo ""
echo "Backend (pytest)"
echo "────────────────"
BACKEND_OUTPUT=$("$ROOT/backend/venv/bin/pytest" "$ROOT/backend/tests/" \
  -q --tb=short --no-header -W ignore::DeprecationWarning 2>&1) || FAILED=1

echo "$BACKEND_OUTPUT"

# Extract summary line (last non-empty line)
BACKEND_RESULT=$(echo "$BACKEND_OUTPUT" | grep -E "passed|failed|error" | tail -1 || echo "no results")

# ── Frontend ───────────────────────────────────────────────────────────────────
echo ""
echo "Frontend (Vitest)"
echo "─────────────────"
FRONTEND_OUTPUT=$(cd "$ROOT/frontend" && npm test 2>&1) || FAILED=1

# Print Vitest output but filter out the npm boilerplate and esbuild deprecation warnings
echo "$FRONTEND_OUTPUT" | grep -v "^>" | grep -v "^$" | \
  grep -v "esbuild.*deprecated" | grep -v "oxc.*deprecated" | \
  grep -v "Both esbuild and oxc" | grep -v "jsxImportSource" || true

FRONTEND_RESULT=$(echo "$FRONTEND_OUTPUT" | grep -E "Tests.*passed|Tests.*failed" | tail -1 || echo "no results")

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "=================================="
echo "Summary"
echo "──────────────────────────────────"
echo "  Backend:  $BACKEND_RESULT"
echo "  Frontend: $FRONTEND_RESULT"
echo ""

if [ $FAILED -eq 0 ]; then
  echo "  ✓ All tests passed"
  echo "=================================="
  exit 0
else
  echo "  ✗ Tests FAILED"
  echo "=================================="
  exit 1
fi
