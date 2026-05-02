#!/usr/bin/env python3
"""
Feedback Agent Review Pipeline — v3
=====================================
Reads all issue sources (audit findings, coordination findings, user feedback),
classifies each one, and creates/updates GitHub issues accordingly. Does not
write any code.

Steps:
  1.  Fetch unresolved code_audit_findings + coordination_findings from Supabase
  2.  Call audit_findings_agent to classify each finding
  3.  Create/update GitHub issues for findings; store issue numbers back to Supabase
  4.  Fetch unprocessed user feedback from PostgreSQL
  5.  Fetch project spec and file tree
  6.  Call feedback_synthesis_agent + feedback_agent to synthesise and route feedback
  7.  Create/update GitHub issues for feedback items
  8.  Fetch open needs-design-review issues; call design agents to resolve or escalate
  9.  Mark feedback as processed
  10. Write run summary to Supabase

Environment variables:
    PROJECT_ID            Project slug e.g. "brain-training"
    DATABASE_URL          PostgreSQL connection string (required)
    ANTHROPIC_API_KEY     Anthropic API key (required)
    GITHUB_TOKEN          GitHub token (required)
    GITHUB_REPOSITORY     Repo name e.g. "james-jxr/brain-training" (required)
    SUPABASE_URL          Supabase project URL (required)
    SUPABASE_SERVICE_KEY  Supabase service key (required)
"""

import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

import requests

from feedback_agent.db import fetch_unprocessed_feedback, get_conn, mark_feedback_processed
from feedback_agent.audit_classifier import classify_audit_findings
from feedback_agent.agent_loader import get_system_prompt
from feedback_agent.synthesizer import synthesise_feedback, build_file_tree
from feedback_agent.github_issues import (
    ensure_labels,
    create_finding_issue,
    create_feedback_issue,
    store_issue_number,
    update_issue_labels,
    post_comment,
    LABEL_READY,
    LABEL_DESIGN,
    LABEL_HUMAN,
)
from feedback_agent.design_reviewer import run_design_reviews

PROJECT_ID = (
    os.environ.get("PROJECT_ID")
    or os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1]
    or "unknown-project"
)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", f"james-jxr/{PROJECT_ID}")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GH_RUN_ID = os.environ.get("GITHUB_RUN_ID") or str(uuid.uuid4())

APP_ROOT = str(Path(__file__).parent.parent.resolve())

SPEC_CANDIDATES = ["docs/functional-spec.md", "spec.md", "docs/spec.md"]
DESIGN_CANDIDATES = ["docs/design-guide.md", "design-guide.md", "docs/design.md"]


# ── Supabase helpers ─────────────────────────────────────────────────────────────────

def _sb_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }


def _fetch_findings(table: str) -> list[dict]:
    if not SUPABASE_URL:
        return []
    # code_audit_findings has file_path; coordination_findings has artifact_a/artifact_b instead
    if table == "code_audit_findings":
        # auto_fixable and route_to live on coordination_findings only
        select_cols = ("id,finding_type,severity,description,file_path,"
                       "last_attempted_at,github_issue_number")
    else:
        select_cols = ("id,finding_type,severity,description,last_attempted_at,"
                       "github_issue_number,artifact_a,artifact_b,auto_fixable,route_to")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=_sb_headers(),
        params={
            "project_id": f"eq.{PROJECT_ID}",
            "resolved": "eq.false",
            "select": select_cols,
            "order": "created_at.asc",
        },
        timeout=15,
    )
    if not resp.ok:
        print(f"  [supabase] WARNING: could not fetch {table}: {resp.text[:200]}")
        return []
    rows = resp.json()
    # Skip findings that already have a GitHub issue
    new = [r for r in rows if not r.get("github_issue_number")]
    print(f"  [supabase] {table}: {len(rows)} unresolved, {len(new)} without issue")
    return new


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
    requests.post(f"{SUPABASE_URL}/rest/v1/agent_performance_logs",
                  headers=_sb_headers(), json=row, timeout=15)


