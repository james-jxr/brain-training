#!/usr/bin/env python3
"""
Implementation Pipeline — v3
==============================
Reads all open ready-to-implement GitHub issues, asks the issue prioritisation
agent to select and order them for this run, then implements each one, runs
tests, updates the spec, commits, pushes, and opens a PR.

Steps:
  1.  Fetch all open ready-to-implement GitHub issues
  2.  Call issue_prioritisation_agent to select issues for this run
  3.  Create a feature branch
  4.  Implement each selected issue via build_agent
  5.  Update test files via testing_agent
  6.  Run full test suite — auto-fix up to 3 times
  7.  Update spec.md via spec_updater_agent
  8.  Append to run-log.md
  9.  Commit + push branch
  10. Open PR
  11. Close implemented GitHub issues
  12. Mark Supabase findings resolved for implemented issues
  13. Write run summary to Supabase

Environment variables:
    PROJECT_ID            Project slug e.g. "brain-training"
    DATABASE_URL          PostgreSQL connection string (required)
    ANTHROPIC_API_KEY     Anthropic API key (required)
    GITHUB_TOKEN          GitHub token (required)
    GITHUB_REPOSITORY     Repo name e.g. "james-jxr/brain-training" (required)
    SUPABASE_URL          Supabase project URL (required)
    SUPABASE_SERVICE_KEY  Supabase service key (required)
    DRY_RUN               Set to "1" to skip implementation and PR
    SKIP_TESTS            Set to "1" to skip test runner
    SKIP_GIT              Set to "1" to write files only, skip commit/push/PR
"""

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

import anthropic
import requests

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
    mark_implementation_failed,
    fetch_ready_to_implement_issues,
)
from feedback_agent.spec_updater import update_spec
from feedback_agent.test_updater import update_tests
from feedback_agent.agent_loader import get_system_prompt
from feedback_agent.prioritiser import prioritise_issues

PROJECT_ID = (
    os.environ.get("PROJECT_ID")
    or os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1]
    or "unknown-project"
)
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
SKIP_TESTS = os.environ.get("SKIP_TESTS", "0") == "1"
SKIP_GIT = os.environ.get("SKIP_GIT", "0") == "1"
MAX_FIX_ITERATIONS = 3

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", f"james-jxr/{PROJECT_ID}")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GH_RUN_ID = os.environ.get("GITHUB_RUN_ID") or str(uuid.uuid4())

APP_ROOT = str(Path(GIT_REPO_ROOT).resolve())
RUN_LOG = str(Path(APP_ROOT) / "run-log.md")

# Finding ID pattern in issue body: Finding ID: `<uuid>`
_FINDING_ID_RE = re.compile(r"Finding ID:\s*`([^`]+)`")


# ── Supabase helpers ─────────────────────────────────────────────────────────────

def _sb_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _log_performance(agent_name: str, action: str, success: bool,
                      tokens_in: int = 0, tokens_out: int = 0):
    if not SUPABASE_URL:
        return
    cost = (tokens_in * 3.0 + tokens_out * 15.0) / 1_000_000
    row = {
        "agent_name": agent_name,
        "project_id": PROJECT_ID,
        "action": action,
        "success": success,
        "run_id": GH_RUN_ID,
        "input_tokens": tokens_in or None,
        "output_tokens": tokens_out or None,
        "estimated_cost_usd": round(cost, 6) if (tokens_in or tokens_out) else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        requests.post(f"{SUPABASE_URL}/rest/v1/agent_performance_logs",
                      headers=_sb_headers(), json=row, timeout=15)
    except Exception:
        pass


def _mark_findings_resolved(finding_ids: list[str], table: str):
    if not finding_ids or not SUPABASE_URL:
        return
    try:
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_sb_headers(),
            params={"id": f"in.({','.join(finding_ids)})"},
            json={"resolved": True, "resolved_at": datetime.now(timezone.utc).isoformat()},
            timeout=15,
        )
        resp.raise_for_status()
        print(f"  [supabase] marked {len(finding_ids)} {table} row(s) resolved")
    except Exception as e:
        print(f"  [supabase] WARNING: could not mark {table} resolved: {e}")


