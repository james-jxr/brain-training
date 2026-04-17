# GitHub Issues integration: create issues for non-implementable items,
# fetch resolved items (ready-to-implement label), close issues after implementation.
import os
from github import Github, GithubException


def _get_repo(token: str, repo_name: str):
    g = Github(token)
    return g.get_repo(repo_name)


def _issue_title(item: dict) -> str:
    return f"[{item['id']}] {item['title']}"


def _build_issue_body(item: dict) -> str:
    files = "\n".join(f"- `{f}`" for f in item.get("files_likely_affected", []))
    return f"""## Feedback-Driven Design Item

**Type:** {item.get('type', 'unknown')}
**Priority:** {item.get('priority', 'unknown')}

### Description
{item.get('description', '')}

### Files Likely Affected
{files or '(unknown)'}

### Why This Needs Human Input
This item was flagged as requiring a design decision before implementation.
The feedback agent cannot implement it autonomously.

---
*Created by the nightly feedback pipeline.*

**To resolve:**
1. Add a comment with your decision
2. Apply the label `ready-to-implement`

The next pipeline run will detect this label, read your decision, and implement the change automatically.
"""


def create_issues_for_non_implementable(items: list, token: str, repo_name: str) -> list:
    """
    Create GitHub Issues for non-implementable items. Idempotent — skips items
    that already have an open issue with the same title prefix.
    Returns list of {id, issue_url} dicts for newly created issues.
    """
    if not token or not repo_name:
        print("  [issues] GITHUB_TOKEN or GITHUB_REPOSITORY not set, skipping issue creation")
        return []

    repo = _get_repo(token, repo_name)
    created = []

    # Build set of existing open issue titles for fast lookup
    existing_titles = set()
    try:
        for issue in repo.get_issues(state="open", labels=["feedback-agent"]):
            existing_titles.add(issue.title)
    except GithubException as e:
        print(f"  [issues] warning: could not fetch existing issues: {e}")

    for item in items:
        if item.get("implementable"):
            continue

        title = _issue_title(item)
        if title in existing_titles:
            print(f"  [issues] already exists: {title}")
            continue

        labels = ["feedback-agent", item.get("type", "design"), item.get("priority", "medium")]
        # Only use labels that exist in the repo — GitHub raises if label missing
        try:
            issue = repo.create_issue(
                title=title,
                body=_build_issue_body(item),
                labels=labels,
            )
            print(f"  [issues] created: {issue.html_url}")
            created.append({"id": item["id"], "issue_url": issue.html_url, "issue_number": issue.number})
        except GithubException as e:
            # Retry without labels if they don't exist yet
            try:
                issue = repo.create_issue(title=title, body=_build_issue_body(item))
                print(f"  [issues] created (no labels): {issue.html_url}")
                created.append({"id": item["id"], "issue_url": issue.html_url, "issue_number": issue.number})
            except GithubException as e2:
                print(f"  [issues] error creating issue for {item['id']}: {e2}")

    return created


def fetch_resolved_design_items(token: str, repo_name: str) -> list:
    """
    Fetch open issues labelled feedback-agent + ready-to-implement.
    Returns list of {id, title, decision, issue_number} dicts.
    """
    if not token or not repo_name:
        return []

    repo = _get_repo(token, repo_name)
    resolved = []

    try:
        issues = repo.get_issues(state="open", labels=["feedback-agent", "ready-to-implement"])
        for issue in issues:
            # Parse item ID from title: "[stroop-button-colour] Fix Stroop..."
            item_id = issue.title.split("]")[0].lstrip("[") if "]" in issue.title else issue.title

            # Get decision from most recent comment
            comments = list(issue.get_comments())
            decision = comments[-1].body if comments else ""

            resolved.append({
                "id": item_id,
                "title": issue.title,
                "decision": decision,
                "issue_number": issue.number,
            })
            print(f"  [issues] resolved item: {item_id}")
    except GithubException as e:
        print(f"  [issues] warning: could not fetch resolved issues: {e}")

    return resolved


def create_issues_for_failed_implementations(items: list, token: str, repo_name: str) -> list:
    """
    Create GitHub Issues for implementable items that failed or were skipped during
    the implementation stage. Idempotent — skips items that already have an open issue.
    Returns list of {id, issue_url} dicts for newly created issues.
    """
    if not token or not repo_name:
        print("  [issues] GITHUB_TOKEN or GITHUB_REPOSITORY not set, skipping failed-impl issue creation")
        return []

    repo = _get_repo(token, repo_name)
    created = []

    existing_titles = set()
    try:
        for issue in repo.get_issues(state="open", labels=["feedback-agent"]):
            existing_titles.add(issue.title)
    except GithubException as e:
        print(f"  [issues] warning: could not fetch existing issues: {e}")

    for entry in items:
        item = entry["item"]
        error = entry.get("error", "No files were written — Claude may have returned an empty or unparseable response.")
        title = f"[{item['id']}] Implementation failed: {item['title']}"

        if title in existing_titles:
            print(f"  [issues] already exists: {title}")
            continue

        files = "\n".join(f"- `{f}`" for f in item.get("files_likely_affected", []))
        body = f"""## Implementation Attempt Failed

The feedback pipeline identified this as implementable and attempted it automatically, but the implementation was skipped or produced an error.

**Type:** {item.get('type', 'unknown')}
**Priority:** {item.get('priority', 'unknown')}

### What was attempted
{item.get('description', '')}

### Files targeted
{files or '(none specified)'}

### Error
```
{error}
```

### What to do
Please add a comment with any additional context or clarification that would help the pipeline implement this correctly (e.g. which specific files to target, what the expected behaviour should be, or a more precise description of the change).

Then apply the label `ready-to-implement` and the next pipeline run will retry it.

---
*Created automatically by the nightly feedback pipeline.*
"""
        labels = ["feedback-agent", item.get("type", "design"), item.get("priority", "medium")]
        try:
            issue = repo.create_issue(title=title, body=body, labels=labels)
            print(f"  [issues] created (failed impl): {issue.html_url}")
            created.append({"id": item["id"], "issue_url": issue.html_url})
        except GithubException:
            try:
                issue = repo.create_issue(title=title, body=body)
                print(f"  [issues] created (failed impl, no labels): {issue.html_url}")
                created.append({"id": item["id"], "issue_url": issue.html_url})
            except GithubException as e2:
                print(f"  [issues] error creating failed-impl issue for {item['id']}: {e2}")

    return created


def close_issue(token: str, repo_name: str, issue_number: int, pr_url: str = ""):
    """Close a GitHub issue after the item has been implemented."""
    if not token or not repo_name:
        return
    try:
        repo = _get_repo(token, repo_name)
        issue = repo.get_issue(issue_number)
        comment = f"Implemented autonomously by the feedback pipeline."
        if pr_url:
            comment += f" See PR: {pr_url}"
        issue.create_comment(comment)
        issue.edit(state="closed")
        print(f"  [issues] closed #{issue_number}")
    except GithubException as e:
        print(f"  [issues] warning: could not close issue #{issue_number}: {e}")
