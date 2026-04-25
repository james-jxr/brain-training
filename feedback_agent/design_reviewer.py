# Design review: scans open needs-decision issues against spec.md and attempts
# to resolve each one using only information already present in the spec.
import json
import anthropic
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def _parse_files_from_issue_body(body: str) -> list:
    """Extract file paths from the '### Files Likely Affected' section of an issue body."""
    files = []
    in_section = False
    for line in body.splitlines():
        if line.strip().startswith("### Files Likely Affected"):
            in_section = True
            continue
        if in_section:
            if line.startswith("#"):
                break
            # Lines like: - `frontend/src/components/Foo.jsx`
            stripped = line.strip().lstrip("- ").strip("`")
            if stripped and not stripped.startswith("("):
                files.append(stripped)
    return files


def run_design_review(issues: list, spec_content: str) -> tuple[list, list, dict]:
    """
    For each needs-decision issue, call Claude to attempt to resolve it from the spec.

    Returns (resolved, unresolved, usage) where:
      resolved   = [{issue_number, title, body, decision}]
      unresolved = [{issue_number, comment}]
      usage      = {input_tokens, output_tokens}
    """
    if not issues or not spec_content:
        return [], [], {}

    from feedback_agent.agent_loader import get_system_prompt
    system_prompt = get_system_prompt("interaction_design_agent")

    client = anthropic.Anthropic()
    resolved = []
    unresolved = []
    total_in = 0
    total_out = 0

    for issue in issues:
        issue_text = f"**Title:** {issue['title']}\n\n**Body:**\n{issue['body']}"
        if issue.get("comments"):
            issue_text += "\n\n**Comments so far:**\n" + "\n---\n".join(issue["comments"])

        user_message = (
            "Review the GitHub Issue below that is waiting for a design decision. "
            "Using ONLY the spec provided, determine whether the answer is already there.\n\n"
            "Return JSON only — no prose — with this exact structure:\n"
            '{"resolved": true, "decision": "..."}\n'
            "or\n"
            '{"resolved": false, "comment": "..."}\n\n'
            "Rules:\n"
            "- resolved=true only when the spec unambiguously answers the question(s). "
            "The decision must be specific enough for a developer to implement without further input.\n"
            "- resolved=false when anything is ambiguous or missing. "
            "The comment must name which spec sections were checked and what specific information "
            "is still absent.\n"
            "- Do not invent design directions. Only surface what is explicitly in the spec.\n\n"
            f"## Spec\n\n{spec_content[:20000]}\n\n"
            f"## Issue\n\n{issue_text}"
        )

        if system_prompt:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
        else:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": user_message}]
            )

        total_in += message.usage.input_tokens
        total_out += message.usage.output_tokens

        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  [design-review] non-JSON response for #{issue['issue_number']}, skipping")
            continue

        if result.get("resolved"):
            resolved.append({
                "issue_number": issue["issue_number"],
                "title": issue["title"],
                "body": issue["body"],
                "decision": result["decision"],
            })
            print(f"  [design-review] resolved #{issue['issue_number']}: {issue['title'][:60]}")
        else:
            unresolved.append({
                "issue_number": issue["issue_number"],
                "comment": result.get("comment", "Spec does not contain sufficient information to resolve this issue."),
            })
            print(f"  [design-review] unresolved #{issue['issue_number']}: {issue['title'][:60]}")

    usage = {"input_tokens": total_in, "output_tokens": total_out}
    return resolved, unresolved, usage
