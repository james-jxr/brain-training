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


# ── Supabase helpers ───────────────────────────────────────────────────────────────────────────────

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


# ── Spec / design file helpers ────────────────────────────────────────────────────────────────────

def _read_local(candidates: list[str]) -> str:
    for path in candidates:
        abs_path = Path(APP_ROOT) / path
        if abs_path.exists():
            return abs_path.read_text()
    return ""


# ── Fetch needs-design-review issues ──────────────────────────────────────────────────────────────

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


# ── Main ────────────────────────────────────────────────────────────────────────────────────

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

    # ── Step 1: Ensure GitHub labels exist ────────────────────────────────────
    ensure_labels(GITHUB_TOKEN, GITHUB_REPOSITORY)

    # ── Step 2: Fetch audit + coordination findings ───────────────────────────
    print("[1/8] Fetching audit findings...")
    audit_findings = _fetch_findings("code_audit_findings")
    coord_findings = _fetch_findings("coordination_findings")

    # ── Step 3: Classify findings ─────────────────────────────────────────────
    print("[2/8] Classifying findings...")
    classifications = []
    if audit_findings or coord_findings:
        audit_system_prompt = get_system_prompt("audit_findings_agent", PROJECT_ID)
        if audit_system_prompt:
            classifications, audit_usage = classify_audit_findings(
                audit_findings, coord_findings, audit_system_prompt
            )
            counts["audit_classified"] = len(
                [c for c in classifications if c.get("table") == "code_audit_findings"]
            )
            counts["coord_classified"] = len(
                [c for c in classifications if c.get("table") == "coordination_findings"]
            )
            _log_performance(
                "audit_findings_agent", "classify_findings", True,
                audit_usage.get("input_tokens", 0), audit_usage.get("output_tokens", 0)
            )
        else:
            print("  [audit] WARNING: no system prompt available, skipping classification")

    # ── Step 4: Create/update GitHub issues for findings ──────────────────────
    print("[3/8] Creating GitHub issues for findings...")
    findings_by_id = {f["id"]: f for f in audit_findings + coord_findings}
    for classification in classifications:
        finding_id = classification.get("finding_id")
        table = classification.get("table")
        routing = classification.get("routing", "needs_human_review")
        finding = findings_by_id.get(finding_id)
        if not finding:
            continue
        label_map = {
            "ready_to_implement": LABEL_READY,
            "needs_design_review": LABEL_DESIGN,
            "needs_human_review": LABEL_HUMAN,
        }
        routing_label = label_map.get(routing, LABEL_HUMAN)
        issue_number = create_finding_issue(
            token=GITHUB_TOKEN,
            repo_name=GITHUB_REPOSITORY,
            finding=finding,
            table=table,
            routing_label=routing_label,
            design_agent=classification.get("design_agent"),
            rationale=classification.get("rationale", ""),
        )
        if issue_number:
            store_issue_number(
                supabase_url=SUPABASE_URL,
                supabase_key=SUPABASE_KEY,
                table=table,
                finding_id=finding_id,
                issue_number=issue_number,
            )
            counts["issues_created"] += 1

    # ── Step 5: Fetch unprocessed user feedback ───────────────────────────────
    print("[4/8] Fetching user feedback...")
    feedback_rows = []
    try:
        with get_conn() as conn:
            feedback_rows = fetch_unprocessed_feedback(conn, PROJECT_ID)
        print(f"  [feedback] {len(feedback_rows)} unprocessed row(s)")
    except Exception as e:
        print(f"  [feedback] WARNING: could not fetch feedback: {e}")

    counts["feedback_items"] = len(feedback_rows)

    # ── Step 6: Fetch spec + file tree ────────────────────────────────────────
    print("[5/8] Loading spec and file tree...")
    spec_content = _read_local(SPEC_CANDIDATES)
    design_content = _read_local(DESIGN_CANDIDATES)
    file_tree = build_file_tree(APP_ROOT)

    # ── Step 7: Synthesise + route feedback ───────────────────────────────────
    print("[6/8] Synthesising feedback...")
    routed_items = []
    if feedback_rows:
        synthesis_prompt = get_system_prompt("feedback_synthesis_agent", PROJECT_ID)
        routing_prompt = get_system_prompt("feedback_agent", PROJECT_ID)
        if synthesis_prompt and routing_prompt:
            routed_items, synth_usage = synthesise_feedback(
                feedback_rows=feedback_rows,
                spec_content=spec_content,
                file_tree=file_tree,
                synthesis_prompt=synthesis_prompt,
                routing_prompt=routing_prompt,
            )
            _log_performance(
                "feedback_synthesis_agent", "synthesise_feedback", True,
                synth_usage.get("input_tokens", 0), synth_usage.get("output_tokens", 0)
            )
        else:
            print("  [feedback] WARNING: missing synthesis or routing prompt, skipping")

    # ── Step 8: Create GitHub issues for feedback items ───────────────────────
    print("[7/8] Creating GitHub issues for feedback...")
    for item in routed_items:
        routing = item.get("routing", "needs_human_review")
        label_map = {
            "ready_to_implement": LABEL_READY,
            "needs_design_review": LABEL_DESIGN,
            "needs_human_review": LABEL_HUMAN,
        }
        routing_label = label_map.get(routing, LABEL_HUMAN)
        issue_number = create_feedback_issue(
            token=GITHUB_TOKEN,
            repo_name=GITHUB_REPOSITORY,
            item=item,
            routing_label=routing_label,
        )
        if issue_number:
            counts["issues_created"] += 1

    # ── Step 9: Mark feedback as processed ───────────────────────────────────
    if feedback_rows and routed_items:
        try:
            with get_conn() as conn:
                processed_ids = [r["id"] for r in feedback_rows]
                mark_feedback_processed(conn, processed_ids)
                print(f"  [feedback] marked {len(processed_ids)} row(s) as processed")
        except Exception as e:
            print(f"  [feedback] WARNING: could not mark feedback processed: {e}")

    # ── Step 10: Design reviews ───────────────────────────────────────────────
    print("[8/8] Running design reviews...")
    design_issues = _fetch_design_review_issues()
    if design_issues:
        functional_prompt = get_system_prompt("functional_design_agent", PROJECT_ID)
        interaction_prompt = get_system_prompt("interaction_design_agent", PROJECT_ID)
        design_results = run_design_reviews(
            issues=design_issues,
            spec_content=spec_content,
            design_content=design_content,
            functional_design_prompt=functional_prompt or "",
            interaction_design_prompt=interaction_prompt or "",
        )
        for result in design_results:
            issue_number = result["issue_number"]
            if result.get("can_resolve"):
                update_issue_labels(
                    token=GITHUB_TOKEN,
                    repo_name=GITHUB_REPOSITORY,
                    issue_number=issue_number,
                    add_labels=[LABEL_READY],
                    remove_labels=[LABEL_DESIGN],
                )
                post_comment(
                    token=GITHUB_TOKEN,
                    repo_name=GITHUB_REPOSITORY,
                    issue_number=issue_number,
                    body=f"**Design resolved:** {result.get('decision', '')}\n\n"
                         f"This issue is now ready to implement.",
                )
                counts["design_resolved"] += 1
            else:
                post_comment(
                    token=GITHUB_TOKEN,
                    repo_name=GITHUB_REPOSITORY,
                    issue_number=issue_number,
                    body=f"**Design review — further input needed:**\n\n"
                         f"{result.get('remaining_questions', '')}",
                )
                counts["design_escalated"] += 1
            _log_performance(
                "design_reviewer", f"review_issue_{issue_number}",
                result.get("can_resolve", False),
                result.get("usage", {}).get("input_tokens", 0),
                result.get("usage", {}).get("output_tokens", 0),
            )

    # ── Summary ───────────────────────────────────────────────────────────────
    _write_run_summary(counts)
    print(f"\n{'='*60}")
    print(f"Review pipeline complete.")
    print(f"  Audit findings classified : {counts['audit_classified']}")
    print(f"  Coord findings classified : {counts['coord_classified']}")
    print(f"  Feedback items processed  : {counts['feedback_items']}")
    print(f"  GitHub issues created     : {counts['issues_created']}")
    print(f"  Design questions resolved : {counts['design_resolved']}")
    print(f"  Design questions escalated: {counts['design_escalated']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_review_pipeline()
