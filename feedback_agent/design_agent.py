# Design agent: auto-reviews GitHub Issues with needs-decision label using project spec.
import json
from pathlib import Path

import anthropic
from github import Github, GithubException

REPO_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = Path(__file__).parent / "prompts"

SPEC_PATH = REPO_ROOT / "spec.md"


def _load_spec() -> str:
    return SPEC_PATH.read_text() if SPEC_PATH.exists() else "(spec.md not found)"


def _call_design_claude(issue_title: str, issue_body: str, spec: str) -> dict:
    from feedback_agent.agent_loader import get_system_prompt
    prompt_template = get_system_prompt("feedback_agent_design_reviewer") or (PROMPTS_DIR / "design_review.md").read_text()
    prompt = (prompt_template
              .replace("{spec_content}", spec)
              .replace("{issue_title}", issue_title)
              .replace("{issue_body}", issue_body))

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def review_needs_decision_issues(token: str, repo_name: str) -> int:
    """
    For each open issue with feedback-agent + needs-decision labels, ask Claude
    whether it can resolve the design questions using the project spec.

    - If yes: posts decision comment, swaps needs-decision → ready-to-implement.
    - If no: posts a "still needs input" comment summarising what's ambiguous.

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
                    "I reviewed the project spec but couldn't fully resolve this issue automatically.\n\n"
                    + result["remaining_questions"]
                    + "\n\n---\n*Please answer the outstanding questions above and apply "
                    "the `ready-to-implement` label when ready.*"
                )
                issue.create_comment(comment)
                print(f"  [design-agent] ✗ needs human input: #{issue.number}")
        except GithubException as e:
            print(f"  [design-agent] error updating issue #{issue.number}: {e}")

    return auto_resolved
