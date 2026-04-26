# GitHub Issues integration for v3 pipelines.
#
# Key changes from v2:
#   - New label set: ready-to-implement, needs-human-review, needs-design-review,
#     audit-finding, coordination-finding, user-feedback, failed-implementation
#   - upsert_issue: create-or-update (deduplication by title prefix)
#   - update_issue_labels: relabel an existing issue
#   - store_issue_number: write github_issue_number back to Supabase finding row
#   - fetch_ready_to_implement_issues: for implementation pipeline
#   - close_issue, post_comment: shared with v2

import os
import requests as _requests
from datetime import datetime, timezone
from github import Github, GithubException

# ── Label constants ─────────────────────────────────────────────────────────────

LABEL_READY       = "ready-to-implement"
LABEL_HUMAN       = "needs-human-review"
LABEL_DESIGN      = "needs-design-review"
LABEL_AUDIT       = "audit-finding"
LABEL_COORD       = "coordination-finding"
LABEL_FEEDBACK    = "user-feedback"
LABEL_FAILED_IMPL = "failed-implementation"
LABEL_PIPELINE    = "pipeline-failure"

ALL_V3_LABELS = [
    (LABEL_READY,    "0075ca", "Clear, unambiguous — ready for the build agent"),
    (LABEL_HUMAN,    "e4e669", "Needs a product owner decision before work can begin"),
    (LABEL_DESIGN,   "d93f0b", "Being reviewed by functional or interaction design agent"),
    (LABEL_AUDIT,    "1d76db", "Raised by the nightly code audit"),
    (LABEL_COORD,    "5319e7", "Raised by the nightly coordination audit"),
    (LABEL_FEEDBACK, "0e8a16", "Raised from user feedback"),
    (LABEL_FAILED_IMPL, "b60205", "Build agent attempted and failed — will retry"),
    (LABEL_PIPELINE, "ee0701", "A pipeline or workflow run failed"),
]

_PIPELINE_CLOSE_MARKER = "Implemented autonomously by the v3 pipeline"


# ── GitHub client helpers ───────────────────────────────────────────────────────

def _get_repo(token: str, repo_name: str):
    return Github(token).get_repo(repo_name)


def ensure_labels(token: str, repo_name: str):
    """Create all v3 labels in the repo if they don't already exist."""
    if not token or not repo_name:
        return
    try:
        repo = _get_repo(token, repo_name)
        existing = {l.name for l in repo.get_labels()}
        for name, color, desc in ALL_V3_LABELS:
            if name not in existing:
                try:
                    repo.create_label(name=name, color=color, description=desc)
                    print(f"  [labels] created: {name}")
                except GithubException:
                    pass
    except GithubException as e:
        print(f"  [labels] WARNING: could not ensure labels: {e}")


# ── Issue deduplication ─────────────────────────────────────────────────────────

def _find_open_issue(repo, title_prefix: str):
    """Return the first open issue whose title starts with title_prefix, or None."""
    try:
        for issue in repo.get_issues(state="open"):
            if issue.title.startswith(title_prefix):
                return issue
    except GithubException:
        pass
    return None


def upsert_issue(
    token: str,
    repo_name: str,
    title: str,
    body: str,
    labels: list[str],
    title_prefix: str | None = None,
) -> int | None:
    """
    Create a new issue or update labels on the existing one if a match is found.
    title_prefix is used for matching; defaults to the full title.
    Returns the issue number, or None on failure.
    """
    if not token or not repo_name:
        return None
    prefix = title_prefix or title
    try:
        repo = _get_repo(token, repo_name)
        existing = _find_open_issue(repo, prefix)
        if existing:
            # Update labels to reflect current routing (e.g. re-classified after design review)
            current_labels = {l.name for l in existing.labels}
            routing_labels = {LABEL_READY, LABEL_HUMAN, LABEL_DESIGN}
            # Only update if routing changed
            new_routing = set(labels) & routing_labels
            old_routing = current_labels & routing_labels
            if new_routing and new_routing != old_routing:
                for lbl in old_routing - new_routing:
                    try:
                        existing.remove_from_labels(lbl)
                    except GithubException:
                        pass
                for lbl in new_routing - old_routing:
                    try:
                        existing.add_to_labels(lbl)
                    except GithubException:
                        pass
                print(f"  [issues] updated labels on #{existing.number}: {new_routing}")
            else:
                print(f"  [issues] already exists: #{existing.number} — {existing.title[:60]}")
            return existing.number

        issue = repo.create_issue(title=title, body=body, labels=labels)
        print(f"  [issues] created #{issue.number}: {issue.html_url}")
        return issue.number
    except GithubException as e:
        # Retry without labels
        try:
            repo = _get_repo(token, repo_name)
            issue = repo.create_issue(title=title, body=body)
            print(f"  [issues] created #{issue.number} (no labels): {issue.html_url}")
            return issue.number
        except GithubException as e2:
            print(f"  [issues] ERROR creating issue '{title[:60]}': {e2}")
            return None


