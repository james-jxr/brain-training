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
  7.  Implement each change (write source files to disk) — retry once on failure
  8.  Update test files to stay in sync with code changes
  9.  Run full test suite — auto-fix failures up to 3 times
      If still failing: isolate which change(s) broke tests, drop them, retry
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
    SUPABASE_URL          Agent Central Supabase URL (optional — falls back to built-in prompts)
    SUPABASE_SERVICE_KEY  Agent Central service role key (optional)
    DRY_RUN               Set to "1" to synthesise only, skip implementation + PR
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

# Allow running from the brain-training root or repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from feedback_agent.json_utils import extract_json

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
from feedback_agent.agent_loader import get_system_prompt
from feedback_agent.design_agent import review_needs_decision_issues

DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
MAX_FIX_ITERATIONS = 3

REPO_ROOT = GIT_REPO_ROOT
APP_ROOT = str(Path(REPO_ROOT).resolve())
RUN_LOG = str(Path(APP_ROOT) / "run-log.md")

_git_root_proc = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, cwd=APP_ROOT
)
GIT_REPO_ACTUAL_ROOT = _git_root_proc.stdout.strip() if _git_root_proc.returncode == 0 else APP_ROOT

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "james-jxr/app-dev-capability")

_TEST_FIX_BUILTIN_SYSTEM_PROMPT = """You are a senior software engineer fixing failing tests for a brain training web app.
Frontend: React/Vite. Backend: FastAPI/Python.

Fix the source code or test code to make the failing tests pass.
Return ONLY a JSON object mapping file paths to complete updated file contents.
Only include files that need changes. If no changes are needed, return {}.

Rules:
- Return valid JSON only — no prose, no markdown fences.
- Prefer fixing the source code if the test is testing correct behaviour.
- Prefer fixing the test if the source change was intentional and the test expectation is stale.
- Do not change the intent of tests — only fix genuine bugs or test/code mismatches.
- Do not add new features or refactor unrelated code.
- Fix the minimum amount needed to make the failing tests pass without breaking others.
- ALWAYS prefer testing exported pure functions over rendering React components.
- If you must render a component, use vi.useFakeTimers() — never rely on real time delays."""


# ── Transient retry ────────────────────────────────────────────────────────────

def _with_retry(fn, max_attempts: int = 3, backoff_base: float = 15.0):
    """
    Call fn() up to max_attempts times, retrying on transient API errors
    (rate limits, connection errors, server overload).
    Raises on the final failure or any non-transient error.
    """
    transient = (
        anthropic.RateLimitError,
        anthropic.APIConnectionError,
        anthropic.InternalServerError,
    )
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except transient as e:
            if attempt == max_attempts:
                raise
            wait = backoff_base * (2 ** (attempt - 1))
            print(f"  [retry] transient error on attempt {attempt}: {e}. Retrying in {wait:.0f}s...")
            time.sleep(wait)


# ── File state helpers ─────────────────────────────────────────────────────────

def _snapshot(paths: list[str], existing: dict) -> dict:
    """
    Record the current on-disk content of each path into `existing`.
    Paths already in `existing` are skipped (first-write wins — preserves original).
    Returns existing (mutated in place).
    """
    for rel_path in paths:
        if rel_path in existing:
            continue
        abs_path = Path(APP_ROOT) / rel_path
        existing[rel_path] = abs_path.read_text() if abs_path.exists() else None
    return existing


def _restore(originals: dict):
    """
    Restore files to their snapshotted state:
    - content present → overwrite with that content
    - content None (file didn't exist before) → delete if it now exists
    """
    for rel_path, content in originals.items():
        abs_path = Path(APP_ROOT) / rel_path
        if content is None:
            abs_path.unlink(missing_ok=True)
        else:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(content)


# ── Test runner ────────────────────────────────────────────────────────────────