def _write_run_summary(counts: dict):
    if not SUPABASE_URL:
        return
    summary = (
        f"Review pipeline: {counts['audit_classified']} audit findings, "
        f"{counts['coord_classified']} coordination findings, "
        f"{counts['feedback_items']} feedback items \u2192 "
        f"{counts['issues_created']} issue(s) created/updated, "
        f"{counts['design_resolved']} design question(s) resolved."
    )
    row = {
        "project_id": PROJECT_ID,
        "run_date": date.today().isoformat(),
        "pipeline_type": "review",
        "summary": summary,
        "total_actions": counts["issues_created"],
        "successful_actions": counts["design_resolved"],
        "failed_actions": 0,
        "escalations": counts.get("design_escalated", 0),
    }
    try:
        resp = requests.post(f"{SUPABASE_URL}/rest/v1/run_summaries",
                             headers=_sb_headers(), json=row, timeout=15)
        if resp.ok:
            print(f"  [supabase] run summary written")
    except Exception as e:
        print(f"  [supabase] WARNING: run summary failed: {e}")


# ── Spec / design file helpers ───────────────────────────────────────────────────────

def _read_local(candidates: list[str]) -> str:
    for path in candidates:
        abs_path = Path(APP_ROOT) / path
        if abs_path.exists():
            return abs_path.read_text()
    return ""


# ── Fetch needs-design-review issues ───────────────────────────────────────────────

def _fetch_design_review_issues() -> list[dict]:
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        return []
    from github import Github, GithubException
    try:
        repo = Github(GITHUB_TOKEN).get_repo(GITHUB_REPOSITORY)
        issues = []
        for issue in repo.get_issues(state="open", labels=[LABEL_DESIGN]):
            comments = [c.body for c in issue.get_comments()]
            issues.append({
                "issue_number": issue.number,
                "title": issue.title,
                "body": issue.body or "",
                "labels": [l.name for l in issue.labels],
                "comments": comments,
            })
        print(f"  [issues] {len(issues)} needs-design-review issue(s)")
        return issues
    except Exception as e:
        print(f"  [issues] WARNING: could not fetch design-review issues: {e}")
        return []


# ── Main ──────────────────────────────────────────────────────────────────────────────