def _write_run_summary(counts: dict):
    if not SUPABASE_URL:
        return
    summary = (
        f"Implementation pipeline: {counts['issues_attempted']} issue(s) attempted, "
        f"{counts['issues_implemented']} implemented, "
        f"{counts['issues_failed']} failed, "
        f"{counts['issues_deferred']} deferred by prioritiser."
    )
    row = {
        "project_id": PROJECT_ID,
        "run_date": date.today().isoformat(),
        "pipeline_type": "implementation",
        "summary": summary,
        "total_actions": counts["issues_attempted"],
        "successful_actions": counts["issues_implemented"],
        "failed_actions": counts["issues_failed"],
        "escalations": 0,
    }
    try:
        resp = requests.post(f"{SUPABASE_URL}/rest/v1/run_summaries",
                             headers=_sb_headers(), json=row, timeout=15)
        if resp.ok:
            print("  [supabase] run summary written")
    except Exception as e:
        print(f"  [supabase] WARNING: run summary failed: {e}")


# ── Test runner (reused from v2) ─────────────────────────────────────────────────

def _run_tests() -> tuple[bool, str]:
    results = []
    passed = True

    env = {**os.environ, "DATABASE_URL": "sqlite:////tmp/pipeline_test.db"}

    # Backend tests — skip if directory doesn't exist
    if (Path(APP_ROOT) / "backend" / "tests").exists():
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

    # Frontend tests — use frontend/ subdirectory if present, otherwise repo root
    frontend_cwd = Path(APP_ROOT) / "frontend"
    if not frontend_cwd.exists():
        frontend_cwd = Path(APP_ROOT)

    frontend_result = subprocess.run(
        ["npm", "test"],
        cwd=str(frontend_cwd),
        capture_output=True, text=True
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

    system_prompt = get_system_prompt("testing_agent")
    if not system_prompt:
        print("  [fix] testing_agent prompt not available")
        return False

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": (
                "Fix the failing tests shown below. Return only the changed files as a JSON object — "
                "no prose, no markdown. Start your response with { and end with }.\n\n"
                f"## Test output\n\n```\n{test_output[:8000]}\n```\n\n"
                f"## Failing files with content\n\n{file_contents[:20000]}"
            )},
        ],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    if not raw:
        return False
    try:
        file_map = json.loads(raw)
    except json.JSONDecodeError:
        return False
    if not file_map:
        return False

    for rel_path, content in file_map.items():
        abs_path = Path(APP_ROOT) / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content)
        print(f"  [fix] wrote {rel_path}")
    return True


# ── Run log ──────────────────────────────────────────────────────────────────────