def _run_tests() -> tuple[bool, str]:
    """Run backend pytest + frontend vitest. Returns (passed, summary_text)."""
    results = []
    passed = True

    env = {**os.environ, "DATABASE_URL": "sqlite:////tmp/pipeline_test.db"}
    backend_result = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/tests/", "-q", "--tb=short",
         "--no-header", "-W", "ignore::DeprecationWarning"],
        cwd=APP_ROOT, capture_output=True, text=True, env=env, timeout=120
    )
    backend_out = (backend_result.stdout + backend_result.stderr).strip()
    backend_ok = backend_result.returncode == 0
    if not backend_ok:
        passed = False
    results.append(f"Backend: {'PASSED' if backend_ok else 'FAILED'}\n{backend_out}")

    frontend_result = subprocess.run(
        ["npm", "test"],
        cwd=str(Path(APP_ROOT) / "frontend"),
        capture_output=True, text=True, timeout=180
    )
    frontend_out = (frontend_result.stdout + frontend_result.stderr).strip()
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
    """Parse test output for failing file paths. Returns (backend_files, frontend_files)."""
    backend_files = set()
    frontend_files = set()

    for line in test_output.splitlines():
        if line.startswith("FAILED "):
            path = line.split("FAILED ")[1].split("::")[0].strip()
            if path.startswith("backend/"):
                backend_files.add(path)
        if "src/test/" in line and ".test." in line:
            part = [p for p in line.split() if "src/test/" in p]
            if part:
                frontend_files.add(f"frontend/{part[0].lstrip('/')}")

    return list(backend_files), list(frontend_files)


def _auto_fix_tests(test_output: str, changed_files: dict) -> bool:
    """
    Call the testing_agent to fix failing tests. Writes fixes to disk.
    Returns True if fixes were written.
    """
    backend_tests, frontend_tests = _extract_failing_info(test_output)
    all_test_paths = backend_tests + frontend_tests

    if not all_test_paths:
        all_test_paths = list(changed_files.keys())

    files_to_read = {}
    for path in all_test_paths:
        abs_path = Path(APP_ROOT) / path
        if abs_path.exists():
            files_to_read[str(Path(path))] = abs_path.read_text()

    files_to_read.update(changed_files)

    if not files_to_read:
        print("  [fix] no files to read for auto-fix")
        return False

    file_contents = "\n\n".join(
        f"### {p}\n```\n{c}\n```" for p, c in files_to_read.items()
    )

    user_message = f"""## Failing test output

{test_output[:8000]}

## Failing test files and their source files

{file_contents[:20000]}"""

    system_prompt = get_system_prompt("testing_agent") or _TEST_FIX_BUILTIN_SYSTEM_PROMPT

    client = anthropic.Anthropic()
    message = _with_retry(lambda: client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ))

    raw = message.content[0].text
    if not raw.strip():
        print(f"  [fix] Claude returned empty response (stop_reason={message.stop_reason})")
        return False

    try:
        file_map = extract_json(raw)
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


# ── Change isolation ───────────────────────────────────────────────────────────

