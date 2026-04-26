#!/usr/bin/env python3
"""
Feedback Agent Pipeline — v2
=============================
Extends v1 with a unified aggregation stage that pulls from three sources:
  - code_audit_findings   (Supabase) — audit agent findings
  - coordination_findings (Supabase) — coordination agent findings
  - feedback_entries      (PostgreSQL) — user feedback

Audit and coordination items bypass the Claude synthesis call (already structured).
User feedback is synthesised by Claude as before.

Steps:
  1.  Aggregate all issue sources (audit + coordination + feedback)
  2.  Check GitHub for resolved design items (ready-to-implement label)
  3.  Synthesise: audit/coord items converted directly; feedback → Claude
  4.  Create GitHub Issues for non-implementable items (idempotent)
  5.  Design agent reviews all open needs-decision issues against spec
  6.  Filter items to those that are autonomously implementable
  7.  Create a feature branch
  8.  Implement each change (write source files to disk)
  9.  Update test files to stay in sync with code changes
  10. Run full test suite — auto-fix failures up to 3 times
  11. Update spec.md
  12. Append to run-log.md
  13. Commit everything + push branch
  14. Open PR
  15. Close resolved GitHub issues that were implemented
  16. Mark feedback processed + audit/coordination findings resolved
  17. Write run summary to Supabase

Environment variables:
    PROJECT_ID            Project slug e.g. "brain-training" (default: brain-training)
    DATABASE_URL          PostgreSQL connection string (required)
    ANTHROPIC_API_KEY     Anthropic API key (required)
    GITHUB_TOKEN          GitHub token for issue creation + PR (required in CI)
    GITHUB_REPOSITORY     Repo name e.g. "james-jxr/brain-training" (required in CI)
    SUPABASE_URL          Supabase project URL (required for audit/coordination aggregation)
    SUPABASE_SERVICE_KEY  Supabase service key (required for audit/coordination aggregation)
    DRY_RUN               Set to "1" to synthesise only, skip implementation + PR
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
    apply_design_decision,
    close_issue,
    create_issues_for_failed_implementations,
    create_issues_for_non_implementable,
    fetch_needs_decision_issues,
    fetch_resolved_design_items,
    post_design_review_comment,
)
from feedback_agent.design_reviewer import run_design_review, _parse_files_from_issue_body
from feedback_agent.spec_updater import update_spec
from feedback_agent.test_updater import update_tests
from feedback_agent.aggregator import aggregate

PROJECT_ID = os.environ.get("PROJECT_ID", "brain-training")
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
SKIP_TESTS = os.environ.get("SKIP_TESTS", "0") == "1"
SKIP_GIT = os.environ.get("SKIP_GIT", "0") == "1"
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
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", f"james-jxr/{PROJECT_ID}")
GH_RUN_ID = os.environ.get("GITHUB_RUN_ID") or str(uuid.uuid4())

PROMPTS_DIR = Path(__file__).parent / "prompts"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


# ── Supabase logging ───────────────────────────────────────────────────────────

_supabase_client = None


def _get_supabase():
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        print(f"  [supabase] could not connect: {e}")
        return None


def _log_to_supabase(action: str, success: bool, duration_ms: int = 0,
                     tokens_in: int = 0, tokens_out: int = 0, error: str = "") -> dict | None:
    sb = _get_supabase()
    if not sb:
        return None
    row = {
        "project_id": PROJECT_ID,
        "run_id": GH_RUN_ID,
        "agent_name": action.split(".")[0] if "." in action else "pipeline",
        "action": action,
        "success": success,
        "duration_ms": duration_ms,
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "output_summary": error[:500] if error else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = sb.table("agent_performance_logs").insert(row).execute()
        return result.data[0] if result.data else row
    except Exception as e:
        print(f"  [supabase] log write failed: {e}")
        return None


def _mark_findings_resolved(supabase_id_list: list[str], table: str):
    """Mark a list of Supabase finding rows as resolved."""
    if not supabase_id_list or not SUPABASE_URL or not SUPABASE_KEY:
        return
    import requests
    try:
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            params={"id": f"in.({','.join(supabase_id_list)})"},
            json={"resolved": True, "resolved_at": datetime.now(timezone.utc).isoformat()},
            timeout=15,
        )
        resp.raise_for_status()
        print(f"  [supabase] marked {len(supabase_id_list)} {table} row(s) resolved")
    except Exception as e:
        print(f"  [supabase] WARNING: could not mark {table} resolved: {e}")


def _stamp_last_attempted(supabase_id_list: list[str], table: str):
    """Set last_attempted_at=now() on findings we attempted but didn't resolve."""
    if not supabase_id_list or not SUPABASE_URL or not SUPABASE_KEY:
        return
    import requests
    try:
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            params={"id": f"in.({','.join(supabase_id_list)})"},
            json={"last_attempted_at": datetime.now(timezone.utc).isoformat()},
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"  [supabase] WARNING: could not stamp last_attempted_at on {table}: {e}")