def run_review_pipeline():
    print(f"\n{'='*60}")
    print(f"Review Pipeline v3 \u2014 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Project: {PROJECT_ID}")
    print(f"{'='*60}\n")

    counts = {
        "audit_classified": 0,
        "coord_classified": 0,
        "feedback_items": 0,
        "issues_created": 0,
        "design_resolved": 0,
        "design_escalated": 0,
    }

    ensure_labels(GITHUB_TOKEN, GITHUB_REPOSITORY)

    # ── Step 1: Fetch unresolved findings from Supabase ────────────────────────────
    print("[Step 1] Fetching audit and coordination findings...")
    audit_findings = _fetch_findings("code_audit_findings")
    coord_findings = _fetch_findings("coordination_findings")

    # ── Step 2: Classify all findings (audit + coord together) ───────────────────────
    print("[Step 2] Classifying audit and coordination findings...")
    audit_prompt = get_system_prompt("audit_findings_agent") or ""
    if audit_findings or coord_findings:
        classifications, audit_usage = classify_audit_findings(
            audit_findings, coord_findings, audit_prompt
        )
        counts["audit_classified"] = sum(
            1 for c in classifications if c["table"] == "code_audit_findings"
        )
        counts["coord_classified"] = sum(
            1 for c in classifications if c["table"] == "coordination_findings"
        )
        _log_performance("audit_findings_agent", "classify_findings", True,
                         audit_usage.get("input_tokens", 0), audit_usage.get("output_tokens", 0))
    else:
        classifications = []
        print("  No new findings to classify.")

    # ── Step 3: Create/update GitHub issues for findings ──────────────────────────
    print("[Step 3] Creating/updating GitHub issues for findings...")
    audit_map = {f["id"]: f for f in audit_findings}
    coord_map = {f["id"]: f for f in coord_findings}
    for cls in classifications:
        fid = cls["finding_id"]
        table = cls["table"]
        finding = (audit_map if table == "code_audit_findings" else coord_map).get(fid)
        if not finding:
            print(f"  [issues] WARNING: no finding found for id {fid}")
            continue
        issue_num = create_finding_issue(
            GITHUB_TOKEN, GITHUB_REPOSITORY,
            finding, table,
            cls["routing"], cls["rationale"], cls.get("design_agent"),
        )
        if issue_num:
            store_issue_number(SUPABASE_URL, SUPABASE_KEY, table, fid, issue_num)
            counts["issues_created"] += 1

    # ── Step 4: Fetch unprocessed user feedback ─────────────────────────────────────
    print("[Step 4] Fetching unprocessed user feedback...")
    conn = get_conn()
    feedback_rows = fetch_unprocessed_feedback(conn, PROJECT_ID)
    counts["feedback_items"] = len(feedback_rows)
    print(f"  {len(feedback_rows)} unprocessed feedback item(s)")

    # ── Step 5: Fetch project spec, file tree, and agent prompts ───────────────────
    print("[Step 5] Fetching project spec and file tree...")
    spec_text = _read_local(SPEC_CANDIDATES)
    design_text = _read_local(DESIGN_CANDIDATES)
    file_tree = build_file_tree(APP_ROOT)
    synthesis_prompt = get_system_prompt("feedback_synthesis_agent") or ""
    routing_prompt = get_system_prompt("feedback_agent") or ""
    functional_design_prompt = get_system_prompt("functional_design_agent") or ""
    interaction_design_prompt = get_system_prompt("interaction_design_agent") or ""

    # ── Step 6: Synthesise and route feedback ───────────────────────────────────────
    print("[Step 6] Synthesising and routing feedback...")
    processed_ids = []
    if feedback_rows:
        items, synth_usage = synthesise_feedback(
            feedback_rows, spec_text, file_tree, synthesis_prompt, routing_prompt
        )
        _log_performance("feedback_synthesis_agent", "synthesise_feedback", True,
                         synth_usage.get("input_tokens", 0), synth_usage.get("output_tokens", 0))
        # ── Step 7: Create/update GitHub issues for feedback ───────────────────────
        print("[Step 7] Creating/updating GitHub issues for feedback...")
        for item in items:
            issue_num = create_feedback_issue(GITHUB_TOKEN, GITHUB_REPOSITORY, item)
            if issue_num:
                counts["issues_created"] += 1
            processed_ids.extend(item.get("feedback_ids", []))
    else:
        print("  No feedback to synthesise.")

    # ── Step 8: Design review ────────────────────────────────────────────────────────
    print("[Step 8] Running design reviews...")
    design_issues = _fetch_design_review_issues()
    if design_issues:
        resolved, unresolved, design_usage = run_design_reviews(
            design_issues, spec_text, design_text,
            functional_design_prompt, interaction_design_prompt,
        )
        counts["design_resolved"] = len(resolved)
        counts["design_escalated"] = len(unresolved)
        _log_performance("functional_design_agent", "design_review", True,
                         design_usage.get("input_tokens", 0), design_usage.get("output_tokens", 0))
        for r in resolved:
            comment = f"**Design decision:** {r['decision']}"
            if r.get("guide_extension"):
                comment += f"\n\n**Guide extension:**\n{r['guide_extension']}"
            post_comment(GITHUB_TOKEN, GITHUB_REPOSITORY, r["issue_number"], comment)
            update_issue_labels(GITHUB_TOKEN, GITHUB_REPOSITORY, r["issue_number"],
                                add=[LABEL_READY], remove=[LABEL_DESIGN])
        for u in unresolved:
            post_comment(
                GITHUB_TOKEN, GITHUB_REPOSITORY, u["issue_number"],
                f"**Still unresolved \u2014 needs human input:**\n\n{u['remaining_questions']}",
            )
            update_issue_labels(GITHUB_TOKEN, GITHUB_REPOSITORY, u["issue_number"],
                                add=[LABEL_HUMAN], remove=[LABEL_DESIGN])
    else:
        print("  No needs-design-review issues found.")

    # ── Step 9: Mark feedback as processed ─────────────────────────────────────────
    print("[Step 9] Marking feedback as processed...")
    if processed_ids:
        mark_feedback_processed(conn, processed_ids)
        print(f"  Marked {len(processed_ids)} feedback item(s) as processed.")
    conn.close()

    # ── Step 10: Write run summary ───────────────────────────────────────────────────
    print("[Step 10] Writing run summary...")
    _write_run_summary(counts)

    print(f"\n{'='*60}")
    print("Review Pipeline complete.")
    print(f"  Audit findings classified : {counts['audit_classified']}")
    print(f"  Coord findings classified : {counts['coord_classified']}")
    print(f"  Feedback items processed  : {counts['feedback_items']}")
    print(f"  GitHub issues created     : {counts['issues_created']}")
    print(f"  Design questions resolved : {counts['design_resolved']}")
    print(f"  Design questions escalated: {counts['design_escalated']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_review_pipeline()
