#!/usr/bin/env python3
"""
Feedback Agent Pipeline
=======================
Nightly autonomous pipeline:
  1.  Fetch unprocessed feedback from DB
  2.  Check GitHub for resolved design items (ready-to-implement label)
  3.  Synthesise feedback → implementable + non-implementable change items
  4.  Create GitHub Issues for non-implementable items (idempotent)
  5.  Filter items to those that are autonomously implementable
  6.  Create a feature branch
  7.  Implement each change (write source files to disk)
  8.  Update test files to stay in sync with code changes
  9.  Run full test suite — auto-fix failures up to 3 times
  10. Update spec.md
  11. Append to run-log.md
  12. Commit everything + push branch
  13. Open PR
  14. Close resolved GitHub issues that were implemented
  15. Mark feedback entries as processed

Usage:
    python feedback_agent/pipeline.py

Environment variables:
    DATABASE_URL          PostgreSQL connection string (required)
    ANTHROPIC_API_KEY     Anthropic API key (required)
    GITHUB_TOKEN          GitHub token for issue creation + PR (required in CI)
    GITHUB_REPOSITORY     Repo name e.g. "james-jxr/app-dev-capability" (required in CI)
    DRY_RUN               Set to "1" to synthesise only, skip implementation + PR
"""

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

# Allow running from the brain-training root or repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

import anthropic

from feedback_agent.db import (
    fetch_unprocessed_feedback,
    get_conn,
    insert_feedback_run,
    mark_feedback_processed,
    update_feedback_run,
)
from feedback_agent.synthesizer import synthesise
from feedback_agent.implementer import implement_change
from feedback_agent.git_helper import (
    commit_all,
    create_branch,
    open_pr,
    push_branch,
    REPO_ROOT as GIT_REPO_ROOT,
)
from feedback_agent.github_issues import (
    close_issue,
    create_issues_for_failed_implementations,
    create_issues_for_non_implementable,
    fetch_resolved_design_items,
)
from feedback_agent.spec_updater import update_spec
from feedback_agent.test_updater import update_tests

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
MAX_FIX_ITERATIONS = 3

REPO_ROOT = GIT_REPO_ROOT
APP_ROOT = str(Path(REPO_ROOT).resolve())  # apps/brain-training/ absolute, no .. segments
RUN_LOG = str(Path(APP_ROOT) / "run-log.md")

# Actual git repo root (needed by spec_updater, which diffs from the repo top-level)
_git_root_proc = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, cwd=APP_ROOT
)
GIT_REPO_ACTUAL_ROOT = _git_root_proc.stdout.strip() if _git_root_proc.returncode == 0 else APP_ROOT

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "james-jxr/app-dev-capability")

PROMPTS_DIR = Path(__file__).parent / "prompts"


# ── Test runner ────────────────────────────────────────────────────────────────

def _run_tests() -> tuple[bool, str]:
    """Run backend pytest + frontend vitest. Returns (passed, summary_text)."""
    results = []
    passed = True

    # Backend — use a temp file so the working tree stays clean
    env = {**os.environ, "DATABASE_URL": "sqlite:////tmp/pipeline_test.db"}
    backend_result = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/tests/", "-q", "--tb=short",
         "--no-header", "-W", "ignore::DeprecationWarning"],
        cwd=APP_ROOT, capture_output=True, text=True, env=env
    )
    backend_out = (backend_result.stdout + backend_result.stderr).strip()
    backend_ok = backend_result.returncode == 0
    if not backend_ok:
        passed = False
    results.append(f"Backend: {'PASSED' if backend_ok else 'FAILED'}\n{backend_out}")

    # Frontend
    frontend_result = subprocess.run(
        ["npm", "test"],
        cwd=str(Path(APP_ROOT) / "frontend"),
        capture_output=True, text=True
    )
    frontend_out = (frontend_result.stdout + frontend_result.stderr).strip()
    # Strip ANSI escape codes and npm/vite noise
    frontend_lines = [
        _ANSI_RE.sub('', l) for l in frontend_out.splitlines()
        if not l.startswith(">") and "esbuild" not in l and "oxc" not in l
    ]
    frontend_out = "\n".join(frontend_lines).strip()
    frontend_ok = frontend_result.returncode == 0
    if not frontend_ok:
        passed = False
    results.append(f"Frontend: {'PASSED' if frontend_ok else 'FAILED'}\n{frontend_out}")

    return passed, "\n\n".join(results)