# ── Test runner ────────────────────────────────────────────────────────────────

def _run_tests() -> tuple[bool, str]:
    results = []
    passed = True

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

    frontend_result = subprocess.run(
        ["npm", "test"],
        cwd=str(Path(APP_ROOT) / "frontend"),
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

    from feedback_agent.agent_loader import get_system_prompt
    system_prompt = get_system_prompt("testing_agent")

    client = anthropic.Anthropic()
    if system_prompt:
        user_message = (
            "Fix the failing tests shown below. Return only the changed files as JSON.\n\n"
            f"## Test output\n\n```\n{test_output[:8000]}\n```\n\n"
            f"## Failing files with content\n\n{file_contents[:20000]}"
        )
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
    else:
        prompt = ((PROMPTS_DIR / "test_fix.md").read_text()
                  .replace("{test_output}", test_output[:8000])
                  .replace("{failing_files_with_content}", file_contents[:20000]))
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


# ── Run log ────────────────────────────────────────────────────────────────────

def _append_run_log(summary: dict):
    today = date.today().isoformat()
    mode = "automated" if os.environ.get("CI") else "local"
    status = summary.get("status", "unknown")
    feedback_count = summary.get("feedback_count", 0)
    audit_count = summary.get("audit_count", 0)
    coord_count = summary.get("coordination_count", 0)
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
## Run — {today} ({mode}) [pipeline v2]
**Status:** {status}
**Sources:** {feedback_count} feedback, {audit_count} audit findings, {coord_count} coordination findings
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


# ── Run summariser ─────────────────────────────────────────────────────────────

def _call_run_summarizer(log_entries: list) -> str | None:
    if not log_entries:
        return None
    from feedback_agent.agent_loader import get_system_prompt
    system_prompt = get_system_prompt("run_summarizer_agent")
    if not system_prompt:
        return None
    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": json.dumps(log_entries, default=str)}]
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        print(f"  [summarizer] failed: {e}")
        return None


def _write_run_summary(summary_data: dict):
    sb = _get_supabase()
    if not sb or not summary_data:
        return
    try:
        row = {
            "project_id": PROJECT_ID,
            "run_date": summary_data.get("run_date", date.today().isoformat()),
            "summary": summary_data.get("summary", ""),
            "total_actions": summary_data.get("total_actions", 0),
            "successful_actions": summary_data.get("successful_actions", 0),
            "failed_actions": summary_data.get("failed_actions", 0),
            "escalations": summary_data.get("escalations", 0),
        }
        sb.table("run_summaries").insert(row).execute()
        print(f"  [supabase] run summary written for {row['run_date']}")
    except Exception as e:
        print(f"  [supabase] run summary write failed: {e}")


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline():
    print(f"\n{'='*60}")
    print(f"Feedback Agent Pipeline v2 — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Project: {PROJECT_ID}")
    print(f"{'='*60}\n")

    conn = get_conn()
    run_id = insert_feedback_run(conn, {"status": "pending", "pipeline_version": "v2"})
    print(f"Run ID: {run_id} | GH Run: {GH_RUN_ID}")

    _supabase_log_entries: list[dict] = []

    run_summary = {
        "status": "pending",
        "feedback_count": 0,
        "audit_count": 0,
        "coordination_count": 0,
        "changes_applied": [],
        "failed_implementations": [],
        "issues_created": [],
        "spec_version": "unchanged",
        "test_result": "not run",
        "pr_url": "",
        "errors": "",
    }

    # Track which Supabase findings we successfully implemented (for mark-resolved)
    implemented_audit_ids: list[str] = []
    implemented_coord_ids: list[str] = []
    # Track all attempted finding IDs (for stamping last_attempted_at on failures)
    attempted_audit_ids: list[str] = []
    attempted_coord_ids: list[str] = []

    try:
        # ── 1. Aggregate all issue sources ─────────────────────────────────────
        print("[Step 1] Aggregating issue sources...")
        aggregation = aggregate(PROJECT_ID, SUPABASE_URL, SUPABASE_KEY, conn)

        feedback = aggregation.feedback_rows
        pre_structured = [i for i in aggregation.items if i.source in ("audit", "coordination")]

        run_summary["feedback_count"] = len(feedback)
        run_summary["audit_count"] = len(aggregation.audit_ids)
        run_summary["coordination_count"] = len(aggregation.coordination_ids)

        # Track all IDs we're about to attempt
        attempted_audit_ids = list(aggregation.audit_ids)
        attempted_coord_ids = list(aggregation.coordination_ids)

        if not feedback and not pre_structured:
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
        print("\n[Step 3] Synthesising...")
        items, synth_usage = synthesise(
            feedback,
            resolved_items=resolved_items,
            pre_structured_items=pre_structured,
        )
        log_entry = _log_to_supabase(
            "feedback_synthesis_agent.synthesise", success=True,
            tokens_in=synth_usage.get("input_tokens", 0),
            tokens_out=synth_usage.get("output_tokens", 0),
        )
        if log_entry:
            _supabase_log_entries.append(log_entry)
        print(f"Change items identified: {len(items)}")
        for item in items:
            flag = "✓" if item.get("implementable") else "–"
            source_tag = f"[{item.get('source', 'feedback')}]"
            print(f"  [{flag}] [{item['priority'].upper()}] {source_tag} {item['id']}: {item['title']}")

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

        # ── 5. Design agent review of needs-decision issues ───────────────────
        print("\n[Step 5] Running design agent review of needs-decision issues...")
        spec_path = Path(APP_ROOT) / "spec.md"
        spec_content = spec_path.read_text() if spec_path.exists() else ""
        needs_decision_issues = fetch_needs_decision_issues(GITHUB_TOKEN, GITHUB_REPOSITORY)

        if needs_decision_issues:
            print(f"  Found {len(needs_decision_issues)} open needs-decision issue(s)")
            agent_resolved, agent_unresolved, review_usage = run_design_review(
                needs_decision_issues, spec_content
            )
            log_entry = _log_to_supabase(
                "interaction_design_agent.design_review", success=True,
                tokens_in=review_usage.get("input_tokens", 0),
                tokens_out=review_usage.get("output_tokens", 0),
            )
            if log_entry:
                _supabase_log_entries.append(log_entry)

            for r in agent_resolved:
                apply_design_decision(GITHUB_TOKEN, GITHUB_REPOSITORY, r["issue_number"], r["decision"])
            for u in agent_unresolved:
                post_design_review_comment(GITHUB_TOKEN, GITHUB_REPOSITORY, u["issue_number"], u["comment"])

            existing_ids = {item.get("id") for item in items}
            for r in agent_resolved:
                item_id = r["title"].split("]")[0].lstrip("[") if "]" in r["title"] else ""
                if item_id in existing_ids:
                    for item in items:
                        if item.get("id") == item_id:
                            item["implementable"] = True
                            item["description"] = r["decision"]
                            break
                else:
                    items.append({
                        "id": item_id or f"design-review-{r['issue_number']}",
                        "title": r["title"].split("] ", 1)[-1] if "] " in r["title"] else r["title"],
                        "implementable": True,
                        "type": "design",
                        "priority": "medium",
                        "description": r["decision"],
                        "files_likely_affected": _parse_files_from_issue_body(r.get("body", "")),
                        "source": "design_review",
                    })
                    print(f"  [design-review] added pre-existing resolved item: {item_id}")

            print(f"  Design review complete: {len(agent_resolved)} resolved, {len(agent_unresolved)} still needs human input")
        else:
            print("  No open needs-decision issues to review")

        # ── 6. Filter to implementable items ──────────────────────────────────
        to_implement = [i for i in items if i.get("implementable")]
        print(f"\n{len(to_implement)} item(s) queued for implementation")

        if not to_implement:
            print("No implementable items this run.")
            mark_feedback_processed(conn, [r["id"] for r in feedback])
            # Stamp last_attempted_at so we don't retry these immediately
            _stamp_last_attempted(attempted_audit_ids, "code_audit_findings")
            _stamp_last_attempted(attempted_coord_ids, "coordination_findings")
            update_feedback_run(conn, run_id, {"status": "no_changes"})
            run_summary["status"] = "no_changes"
            _append_run_log(run_summary)
            return

        # ── 7. Create branch ──────────────────────────────────────────────────
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        branch_name = f"feedback/{date_str}-run-{run_id}"
        if SKIP_GIT:
            print(f"[SKIP_GIT=1] Skipping branch creation — would create: {branch_name}")
        else:
            create_branch(branch_name)
            print(f"Branch: {branch_name}")

        # ── 8. Implement each change ──────────────────────────────────────────
        applied = []
        failed_implementations = []
        all_changed_files = {}

        for item in to_implement:
            print(f"\n  Implementing: {item['id']} ({item.get('source', 'feedback')})")
            try:
                file_map, impl_usage = implement_change(item)
                log_entry = _log_to_supabase(
                    "build_agent.implement_change", success=bool(file_map),
                    tokens_in=impl_usage.get("input_tokens", 0),
                    tokens_out=impl_usage.get("output_tokens", 0),
                )
                if log_entry:
                    _supabase_log_entries.append(log_entry)
                if file_map:
                    applied.append({
                        "id": item["id"],
                        "title": item["title"],
                        "files_changed": list(file_map.keys()),
                        "source": item.get("source", "feedback"),
                        "supabase_id": item.get("supabase_id"),
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
                _log_to_supabase("build_agent.implement_change", success=False, error=str(e))
                failed_implementations.append({"item": item, "error": str(e)})

        if failed_implementations:
            print(f"\n  Creating issues for {len(failed_implementations)} failed implementation(s)...")
            failed_issues = create_issues_for_failed_implementations(
                failed_implementations, GITHUB_TOKEN, GITHUB_REPOSITORY
            )
            run_summary["issues_created"].extend(failed_issues)

        if not applied:
            print("\nNo changes were written. Exiting without commit.")
            # Stamp last_attempted_at on findings we tried but couldn't implement
            _stamp_last_attempted(attempted_audit_ids, "code_audit_findings")
            _stamp_last_attempted(attempted_coord_ids, "coordination_findings")
            update_feedback_run(conn, run_id, {"status": "no_changes"})
            run_summary["status"] = "no_changes"
            _append_run_log(run_summary)
            try:
                summary_data = _call_run_summarizer(_supabase_log_entries)
                if summary_data:
                    _write_run_summary(summary_data)
            except Exception as e:
                print(f"  [warn] run summary failed: {e}")
            return

        run_summary["changes_applied"] = applied
        run_summary["failed_implementations"] = failed_implementations

        # ── 9. Update tests ───────────────────────────────────────────────────
        print("\n[Step 9] Updating tests to reflect code changes...")
        try:
            _, test_usage = update_tests(all_changed_files)
            log_entry = _log_to_supabase(
                "testing_agent.update_tests", success=True,
                tokens_in=test_usage.get("input_tokens", 0),
                tokens_out=test_usage.get("output_tokens", 0),
            )
            if log_entry:
                _supabase_log_entries.append(log_entry)
        except Exception as e:
            print(f"  [warn] test update failed: {e}")
            _log_to_supabase("testing_agent.update_tests", success=False, error=str(e))

        # ── 10. Run tests with auto-fix loop ──────────────────────────────────
        print("\n[Step 10] Running test suite...")
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
            update_feedback_run(conn, run_id, {
                "status": "tests_failed",
                "error": last_test_output[-2000:],
            })
            _append_run_log(run_summary)
            print(f"\n[ABORT] Tests failed after {MAX_FIX_ITERATIONS} fix attempts. No PR created.")
            sys.exit(1)

        # ── 11. Update spec.md ────────────────────────────────────────────────
        print("\n[Step 11] Updating spec.md...")
        try:
            new_spec_version = update_spec(GIT_REPO_ACTUAL_ROOT, APP_ROOT)
            run_summary["spec_version"] = new_spec_version or "unchanged"
        except Exception as e:
            print(f"  [warn] spec update failed: {e}")

        # ── 12. Append run-log ────────────────────────────────────────────────
        run_summary["status"] = "completed"
        _append_run_log(run_summary)

        # ── 13. Commit and push ───────────────────────────────────────────────
        if SKIP_GIT:
            print("[SKIP_GIT=1] Skipping commit/push/PR — files written to disk only.")
            run_summary["pr_url"] = "(skipped — SKIP_GIT=1)"
        else:
            source_summary = []
            if run_summary["audit_count"]:
                source_summary.append(f"{run_summary['audit_count']} audit finding(s)")
            if run_summary["coordination_count"]:
                source_summary.append(f"{run_summary['coordination_count']} coordination finding(s)")
            if run_summary["feedback_count"]:
                source_summary.append(f"{run_summary['feedback_count']} feedback item(s)")
            source_str = ", ".join(source_summary) or "mixed sources"

            commit_msg = (
                f"[feedback-agent] Apply {len(applied)} change(s) from {source_str}\n\n"
                + "\n".join(f"- {c['title']}" for c in applied)
                + "\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
            )
            committed = commit_all(commit_msg)
            if not committed:
                update_feedback_run(conn, run_id, {"status": "no_changes"})
                return

            push_branch(branch_name)

            # ── 14. Open PR ───────────────────────────────────────────────────
            pr_body = (
                "## Automated changes\n\n"
                "This PR was generated by the nightly feedback agent pipeline (v2).\n\n"
                f"**Sources:** {source_str}\n\n"
                "### Changes applied\n"
                + "\n".join(
                    f"- **{c['id']}** [{c.get('source', 'feedback')}]: {c['title']}"
                    for c in applied
                )
                + "\n\n### Tests\n"
                f"✅ Full test suite passed ({run_summary['test_result']})\n\n"
                "### Spec\n"
                f"Spec updated to {run_summary['spec_version']}\n\n"
                "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
            )
            pr_url = open_pr(
                branch_name,
                f"[feedback-agent] {len(applied)} change(s) from {source_str}",
                pr_body,
            )
            print(f"\nPR created: {pr_url}")
            run_summary["pr_url"] = pr_url

        # ── 15. Close resolved GitHub issues that were implemented ────────────
        if not SKIP_GIT:
            implemented_ids = {c["id"] for c in applied}
            for resolved in resolved_items:
                if resolved["id"] in implemented_ids:
                    close_issue(GITHUB_TOKEN, GITHUB_REPOSITORY, resolved["issue_number"], run_summary["pr_url"])

        # ── 16. Mark sources as processed / resolved ──────────────────────────
        # Feedback entries
        mark_feedback_processed(conn, [r["id"] for r in feedback])

        # Audit and coordination findings that were successfully implemented
        for change in applied:
            sid = change.get("supabase_id")
            if not sid:
                continue
            source = change.get("source", "")
            if source == "audit":
                implemented_audit_ids.append(sid)
            elif source == "coordination":
                implemented_coord_ids.append(sid)

        if implemented_audit_ids:
            _mark_findings_resolved(implemented_audit_ids, "code_audit_findings")
        if implemented_coord_ids:
            _mark_findings_resolved(implemented_coord_ids, "coordination_findings")

        # Stamp last_attempted_at on findings we tried but didn't successfully resolve
        failed_audit_ids = [i for i in attempted_audit_ids if i not in implemented_audit_ids]
        failed_coord_ids = [i for i in attempted_coord_ids if i not in implemented_coord_ids]
        if failed_audit_ids:
            _stamp_last_attempted(failed_audit_ids, "code_audit_findings")
        if failed_coord_ids:
            _stamp_last_attempted(failed_coord_ids, "coordination_findings")

        update_feedback_run(conn, run_id, {
            "status": "completed",
            "changes_applied": applied,
            "branch_name": branch_name,
            "pr_url": run_summary.get("pr_url", ""),
            "pipeline_version": "v2",
        })

        # ── 17. Summarise run ─────────────────────────────────────────────────
        print("\n[Step 17] Generating run summary...")
        try:
            summary_data = _call_run_summarizer(_supabase_log_entries)
            if summary_data:
                _write_run_summary(summary_data)
        except Exception as e:
            print(f"  [warn] run summary failed: {e}")

        print(f"\n{'='*60}")
        print(f"Pipeline complete. {len(applied)} change(s) → {run_summary.get('pr_url', '(no PR)')}")
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