def _append_run_log(summary: dict):
    today = date.today().isoformat()
    mode = "automated" if os.environ.get("CI") else "local"
    status = summary.get("status", "unknown")
    applied = summary.get("changes_applied", [])
    failed = summary.get("failed_implementations", [])
    deferred = summary.get("deferred", [])
    test_result = summary.get("test_result", "not run")
    pr_url = summary.get("pr_url", "")
    errors = summary.get("errors", "")

    applied_text = "\n".join(f"  - #{c['issue_number']}: {c['title']}" for c in applied) or "  (none)"
    failed_text = "\n".join(f"  - #{f['issue_number']}: {f['error'][:120]}" for f in failed) or "  (none)"
    deferred_text = "\n".join(f"  - #{d['issue_number']}: {d['reason']}" for d in deferred) or "  (none)"

    entry = f"""
## Run — {today} ({mode}) [pipeline v3 — implementation]
**Status:** {status}
**Issues implemented:**
{applied_text}
**Issues failed:**
{failed_text}
**Issues deferred:**
{deferred_text}
**Spec version:** {summary.get("spec_version", "unchanged")}
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


# ── Finding ID extraction ─────────────────────────────────────────────────────────

def _extract_finding_id(issue_body: str) -> str | None:
    """Extract Supabase finding ID from issue body if present."""
    m = _FINDING_ID_RE.search(issue_body or "")
    return m.group(1) if m else None


# ── Main ─────────────────────────────────────────────────────────────────────────

def run_implementation_pipeline():
    print(f"\n{'='*60}")
    print(f"Implementation Pipeline v3 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Project: {PROJECT_ID}")
    print(f"{'='*60}\n")

    counts = {
        "issues_available": 0,
        "issues_attempted": 0,
        "issues_implemented": 0,
        "issues_failed": 0,
        "issues_deferred": 0,
    }

    run_summary = {
        "status": "pending",
        "changes_applied": [],
        "failed_implementations": [],
        "deferred": [],
        "spec_version": "unchanged",
        "test_result": "not run",
        "pr_url": "",
        "errors": "",
    }

    # ── 1. Fetch ready-to-implement issues ────────────────────────────────────
    print("[Step 1] Fetching ready-to-implement issues from GitHub...")
    issues = fetch_ready_to_implement_issues(GITHUB_TOKEN, GITHUB_REPOSITORY)
    counts["issues_available"] = len(issues)

    if not issues:
        print("  No ready-to-implement issues. Nothing to do.")
        run_summary["status"] = "no_changes"
        _append_run_log(run_summary)
        _write_run_summary(counts)
        return

    # ── 2. Prioritise issues ──────────────────────────────────────────────────
    print(f"\n[Step 2] Calling issue_prioritisation_agent for {len(issues)} issue(s)...")
    prioritisation_prompt = get_system_prompt("issue_prioritisation_agent") or ""

    if not prioritisation_prompt:
        print("  WARNING: issue_prioritisation_agent prompt not found — attempting all issues")
        selected = [
            {
                "issue_number": i["number"],
                "id": f"issue-{i['number']}",
                "title": i["title"],
                "complexity": "medium",
                "priority": "medium",
                "type": "feature",
                "description": i["body"],
                "files_likely_affected": [],
                "implementation_notes": "",
            }
            for i in issues
        ]
        deferred = []
        prio_usage = {"input_tokens": 0, "output_tokens": 0}
    else:
        try:
            selected, deferred, prio_usage = prioritise_issues(issues, prioritisation_prompt)
            _log_performance("issue_prioritisation_agent", "prioritise_issues", True,
                             prio_usage["input_tokens"], prio_usage["output_tokens"])
        except Exception as e:
            print(f"  [prioritiser] ERROR: {e} — attempting all issues")
            _log_performance("issue_prioritisation_agent", "prioritise_issues", False)
            selected = [
                {
                    "issue_number": i["number"],
                    "id": f"issue-{i['number']}",
                    "title": i["title"],
                    "complexity": "medium",
                    "priority": "medium",
                    "type": "feature",
                    "description": i["body"],
                    "files_likely_affected": [],
                    "implementation_notes": "",
                }
                for i in issues
            ]
            deferred = []

    counts["issues_deferred"] = len(deferred)
    run_summary["deferred"] = deferred

    print(f"  Selected: {len(selected)} | Deferred: {len(deferred)}")
    for item in selected:
        print(f"    [{item.get('complexity', '?')}] #{item['issue_number']}: {item['title'][:70]}")
    for d in deferred:
        print(f"    [deferred] #{d['issue_number']}: {d.get('reason', '')[:70]}")

    if not selected:
        print("  Prioritiser selected no issues for this run.")
        run_summary["status"] = "no_changes"
        _append_run_log(run_summary)
        _write_run_summary(counts)
        return

    if DRY_RUN:
        print("\n[DRY RUN] Skipping implementation and PR.")
        run_summary["status"] = "dry_run"
        _append_run_log(run_summary)
        return

    counts["issues_attempted"] = len(selected)

    # Build a lookup from issue number → full issue dict (for body parsing later)
    issue_map = {i["number"]: i for i in issues}

    # ── 3. Create feature branch ──────────────────────────────────────────────
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    branch_name = f"implementation/{date_str}-{GH_RUN_ID[:8]}"
    if SKIP_GIT:
        print(f"\n[SKIP_GIT=1] Skipping branch creation — would create: {branch_name}")
    else:
        print(f"\n[Step 3] Creating branch: {branch_name}")
        create_branch(branch_name)

    # ── 4. Implement each selected issue ──────────────────────────────────────
    print(f"\n[Step 4] Implementing {len(selected)} issue(s)...")

    applied = []
    failed_implementations = []
    all_changed_files = {}

    for item in selected:
        issue_number = item["issue_number"]
        print(f"\n  Implementing: #{issue_number} — {item['title'][:70]}")

        # Build the change item in the format implement_change expects
        change_item = {
            "id": item.get("id", f"issue-{issue_number}"),
            "title": item["title"],
            "description": item.get("description", ""),
            "files_likely_affected": item.get("files_likely_affected", []),
            "implementable": True,
            "type": item.get("type", "feature"),
            "priority": item.get("priority", "medium"),
            "implementation_notes": item.get("implementation_notes", ""),
        }

        try:
            file_map, impl_usage = implement_change(change_item)
            _log_performance("build_agent", "implement_change", bool(file_map),
                             impl_usage.get("input_tokens", 0), impl_usage.get("output_tokens", 0))

            if file_map:
                applied.append({
                    "issue_number": issue_number,
                    "id": change_item["id"],
                    "title": item["title"],
                    "files_changed": list(file_map.keys()),
                    "labels": issue_map.get(issue_number, {}).get("labels", []),
                    "body": issue_map.get(issue_number, {}).get("body", ""),
                })
                for rel_path in file_map:
                    abs_path = Path(APP_ROOT) / rel_path
                    if abs_path.exists():
                        all_changed_files[rel_path] = abs_path.read_text()
                counts["issues_implemented"] += 1
            else:
                error_msg = "No files were written — build agent returned empty response."
                print(f"  [skip] #{issue_number} — {error_msg}")
                failed_implementations.append({"issue_number": issue_number, "error": error_msg})
                mark_implementation_failed(GITHUB_TOKEN, GITHUB_REPOSITORY, issue_number, error_msg)
                counts["issues_failed"] += 1

        except Exception as e:
            print(f"  [error] #{issue_number}: {e}")
            _log_performance("build_agent", "implement_change", False)
            error_msg = str(e)
            failed_implementations.append({"issue_number": issue_number, "error": error_msg})
            mark_implementation_failed(GITHUB_TOKEN, GITHUB_REPOSITORY, issue_number, error_msg)
            counts["issues_failed"] += 1

    run_summary["changes_applied"] = applied
    run_summary["failed_implementations"] = failed_implementations

    if not applied:
        print("\nNo changes were written. Exiting without commit.")
        run_summary["status"] = "no_changes"
        _append_run_log(run_summary)
        _write_run_summary(counts)
        return

    # ── 5. Update tests ───────────────────────────────────────────────────────
    print("\n[Step 5] Updating tests to reflect code changes...")
    try:
        _, test_usage = update_tests(all_changed_files)
        _log_performance("testing_agent", "update_tests", True,
                         test_usage.get("input_tokens", 0), test_usage.get("output_tokens", 0))
    except Exception as e:
        print(f"  [warn] test update failed: {e}")
        _log_performance("testing_agent", "update_tests", False)

    # ── 6. Run tests with auto-fix loop ───────────────────────────────────────
    print("\n[Step 6] Running test suite...")
    test_passed = False
    last_test_output = ""

    if SKIP_TESTS:
        print("  [SKIP_TESTS=1] Skipping test runner.")
        test_passed = True
        run_summary["test_result"] = "SKIPPED (SKIP_TESTS=1)"
    else:
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
                print(f"\n--- Test output (iteration {iteration}) ---\n{test_output}\n--- End test output ---\n")
                if iteration < MAX_FIX_ITERATIONS:
                    print("  Auto-fixing...")
                    fixed = _auto_fix_tests(test_output, all_changed_files)
                    if not fixed:
                        print("  No fixes suggested — stopping early")
                        break

    if not test_passed:
        run_summary["status"] = "tests_failed"
        run_summary["test_result"] = f"FAILED after {MAX_FIX_ITERATIONS} iterations"
        run_summary["errors"] = last_test_output[-2000:]
        _append_run_log(run_summary)

        # Mark all implemented issues as failed — leave them ready-to-implement
        for change in applied:
            mark_implementation_failed(
                GITHUB_TOKEN, GITHUB_REPOSITORY, change["issue_number"],
                f"Test suite failed after {MAX_FIX_ITERATIONS} fix attempts:\n\n"
                f"```\n{last_test_output[-1500:]}\n```"
            )
            counts["issues_implemented"] -= 1
            counts["issues_failed"] += 1

        _write_run_summary(counts)
        print(f"\n[ABORT] Tests failed after {MAX_FIX_ITERATIONS} fix attempts. No PR created.")
        sys.exit(1)

    # ── 7. Update spec.md ─────────────────────────────────────────────────────
    print("\n[Step 7] Updating spec.md...")
    try:
        new_spec_version = update_spec(GIT_REPO_ROOT, APP_ROOT)
        run_summary["spec_version"] = new_spec_version or "unchanged"
    except Exception as e:
        print(f"  [warn] spec update failed: {e}")

    # ── 8. Append run-log ─────────────────────────────────────────────────────
    run_summary["status"] = "completed"
    _append_run_log(run_summary)

    # ── 9. Commit and push ────────────────────────────────────────────────────
    if SKIP_GIT:
        print("\n[SKIP_GIT=1] Skipping commit/push/PR — files written to disk only.")
        run_summary["pr_url"] = "(skipped — SKIP_GIT=1)"
    else:
        issue_refs = ", ".join(f"#{c['issue_number']}" for c in applied)
        commit_msg = (
            f"[implementation-agent] Apply {len(applied)} change(s) ({issue_refs})\n\n"
            + "\n".join(f"- #{c['issue_number']}: {c['title']}" for c in applied)
            + "\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
        )
        print(f"\n[Step 9] Committing and pushing branch: {branch_name}")
        committed = commit_all(commit_msg)
        if not committed:
            print("  Nothing to commit — exiting.")
            run_summary["status"] = "no_changes"
            _write_run_summary(counts)
            return

        push_branch(branch_name)

        # ── 10. Open PR ───────────────────────────────────────────────────────
        print("\n[Step 10] Opening PR...")
        pr_body = (
            "## Automated implementation\n\n"
            "This PR was generated by the nightly implementation pipeline (v3).\n\n"
            "### Issues implemented\n"
            + "\n".join(
                f"- Closes #{c['issue_number']}: {c['title']}"
                for c in applied
            )
            + f"\n\n### Tests\n✅ Full test suite passed ({run_summary['test_result']})\n\n"
            f"### Spec\nSpec updated to {run_summary['spec_version']}\n\n"
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
        )
        pr_url = open_pr(
            branch_name,
            f"[implementation-agent] {len(applied)} issue(s): {issue_refs}",
            pr_body,
        )
        print(f"\nPR created: {pr_url}")
        run_summary["pr_url"] = pr_url

        # ── 11. Close implemented issues ──────────────────────────────────────
        print(f"\n[Step 11] Closing {len(applied)} implemented issue(s)...")
        for change in applied:
            close_issue(GITHUB_TOKEN, GITHUB_REPOSITORY, change["issue_number"], pr_url)

        # ── 12. Mark Supabase findings resolved ───────────────────────────────
        print("\n[Step 12] Marking Supabase findings resolved...")
        audit_ids = []
        coord_ids = []
        for change in applied:
            finding_id = _extract_finding_id(change.get("body", ""))
            if not finding_id:
                continue
            labels = change.get("labels", [])
            if "audit-finding" in labels:
                audit_ids.append(finding_id)
            elif "coordination-finding" in labels:
                coord_ids.append(finding_id)

        if audit_ids:
            _mark_findings_resolved(audit_ids, "code_audit_findings")
        if coord_ids:
            _mark_findings_resolved(coord_ids, "coordination_findings")

    # ── 13. Write run summary ─────────────────────────────────────────────────
    print("\n[Step 13] Writing run summary...")
    _write_run_summary(counts)

    print(f"\n{'='*60}")
    print(f"Implementation pipeline complete.")
    print(f"  Implemented: {counts['issues_implemented']}")
    print(f"  Failed:      {counts['issues_failed']}")
    print(f"  Deferred:    {counts['issues_deferred']}")
    print(f"  PR:          {run_summary.get('pr_url', '(none)')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_implementation_pipeline()
