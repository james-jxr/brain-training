# Design agent: auto-reviews GitHub Issues with needs-decision label using project spec.
import json
from pathlib import Path

import anthropic
from github import Github, GithubException
from feedback_agent.agent_loader import get_system_prompt

REPO_ROOT = Path(__file__).parent.parent
SPEC_PATH = REPO_ROOT / "spec.md"

# Built-in system prompt used when Supabase is unavailable
_BUILTIN_SYSTEM_PROMPT = """You are the Design Review Agent. You review GitHub Issues that were flagged as needing a design decision, and determine whether you can resolve them using the project's existing specification.

Read the issue carefully. Look at the design questions listed in it. Cross-reference each question against the project specification.

- If the spec provides enough information to make a confident, specific decision for ALL questions: set can_resolve to true and write a clear, actionable decision comment.
- If ANY question requires a judgement call not covered by the spec: set can_resolve to false.

Rules:
- Do not invent design directions not grounded in the spec.
- Output ONLY valid JSON. No prose before or after.

Output format:
{"can_resolve": true, "decision": "...", "remaining_questions": ""}
or:
{"can_resolve": false, "decision": "", "remaining_questions": "..."}"""


def _load_spec() -> str:
    return SPEC_PATH.read_text() if SPEC_PATH.exists() else "(spec.md not found)"


def _call_design_claude(issue_title: str, issue_body: str, spec: str) -> dict:
    system_prompt = get_system_prompt("design_review_agent") or _BUILTIN_SYSTEM_PROMPT

    user_message = f"""## Project specification

{spec}

## Issue to review

**Title:** {issue_title}

{issue_body}"""

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        start = raw.index("\n") + 1
        end = raw.rfind("```")
        raw = raw[start:end] if end > start else raw[start:]
    raw = raw.strip()

    return json.loads(raw)


def review_needs_decision_issues(token: str, repo_name: str) -> int:
    """
    For each open issue with feedback-agent + needs-decision labels, ask Claude
    whether it can resolve the design questions using the project spec.

    - If yes: posts decision comment, swaps needs-decision → ready-to-implement.
    - If no: posts a "still needs input" comment summarising what is ambiguous.

    Returns the count of issues auto-resolved (had ready-to-implement applied).
    """
    if not token or not repo_name:
        print("  [design-agent] no GITHUB_TOKEN or GITHUB_REPOSITORY — skipping")
        return 0

    spec = _load_spec()
    repo = Github(token).get_repo(repo_name)
    auto_resolved = 0

    try:
        issues = list(repo.get_issues(state="open", labels=["feedback-agent", "needs-decision"]))
    except GithubException as e:
        print(f"  [design-agent] could not fetch issues: {e}")
        return 0

    if not issues:
        print("  [design-agent] no needs-decision issues to review")
        return 0

    print(f"  [design-agent] reviewing {len(issues)} needs-decision issue(s)...")

    try:
        ready_label = repo.get_label("ready-to-implement")
        needs_label = repo.get_label("needs-decision")
    except GithubException as e:
        print(f"  [design-agent] could not fetch labels: {e}")
        return 0

    for issue in issues:
        current_label_names = {lb.name for lb in issue.labels}
        if "ready-to-implement" in current_label_names:
            print(f"  [design-agent] #{issue.number} already has ready-to-implement — skipping")
            continue

        print(f"  [design-agent] reviewing #{issue.number}: {issue.title[:60]}")

        try:
            result = _call_design_claude(issue.title, issue.body or "", spec)
        except Exception as e:
            print(f"  [design-agent] error calling Claude for #{issue.number}: {e}")
            continue

        try:
            if result.get("can_resolve"):
                comment = (
                    "**Design Agent Decision** 🤖\n\n"
                    + result["decision"]
                    + "\n\n---\n*Resolved automatically from project spec. "
                    "Applying `ready-to-implement` — the next pipeline run will implement this.*"
                )
                issue.create_comment(comment)
                issue.add_to_labels(ready_label)
                issue.remove_from_labels(needs_label)
                print(f"  [design-agent] ✓ resolved #{issue.number}")
                auto_resolved += 1
            else:
                comment = (
                    "**Design Agent Review** 🤖\n\n"
                    "I reviewed the project spec but could not fully resolve this issue automatically.\n\n"
                    + result["remaining_questions"]
                    + "\n\n---\n*Please answer the outstanding questions above and apply "
                    "the `ready-to-implement` label when ready.*"
                )
                issue.create_comment(comment)
                print(f"  [design-agent] ✗ needs human input: #{issue.number}")
        except GithubException as e:
            print(f"  [design-agent] error updating issue #{issue.number}: {e}")

    return auto_resolved