def _extract_failing_info(test_output: str) -> tuple[list, list]:
    """
    Parse test output to find failing test file paths (backend + frontend).
    Returns (backend_test_files, frontend_test_files).
    """
    backend_files = set()
    frontend_files = set()

    for line in test_output.splitlines():
        # pytest: "FAILED backend/tests/test_foo.py::TestClass::test_method"
        if line.startswith("FAILED "):
            path = line.split("FAILED ")[1].split("::")[0].strip()
            if path.startswith("backend/"):
                backend_files.add(path)
        # vitest: " ❯ src/test/foo.test.js"
        if "src/test/" in line and ".test." in line:
            part = [p for p in line.split() if "src/test/" in p]
            if part:
                frontend_files.add(f"frontend/{part[0].lstrip('/')}")

    return list(backend_files), list(frontend_files)


def _auto_fix_tests(test_output: str, changed_files: dict) -> bool:
    """
    Call Claude to fix failing tests. Writes fixes to disk.
    Returns True if fixes were written (doesn't re-run tests — caller does that).
    """
    backend_tests, frontend_tests = _extract_failing_info(test_output)
    all_test_paths = backend_tests + frontend_tests

    if not all_test_paths:
        # Can't identify specific files — pass all changed files + full output
        all_test_paths = list(changed_files.keys())

    # Read failing test files + their source counterparts
    files_to_read = {}
    for path in all_test_paths:
        abs_path = Path(APP_ROOT) / path
        if abs_path.exists():
            rel = str(Path(path))
            files_to_read[rel] = abs_path.read_text()

    # Also include the recently changed source files
    files_to_read.update(changed_files)

    if not files_to_read:
        print("  [fix] no files to read for auto-fix")
        return False

    file_contents = "\n\n".join(
        f"### {p}\n```\n{c}\n```" for p, c in files_to_read.items()
    )

    prompt = ((PROMPTS_DIR / "test_fix.md").read_text()
              .replace("{test_output}", test_output[:8000])
              .replace("{failing_files_with_content}", file_contents[:20000]))

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    if not raw:
        print(f"  [fix] Claude returned empty response (stop_reason={message.stop_reason})")
        return False

    try:
        file_map = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  [fix] Claude returned non-JSON (stop_reason={message.stop_reason}): {raw[:200]}")
        return False

    if not file_map:
        print("  [fix] Claude suggested no changes")
        return False

    for rel_path, content in file_map.items():
        abs_path = Path(APP_ROOT) / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content)
        print(f"  [fix] wrote {rel_path}")

    return True


# ── Run log ────────────────────────────────────────────────────────────────────