def update_issue_labels(token: str, repo_name: str, issue_number: int,
                         add: list[str], remove: list[str]):
    """Add and remove labels on an existing issue."""
    if not token or not repo_name:
        return
    try:
        repo = _get_repo(token, repo_name)
        issue = repo.get_issue(issue_number)
        for lbl in remove:
            try:
                issue.remove_from_labels(lbl)
            except GithubException:
                pass
        for lbl in add:
            try:
                issue.add_to_labels(lbl)
            except GithubException:
                pass
    except GithubException as e:
        print(f"  [issues] WARNING: could not update labels on #{issue_number}: {e}")


def post_comment(token: str, repo_name: str, issue_number: int, comment: str):
    """Post a comment on an issue."""
    if not token or not repo_name:
        return
    try:
        repo = _get_repo(token, repo_name)
        repo.get_issue(issue_number).create_comment(comment)
        print(f"  [issues] commented on #{issue_number}")
    except GithubException as e:
        print(f"  [issues] WARNING: could not comment on #{issue_number}: {e}")


# ── Supabase: store github_issue_number back to finding row ────────────────────

def store_issue_number(
    supabase_url: str,
    supabase_key: str,
    table: str,
    finding_id: str,
    issue_number: int,
):
    """Persist github_issue_number on a code_audit_findings or coordination_findings row."""
    if not supabase_url or not supabase_key or not issue_number:
        return
    try:
        resp = _requests.patch(
            f"{supabase_url}/rest/v1/{table}",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            params={"id": f"eq.{finding_id}"},
            json={"github_issue_number": issue_number},
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as e:
        print(f"  [issues] WARNING: could not store issue number for {finding_id}: {e}")


# ── Issue body builders ─────────────────────────────────────────────────────────

def _finding_issue_body(finding: dict, table: str, routing: str, rationale: str) -> str:
    source_label = "Code Audit" if table == "code_audit_findings" else "Coordination Audit"
    files = f"`{finding.get('file_path', '')}`" if finding.get("file_path") else "(unknown)"
    routing_note = {
        "ready_to_implement": "This finding has been classified as **ready to implement** — no design decisions needed.",
        "needs_design_review": "This finding requires a **design review** before implementation. The design agent will comment with a resolution.",
        "needs_human_review": "This finding requires **human review** — it involves a decision the agents cannot make autonomously.",
    }.get(routing, "")
    return f"""## {source_label} Finding

**Severity:** {finding.get('severity', 'unknown')}
**Type:** {finding.get('finding_type', 'unknown')}
**File:** {files}

### Description
{finding.get('description', '')}

### Classification
{routing_note}

**Rationale:** {rationale}

---
*Raised by the Agent Central nightly health audit. Finding ID: `{finding.get('id', '')}`*
"""


def _feedback_issue_body(item: dict) -> str:
    files = "\n".join(f"- `{f}`" for f in item.get("files_likely_affected", []))
    routing_note = {
        "build": "Classified as **ready to implement** — the required change is clear.",
        "functional_design": "Requires **functional design review** — raises a question about what the app should do.",
        "interaction_design": "Requires **interaction design review** — raises a question about how the app looks or feels.",
        "skip": "Marked as **skip** — out of scope or not actionable.",
    }.get(item.get("routing", ""), "")
    return f"""## User Feedback Item

**Type:** {item.get('type', 'unknown')}
**Priority:** {item.get('priority', 'unknown')}
**Feedback count:** {item.get('feedback_count', 1)}

### Description
{item.get('description', '')}

### Files likely affected
{files or '(unknown)'}

### Classification
{routing_note}

---
*Raised by the nightly feedback review pipeline.*

**To resolve manually:** Add a comment with your decision, then apply the label `ready-to-implement`.
"""


# ── Review pipeline helpers ─────────────────────────────────────────────────────

def create_finding_issue(
    token: str,
    repo_name: str,
    finding: dict,
    table: str,
    routing: str,
    rationale: str,
    design_agent: str | None,
) -> int | None:
    """Create or update a GitHub issue for a single audit/coordination finding."""
    finding_id_short = finding["id"][:8]
    source = "audit" if table == "code_audit_findings" else "coord"
    title_prefix = f"[{source}-{finding_id_short}]"
    title = f"{title_prefix} {finding.get('finding_type', 'finding')}: {finding.get('description', '')[:80]}"

    routing_to_label = {
        "ready_to_implement": LABEL_READY,
        "needs_design_review": LABEL_DESIGN,
        "needs_human_review": LABEL_HUMAN,
    }
    source_label = LABEL_AUDIT if table == "code_audit_findings" else LABEL_COORD
    labels = [routing_to_label.get(routing, LABEL_HUMAN), source_label]

    body = _finding_issue_body(finding, table, routing, rationale)
    if design_agent:
        body += f"\n**Design agent assigned:** `{design_agent}`\n"

    return upsert_issue(token, repo_name, title, body, labels, title_prefix=title_prefix)


def create_feedback_issue(
    token: str,
    repo_name: str,
    item: dict,
) -> int | None:
    """Create or update a GitHub issue for a synthesized feedback item."""
    title_prefix = f"[feedback-{item['id']}]"
    title = f"{title_prefix} {item['title']}"

    routing = item.get("routing", "")
    if routing == "build" and item.get("implementable"):
        status_label = LABEL_READY
    elif routing in ("functional_design", "interaction_design"):
        status_label = LABEL_DESIGN
    else:
        status_label = LABEL_HUMAN

    labels = [status_label, LABEL_FEEDBACK]
    body = _feedback_issue_body(item)
    return upsert_issue(token, repo_name, title, body, labels, title_prefix=title_prefix)


# ── Implementation pipeline helpers ────────────────────────────────────────────

def fetch_ready_to_implement_issues(token: str, repo_name: str) -> list[dict]:
    """
    Return all open issues labelled ready-to-implement.
    Each dict includes: number, title, body, labels (list of names), created_at,
    comments (list of comment bodies), failed_impl_count.
    """
    if not token or not repo_name:
        return []
    try:
        repo = _get_repo(token, repo_name)
        issues = []
        for issue in repo.get_issues(state="open", labels=[LABEL_READY]):
            label_names = [l.name for l in issue.labels]
            # Never let the implementation pipeline attempt pipeline-failure notifications
            if LABEL_PIPELINE in label_names:
                print(f"  [issues] skipping #{issue.number} — has {LABEL_PIPELINE} label")
                continue
            comments = [c.body for c in issue.get_comments()]
            failed_count = label_names.count(LABEL_FAILED_IMPL)
            issues.append({
                "number": issue.number,
                "title": issue.title,
                "body": issue.body or "",
                "labels": label_names,
                "created_at": issue.created_at.isoformat(),
                "comments": comments,
                "failed_impl_count": failed_count,
            })
        print(f"  [issues] {len(issues)} ready-to-implement issue(s)")
        return issues
    except GithubException as e:
        print(f"  [issues] WARNING: could not fetch ready-to-implement issues: {e}")
        return []


def close_issue(token: str, repo_name: str, issue_number: int, pr_url: str = ""):
    """Close an issue after successful implementation."""
    if not token or not repo_name:
        return
    try:
        repo = _get_repo(token, repo_name)
        issue = repo.get_issue(issue_number)
        comment = _PIPELINE_CLOSE_MARKER
        if pr_url:
            comment += f" PR: {pr_url}"
        issue.create_comment(comment)
        issue.edit(state="closed")
        print(f"  [issues] closed #{issue_number}")
    except GithubException as e:
        print(f"  [issues] WARNING: could not close #{issue_number}: {e}")


def mark_implementation_failed(token: str, repo_name: str, issue_number: int, error: str):
    """Add failed-implementation label and post an error comment. Issue stays ready-to-implement."""
    if not token or not repo_name:
        return
    try:
        repo = _get_repo(token, repo_name)
        issue = repo.get_issue(issue_number)
        try:
            issue.add_to_labels(LABEL_FAILED_IMPL)
        except GithubException:
            pass
        issue.create_comment(
            f"**Implementation attempt failed:**\n\n```\n{error[:1500]}\n```\n\n"
            "_The issue remains `ready-to-implement`. The nightly audit will detect "
            "any pipeline failure and raise a separate issue. The next implementation "
            "run will retry this._"
        )
        print(f"  [issues] marked #{issue_number} as failed-implementation")
    except GithubException as e:
        print(f"  [issues] WARNING: could not mark #{issue_number} failed: {e}")