def _isolate_failing_changes(
    item_file_maps: list[tuple[dict, dict]],
    all_originals: dict,
) -> tuple[list[dict], list[dict]] | tuple[None, None]:
    """
    When the test fix loop exhausts its iterations, try to identify which
    individual change(s) caused the failure so the rest can proceed.

    Algorithm:
    1. Restore ALL files to their pre-run originals (implementation + test changes)
    2. Run tests — if they fail on clean state it's a pre-existing issue; return None, None
    3. Re-apply each item's file map one at a time, running tests after each addition
    4. If adding an item breaks tests: revert it and mark it as bad
    5. Return (good_applied_records, bad_applied_records)

    Returns (None, None) if tests fail on the clean baseline (can't isolate).
    """
    if len(item_file_maps) <= 1:
        # Nothing to isolate — one change failed, nothing else to save
        return None, None

    print("\n  [isolate] Restoring files to pre-run state...")
    _restore(all_originals)

    print("  [isolate] Running tests on clean baseline...")
    baseline_passed, baseline_out = _run_tests()
    if not baseline_passed:
        print("  [isolate] Tests fail on clean baseline — pre-existing failure, cannot isolate")
        # Restore the changes we just reverted so we don't leave the tree in a broken state
        for _, file_map in item_file_maps:
            for rel_path, content in file_map.items():
                if isinstance(content, str):
                    abs_path = Path(APP_ROOT) / rel_path
                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    abs_path.write_text(content)
        return None, None

    print("  [isolate] Baseline clean. Testing changes incrementally...")
    good: list[dict] = []
    bad: list[dict] = []
    # Track cumulative good state so we can revert only the newly added item on failure
    cumulative_good_files: dict = {}

    for applied_record, file_map in item_file_maps:
        item_id = applied_record["id"]

        # Apply this item's files on top of current cumulative good state
        for rel_path, content in file_map.items():
            if isinstance(content, str):
                abs_path = Path(APP_ROOT) / rel_path
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_text(content)

        passed, _ = _run_tests()

        if passed:
            print(f"  [isolate] ✓ {item_id} — passes in isolation")
            good.append(applied_record)
            cumulative_good_files.update(file_map)
        else:
            print(f"  [isolate] ✗ {item_id} — breaks tests, dropping")
            bad.append(applied_record)
            # Revert this item's files to the cumulative good state (or original)
            for rel_path in file_map:
                original = cumulative_good_files.get(rel_path) or all_originals.get(rel_path)
                abs_path = Path(APP_ROOT) / rel_path
                if original is None:
                    abs_path.unlink(missing_ok=True)
                else:
                    abs_path.write_text(original)

    return good, bad


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
        # ── 0. Design agent: auto-resolve needs-decision issues ─────────────
        print("\n[Stage 0] Running design agent on open needs-decision issues...")
        auto_resolved = review_needs_decision_issues(GITHUB_TOKEN, GITHUB_REPOSITORY)
        if auto_resolved:
            print(f"  Design agent resolved {auto_resolved} issue(s) → now ready to implement")

        # ── 1. Fetch unprocessed feedback ──────────────────────────────────────
        feedback = fetch_unprocessed_feedback(conn)
        print(f"Unprocessed feedback items: {len(feedback)}")
        run_summary["feedback_count"] = len(feedback)

        # ── 2. Check for resolved design items ────────────────────────────────
        print("\n[Stage 1] Checking for resolved design items on GitHub...")
        resolved_items = fetch_resolved_design_items(GITHUB_TOKEN, GITHUB_REPOSITORY)
        if resolved_items:
            print(f"  Found {len(resolved_items)} resolved item(s) to implement")

        if not feedback and not resolved_items:
            update_feedback_run(conn, run_id, {"status": "no_changes", "feedback_count": 0})
            run_summary["status"] = "no_changes"
            _append_run_log(run_summary)
            print("No new feedback and no resolved issues. Nothing to do.")
            return

        # ── 3. Synthesise ──────────────────────────────────────────────────────
        print("\n[Step 3] Synthesising feedback with Claude...")
        items = _with_retry(lambda: synthesise(feedback, resolved_items=resolved_items))
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
        to_implement = [i for i in items if i.get("implementable")]
        print(f"\n[Step 5] {len(to_implement)} implementable item(s).")

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
        print(f"\n[Step 7] Implementing {len(to_implement)} item(s)...")
        applied = []
        failed_implementations = []
        all_changed_files = {}       # rel_path → latest content (for test updater)
        item_file_maps = []          # [(applied_record, file_map), ...] for isolation
        all_originals: dict = {}     # rel_path → content before this run (for isolation)

        for item in to_implement:
            print(f"\n  Implementing: {item['id']}")

            # Snapshot originals before we write anything for this item
            _snapshot(item.get("files_likely_affected", []), all_originals)

            file_map = {}
            error_context = ""

            # First attempt
            try:
                file_map = implement_change(item)
            except Exception as e:
                error_context = str(e)
                print(f"  [error] {item['id']} attempt 1: {e}")

            # Retry once with error context if first attempt failed
            if not file_map:
                retry_description = item["description"]
                if error_context:
                    retry_description += f"\n\nRetry context: Previous attempt failed with: {error_context}. Check file paths carefully and ensure all affected files are returned."
                else:
                    retry_description += "\n\nRetry context: Previous attempt returned no files. Return the complete updated content for all files that need changing."

                print(f"  [retry] {item['id']} — retrying with error context...")
                try:
                    retry_item = {**item, "description": retry_description}
                    file_map = implement_change(retry_item)
                except Exception as e2:
                    error_context = f"Failed on both attempts: {e2}"
                    print(f"  [error] {item['id']} attempt 2: {e2}")

            if file_map:
                applied_record = {
                    "id": item["id"],
                    "title": item["title"],
                    "files_changed": list(file_map.keys()),
                }
                applied.append(applied_record)
                item_file_maps.append((applied_record, file_map))
                for rel_path in file_map:
                    abs_path = Path(APP_ROOT) / rel_path
                    if abs_path.exists():
                        all_changed_files[rel_path] = abs_path.read_text()
            else:
                print(f"  [skip] {item['id']} — no files written after retry")
                failed_implementations.append({
                    "item": item,
                    "error": error_context or "No files written — Claude returned an empty or unparseable response on both attempts.",
                })

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

        # ── 7b. Regression build (Stage 4) ───────────────────────────────────
        print("\n[Step 7b] Running regression build...")
        build_passed = False
        build_output = ""
        MAX_BUILD_ITERATIONS = 3

        for build_iter in range(1, MAX_BUILD_ITERATIONS + 1):
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=str(Path(APP_ROOT) / "frontend"),
                capture_output=True, text=True, timeout=120,
            )
            build_output = _ANSI_RE.sub(
                '', (build_result.stdout + build_result.stderr).strip()
            )
            if build_result.returncode == 0:
                build_passed = True
                print(f"  Build passed (iteration {build_iter})")
                break
            else:
                print(f"  Build FAILED (iteration {build_iter}/{MAX_BUILD_ITERATIONS})")
                if build_iter < MAX_BUILD_ITERATIONS:
                    print("  Asking Claude to fix the build error...")
                    # Ask Claude to fix only the changed files
                    changed_src = "\n".join(
                        f"### {p}\n```\n{c}\n```"
                        for p, c in all_changed_files.items()
                    )
                    fix_prompt = (
                        f"The frontend build failed with this error:\n\n```\n{build_output[-3000:]}\n```\n\n"
                        f"The following files were changed in this pipeline run:\n\n{changed_src}\n\n"
                        f"Fix only the changed files to resolve the build error. "
                        f"Do not modify other files."
                    )
                    try:
                        build_fix_client = anthropic.Anthropic()
                        build_fix_msg = _with_retry(lambda: build_fix_client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=8192,
                            messages=[{"role": "user", "content": fix_prompt}],
                        ))
                        fix_result = extract_json(build_fix_msg.content[0].text)
                        fix_files = fix_result.get("files", {})
                        for rel_path, content in fix_files.items():
                            abs_path = Path(APP_ROOT) / rel_path
                            abs_path.write_text(content)
                            all_changed_files[rel_path] = content
                            print(f"    Applied build fix: {rel_path}")
                    except Exception as e:
                        print(f"    [warn] build fix attempt failed: {e}")

        if not build_passed:
            issue_title = f"[pipeline] Build failed after {MAX_BUILD_ITERATIONS} attempts"
            changed_list = "\n".join(f"- `{p}`" for p in all_changed_files)
            issue_body = (
                f"The nightly feedback pipeline could not fix a build failure after "
                f"{MAX_BUILD_ITERATIONS} iterations.\n\n"
                f"**Build error (last attempt):**\n```\n{build_output[-3000:]}\n```\n\n"
                f"**Changed files:**\n{changed_list}\n\n"
                f"These changes have not been committed. "
                f"Please fix the build manually and re-run the pipeline."
            )
            if GITHUB_TOKEN and GITHUB_REPOSITORY:
                from feedback_agent.github_issues import _get_repo
                _gh_repo = _get_repo(GITHUB_TOKEN, GITHUB_REPOSITORY)
                _gh_repo.create_issue(
                    title=issue_title, body=issue_body,
                    labels=["feedback-agent", "pipeline-failure"],
                )
            run_summary["status"] = "build_failed"
            run_summary["errors"] = f"Build failed after {MAX_BUILD_ITERATIONS} attempts"
            update_feedback_run(conn, run_id, {"status": "build_failed", "error": build_output[-2000:]})
            _append_run_log(run_summary)
            print(f"\n[ABORT] Build could not be fixed. No PR created.")
            sys.exit(1)

        # ── 8. Update tests ───────────────────────────────────────────────────
        print("\n[Step 8] Updating tests to reflect code changes...")
        test_file_originals: dict = {}
        try:
            # Snapshot existing test files before update_tests touches them
            test_dirs = [
                Path(APP_ROOT) / "backend" / "tests",
                Path(APP_ROOT) / "frontend" / "src" / "test",
            ]
            for tdir in test_dirs:
                if tdir.exists():
                    for p in tdir.rglob("*"):
                        if p.is_file():
                            rel = str(p.relative_to(APP_ROOT))
                            test_file_originals[rel] = p.read_text()

            updated_test_files = update_tests(all_changed_files)
            # Track new/updated test files so isolation can restore them
            for rel_path in updated_test_files:
                if rel_path not in test_file_originals:
                    all_originals[rel_path] = None  # new file
                else:
                    all_originals[rel_path] = test_file_originals[rel_path]  # had prior content
        except Exception as e:
            print(f"  [warn] test update failed: {e}")

        # ── 9. Run tests with auto-fix loop ───────────────────────────────────
        print("\n[Step 9] Running test suite...")
        test_passed = False
        last_test_output = ""
        iterations_run = 0

        for iteration in range(1, MAX_FIX_ITERATIONS + 1):
            iterations_run = iteration
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
                    print("  Auto-fixing...")
                    fixed = _auto_fix_tests(test_output, all_changed_files)
                    if not fixed:
                        print("  No fixes suggested — stopping early")
                        break

        # ── 9b. Change isolation if tests still failing ───────────────────────
        if not test_passed and len(item_file_maps) > 1:
            print(f"\n[Step 9b] Tests still failing after {iterations_run} attempt(s).")
            print("  Isolating which change(s) caused the failure...")

            good_applied, bad_applied = _isolate_failing_changes(item_file_maps, all_originals)

            if good_applied is not None:
                print(f"\n  Isolation result: {len(good_applied)} safe, {len(bad_applied)} dropped")

                # Log dropped items as failed implementations
                bad_ids = {r["id"] for r in bad_applied}
                for bad_record in bad_applied:
                    original_item = next(
                        (i for i in to_implement if i["id"] == bad_record["id"]), {}
                    )
                    failed_implementations.append({
                        "item": original_item or bad_record,
                        "error": "Isolated as the cause of persistent test failures. Dropped to allow other changes to proceed.",
                    })

                if good_applied:
                    # Update applied list to only the safe changes
                    applied = good_applied
                    run_summary["changes_applied"] = applied
                    run_summary["failed_implementations"] = failed_implementations

                    # Re-create issues for the newly discovered failures
                    newly_failed = [fi for fi in failed_implementations if fi["item"].get("id") in bad_ids]
                    if newly_failed:
                        extra_issues = create_issues_for_failed_implementations(
                            newly_failed, GITHUB_TOKEN, GITHUB_REPOSITORY
                        )
                        run_summary["issues_created"].extend(extra_issues)

                    # Re-run test updater on just the safe changes
                    print("\n  Re-running test updater for safe changes...")
                    safe_changed_files = {}
                    for rec in good_applied:
                        for rel_path in rec.get("files_changed", []):
                            abs_path = Path(APP_ROOT) / rel_path
                            if abs_path.exists():
                                safe_changed_files[rel_path] = abs_path.read_text()
                    try:
                        update_tests(safe_changed_files)
                    except Exception as e:
                        print(f"  [warn] test update after isolation failed: {e}")

                    # One more test run on the surviving changes
                    print("\n  Running final test suite on isolated changes...")
                    test_passed, test_output = _run_tests()
                    last_test_output = test_output
                    summary_line = test_output.split("\n")[-1] if test_output else "no output"

                    if test_passed:
                        print(f"  Tests passed after isolation ({len(bad_applied)} change(s) dropped)")
                        run_summary["test_result"] = (
                            f"PASSED after isolation: {len(bad_applied)} change(s) dropped, "
                            f"{len(good_applied)} applied: {summary_line}"
                        )
                    else:
                        print("  Tests still failing after isolation.")
                        # Fall through to the abort below
                else:
                    print("  No safe changes remain after isolation — aborting.")
                    # All changes were bad; fall through to abort

        if not test_passed:
            run_summary["status"] = "tests_failed"
            run_summary["test_result"] = f"FAILED after {iterations_run} iteration(s)"
            run_summary["errors"] = last_test_output[-2000:]
            update_feedback_run(conn, run_id, {
                "status": "tests_failed",
                "error": last_test_output[-2000:],
            })
            _append_run_log(run_summary)
            print(f"\n[ABORT] Tests failed and could not be resolved. No PR created.")
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
            + "\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
        )
        committed = commit_all(commit_msg)
        if not committed:
            update_feedback_run(conn, run_id, {"status": "no_changes"})
            return

        push_branch(branch_name)

        # ── 13. Open PR ───────────────────────────────────────────────────────
        isolation_note = ""
        dropped = [fi for fi in run_summary["failed_implementations"]
                   if "Isolated as the cause" in fi.get("error", "")]
        if dropped:
            isolation_note = (
                "\n\n### ⚠️ Changes dropped by isolation\n"
                "The following change(s) broke tests and were excluded. "
                "GitHub Issues have been created for manual review:\n"
                + "\n".join(f"- **{d['item']['id']}**: {d['item'].get('title', '')}" for d in dropped)
            )

        pr_body = (
            "## Automated feedback-driven changes\n\n"
            "This PR was generated by the nightly feedback agent pipeline.\n\n"
            "### Changes applied\n"
            + "\n".join(f"- **{c['id']}**: {c['title']}" for c in applied)
            + isolation_note
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