def _append_run_log(summary: dict):
    """Append a structured entry to run-log.md."""
    today = date.today().isoformat()
    mode = "automated" if os.environ.get("CI") else "local"
    status = summary.get("status", "unknown")
    feedback_count = summary.get("feedback_count", 0)
    changes = summary.get("changes_applied", [])
    issues = summary.get("issues_created", [])
    spec_version = summary.get("spec_version", "unchanged")
    test_result = summary.get("test_result", "not run")
    pr_url = summary.get("pr_url", "")
    errors = summary.get("errors", "")

    changes_text = "\n".join(f"  - {c['id']}: {c['title']}" for c in changes) or "  (none)"
    issues_text = "\n".join(f"  - {i['issue_url']}" for i in issues) or "  (none)"
    skipped = summary.get("failed_implementations", [])
    skipped_text = "\n".join(f"  - {s['item']['id']}: {s['error'][:120]}" for s in skipped) or "  (none)"

    entry = f"""
## Run — {today} ({mode})
**Status:** {status}
**Feedback processed:** {feedback_count}
**Changes applied:**
{changes_text}
**Skipped implementations (GitHub issues created):**
{skipped_text}
**Issues created:**
{issues_text}
**Spec version:** {spec_version}
**Test result:** {test_result}
**PR:** {pr_url or '(none)'}
**Errors:** {errors or '(none)'}
"""

    log_path = Path(RUN_LOG)
    if log_path.exists():
        existing = log_path.read_text()
        log_path.write_text(existing + entry)
    else:
        log_path.write_text(f"# Feedback Pipeline Run Log\n{entry}")


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline():
    print(f"\n{'='*60}")
    print(f"Feedback Agent Pipeline — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    conn = get_conn()
    run_id = insert_feedback_run(conn, {"status": "pending"})
    print(f"Run ID: {run_id}")

    run_summary = {
        "status": "pending",
        "feedback_count": 0,
        "changes_applied": [],
        "failed_implementations": [],
        "issues_created": [],
        "spec_version": "unchanged",
        "test_result": "not run",
        "pr_url": "",
        "errors": "",
    }

    try:
        # ── 1. Fetch unprocessed feedback ──────────────────────────────────────
        feedback = fetch_unprocessed_feedback(conn)
        print(f"Unprocessed feedback items: {len(feedback)}")
        run_summary["feedback_count"] = len(feedback)

        if not feedback:
            update_feedback_run(conn, run_id, {"status": "no_changes", "feedback_count": 0})
            run_summary["status"] = "no_changes"
            _append_run_log(run_summary)
            print("Nothing to process. Exiting.")
            return

        # ── 2. Check for resolved design items ────────────────────────────────
        print("\n[Step 2] Checking for resolved design items on GitHub...")
        resolved_items = fetch_resolved_design_items(GITHUB_TOKEN, GITHUB_REPOSITORY)
        if resolved_items:
            print(f"  Found {len(resolved_items)} resolved item(s) to implement")

        # ── 3. Synthesise ──────────────────────────────────────────────────────
        print("\n[Step 3] Synthesising feedback with Claude...")
        items = synthesise(feedback, resolved_items=resolved_items)
        print(f"Change items identified: {len(items)}")
        for item in items:
            flag = "✓" if item.get("implementable") else "–"
            print(f"  [{flag}] [{item['priority'].upper()}] {item['id']}: {item['title']}")

        update_feedback_run(conn, run_id, {
            "feedback_count": len(feedback),
            "themes": items,
        })

        if DRY_RUN:
            print("\n[DRY RUN] Skipping implementation and PR.")
            update_feedback_run(conn, run_id, {"status": "dry_run"})
            run_summary["status"] = "dry_run"
            _append_run_log(run_summary)
            return

        # ── 4. Create GitHub Issues for non-implementable items ───────────────
        print("\n[Step 4] Creating GitHub Issues for non-implementable items...")
        created_issues = create_issues_for_non_implementable(items, GITHUB_TOKEN, GITHUB_REPOSITORY)
        run_summary["issues_created"] = created_issues

        # ── 5. Filter to implementable items ──────────────────────────────────
        # Trust the synthesiser's `implementable` flag directly. A type-based
        # allowlist was previously used here but it silently blocked design/feature
        # items that had been resolved by the owner (who provided a decision comment
        # and set ready-to-implement). The synthesiser already marks those
        # implementable=true, so no extra filter is needed.
        to_implement = [i for i in items if i.get("implementable")]
        print(f"\n[Step 7] Implementing {len(to_implement)} item(s)...")

        if not to_implement:
            print("No implementable items this run.")
            mark_feedback_processed(conn, [r["id"] for r in feedback])
            update_feedback_run(conn, run_id, {"status": "no_changes"})
            run_summary["status"] = "no_changes"
            _append_run_log(run_summary)
            return

        # ── 6. Create branch ──────────────────────────────────────────────────
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        branch_name = f"feedback/{date_str}-run-{run_id}"
        create_branch(branch_name)
        print(f"Branch: {branch_name}")

        # ── 7. Implement each change ──────────────────────────────────────────
        applied = []
        failed_implementations = []  # items that errored or returned no files
        all_changed_files = {}  # rel_path → new content

        for item in to_implement:
            print(f"\n  Implementing: {item['id']}")
            try:
                file_map = implement_change(item)
                if file_map:
                    applied.append({
                        "id": item["id"],
                        "title": item["title"],
                        "files_changed": list(file_map.keys()),
                    })
                    for rel_path in file_map:
                        abs_path = Path(APP_ROOT) / rel_path
                        if abs_path.exists():
                            all_changed_files[rel_path] = abs_path.read_text()
                else:
                    print(f"  [skip] {item['id']} — no files written")
                    failed_implementations.append({
                        "item": item,
                        "error": "No files were written — Claude returned an empty or unparseable response.",
                    })
            except Exception as e:
                print(f"  [error] {item['id']}: {e}")
                failed_implementations.append({"item": item, "error": str(e)})

        # Create GitHub Issues for failed implementations so they can be reviewed
        if failed_implementations:
            print(f"\n  Creating issues for {len(failed_implementations)} failed implementation(s)...")
            failed_issues = create_issues_for_failed_implementations(
                failed_implementations, GITHUB_TOKEN, GITHUB_REPOSITORY
            )
            run_summary["issues_created"].extend(failed_issues)

        if not applied:
            print("\nNo changes were written. Exiting without commit.")
            update_feedback_run(conn, run_id, {"status": "no_changes"})
            run_summary["status"] = "no_changes"
            _append_run_log(run_summary)
            return

        run_summary["changes_applied"] = applied
        run_summary["failed_implementations"] = failed_implementations

        # ── 8. Update tests ───────────────────────────────────────────────────
        print("\n[Step 8] Updating tests to reflect code changes...")
        try:
            update_tests(all_changed_files)
        except Exception as e:
            print(f"  [warn] test update failed: {e}")

        # ── 9. Run tests with auto-fix loop ───────────────────────────────────
        print("\n[Step 9] Running test suite...")
        test_passed = False
        last_test_output = ""

        for iteration in range(1, MAX_FIX_ITERATIONS + 1):
            test_passed, test_output = _run_tests()
            last_test_output = test_output
            summary_line = test_output.split("\n")[-1] if test_output else "no output"

            if test_passed:
                print(f"  Tests passed (iteration {iteration})")
                run_summary["test_result"] = f"PASSED (iteration {iteration}): {summary_line}"
                break
            else:
                print(f"  Tests FAILED (iteration {iteration}/{MAX_FIX_ITERATIONS})")
                if iteration < MAX_FIX_ITERATIONS:
                    print(f"  Auto-fixing...")
                    fixed = _auto_fix_tests(test_output, all_changed_files)
                    if not fixed:
                        print("  No fixes suggested — stopping early")
                        break

        if not test_passed:
            run_summary["status"] = "tests_failed"
            run_summary["test_result"] = f"FAILED after {MAX_FIX_ITERATIONS} iterations"
            run_summary["errors"] = last_test_output[-2000:]
            update_feedback_run(conn, run_id, {
                "status": "tests_failed",
                "error": last_test_output[-2000:],
            })
            # Record failure in run-log (artifact upload in CI will capture it)
            _append_run_log(run_summary)
            print(f"\n[ABORT] Tests failed after {MAX_FIX_ITERATIONS} fix attempts. No PR created.")
            sys.exit(1)

        # ── 10. Update spec.md ────────────────────────────────────────────────
        print("\n[Step 10] Updating spec.md...")
        try:
            new_spec_version = update_spec(GIT_REPO_ACTUAL_ROOT, APP_ROOT)
            run_summary["spec_version"] = new_spec_version or "unchanged"
        except Exception as e:
            print(f"  [warn] spec update failed: {e}")

        # ── 11. Append run-log ────────────────────────────────────────────────
        run_summary["status"] = "completed"
        _append_run_log(run_summary)

        # ── 12. Commit and push ───────────────────────────────────────────────
        commit_msg = (
            f"[feedback-agent] Apply {len(applied)} feedback-driven change(s)\n\n"
            + "\n".join(f"- {c['title']}" for c in applied)
            + "\n\nCo-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
        )
        committed = commit_all(commit_msg)
        if not committed:
            update_feedback_run(conn, run_id, {"status": "no_changes"})
            return

        push_branch(branch_name)

        # ── 13. Open PR ───────────────────────────────────────────────────────
        pr_body = (
            "## Automated feedback-driven changes\n\n"
            "This PR was generated by the nightly feedback agent pipeline.\n\n"
            "### Changes applied\n"
            + "\n".join(f"- **{c['id']}**: {c['title']}" for c in applied)
            + "\n\n### Tests\n"
            f"✅ Full test suite passed ({run_summary['test_result']})\n\n"
            "### Spec\n"
            f"Spec updated to {run_summary['spec_version']}\n\n"
            "### Feedback processed\n"
            f"{len(feedback)} feedback entries marked as processed.\n\n"
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
        )
        pr_url = open_pr(
            branch_name,
            f"[feedback-agent] {len(applied)} feedback-driven change(s)",
            pr_body,
        )
        print(f"\nPR created: {pr_url}")
        run_summary["pr_url"] = pr_url

        # ── 14. Close resolved issues that were implemented ───────────────────
        implemented_ids = {c["id"] for c in applied}
        for resolved in resolved_items:
            if resolved["id"] in implemented_ids:
                close_issue(GITHUB_TOKEN, GITHUB_REPOSITORY, resolved["issue_number"], pr_url)

        # ── 15. Mark feedback as processed ───────────────────────────────────
        mark_feedback_processed(conn, [r["id"] for r in feedback])
        update_feedback_run(conn, run_id, {
            "status": "completed",
            "changes_applied": applied,
            "branch_name": branch_name,
            "pr_url": pr_url,
        })

        print(f"\n{'='*60}")
        print(f"Pipeline complete. {len(applied)} change(s) → {pr_url}")
        print(f"{'='*60}\n")

    except Exception as e:
        run_summary["status"] = "error"
        run_summary["errors"] = str(e)
        update_feedback_run(conn, run_id, {"status": "failed", "error": str(e)})
        _append_run_log(run_summary)
        print(f"\n[FATAL] Pipeline failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_pipeline()
