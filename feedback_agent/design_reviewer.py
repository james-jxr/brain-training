# Calls functional_design_agent or interaction_design_agent in review mode
# to resolve needs-design-review GitHub issues.
#
# Both design agents already support a question-resolution output format:
#   {"can_resolve": bool, "decision": "...", "remaining_questions": "..."}
# This module drives that flow per-issue.

import anthropic
import json
import time

REVIEW_MODEL = "claude-sonnet-4-6"


def review_design_issue(
    issue: dict,
    spec_content: str,
    design_content: str,
    design_agent: str,
    functional_design_prompt: str,
    interaction_design_prompt: str,
) -> dict:
    """
    Ask the appropriate design agent to review a single needs-design-review issue.

    Args:
        issue: {number, title, body, comments}
        spec_content: full text of spec.md / functional-spec.md
        design_content: full text of design-guide.md
        design_agent: "functional_design" | "interaction_design"
        functional_design_prompt: system prompt from Supabase
        interaction_design_prompt: system prompt from Supabase

    Returns:
        {
          "issue_number": int,
          "can_resolve": bool,
          "decision": str,         # if can_resolve
          "remaining_questions": str,  # if not can_resolve
          "usage": {input_tokens, output_tokens}
        }
    """
    if design_agent == "functional_design":
        system_prompt = functional_design_prompt
        context = f"## Functional Spec\n\n{spec_content}" if spec_content else ""
    else:
        system_prompt = interaction_design_prompt
        context = f"## Design Guide\n\n{design_content}" if design_content else ""

    if not system_prompt:
        return {
            "issue_number": issue["issue_number"],
            "can_resolve": False,
            "decision": "",
            "remaining_questions": "Design agent system prompt unavailable.",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    comments_text = ""
    if issue.get("comments"):
        comments_text = "\n\n## Previous comments\n\n" + "\n\n---\n\n".join(issue["comments"])

    user_message = (
        f"{context}\n\n"
        f"## Issue Review\n\n"
        f"**Issue #{issue['issue_number']}: {issue['title']}**\n\n"
        f"{issue.get('body', '')}"
        f"{comments_text}"
    )

    t0 = time.monotonic()
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=REVIEW_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    duration_ms = int((time.monotonic() - t0) * 1000)

    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    usage = {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}

    try:
        result = json.loads(raw)
        can_resolve = bool(result.get("can_resolve", False))
        print(f"  [design_reviewer] #{issue['issue_number']}: "
              f"{'resolved' if can_resolve else 'unresolved'} "
              f"({design_agent}, {duration_ms}ms)")
        return {
            "issue_number": issue["issue_number"],
            "can_resolve": can_resolve,
            "decision": result.get("decision", ""),
            "remaining_questions": result.get("remaining_questions", ""),
            "guide_extension": result.get("guide_extension", ""),
            "usage": usage,
        }
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  [design_reviewer] WARNING: could not parse response for "
              f"#{issue['issue_number']}: {e}")
        return {
            "issue_number": issue["issue_number"],
            "can_resolve": False,
            "decision": "",
            "remaining_questions": f"Design agent returned unparseable response: {raw[:200]}",
            "usage": usage,
        }


def run_design_reviews(
    issues: list[dict],
    spec_content: str,
    design_content: str,
    functional_design_prompt: str,
    interaction_design_prompt: str,
) -> tuple[list[dict], list[dict], dict]:
    """
    Review all needs-design-review issues.

    Each issue must have a 'design_agent' key ('functional_design' | 'interaction_design')
    indicating which agent to call. This is stored in the issue body by the review pipeline.

    Returns:
        (resolved, unresolved, total_usage)
        resolved: [{issue_number, decision, guide_extension}]
        unresolved: [{issue_number, remaining_questions}]
    """
    resolved = []
    unresolved = []
    total_usage = {"input_tokens": 0, "output_tokens": 0}

    for issue in issues:
        design_agent = _infer_design_agent(issue)
        result = review_design_issue(
            issue=issue,
            spec_content=spec_content,
            design_content=design_content,
            design_agent=design_agent,
            functional_design_prompt=functional_design_prompt,
            interaction_design_prompt=interaction_design_prompt,
        )
        total_usage["input_tokens"] += result["usage"]["input_tokens"]
        total_usage["output_tokens"] += result["usage"]["output_tokens"]

        if result["can_resolve"]:
            resolved.append({
                "issue_number": result["issue_number"],
                "decision": result["decision"],
                "guide_extension": result.get("guide_extension", ""),
            })
        else:
            unresolved.append({
                "issue_number": result["issue_number"],
                "remaining_questions": result["remaining_questions"],
            })

    print(f"  [design_reviewer] {len(resolved)} resolved, {len(unresolved)} unresolved")
    return resolved, unresolved, total_usage


def _infer_design_agent(issue: dict) -> str:
    """
    Determine which design agent to call based on labels or body content.
    Defaults to functional_design if no clear signal.
    """
    labels = issue.get("labels", [])
    body = (issue.get("body") or "").lower()

    # Label set by the review pipeline when the issue was created
    if "interaction_design" in labels or "interaction-design" in labels:
        return "interaction_design"
    if "functional_design" in labels or "functional-design" in labels:
        return "functional_design"

    # Infer from body content
    if "design agent assigned: `interaction_design`" in body:
        return "interaction_design"
    if "design agent assigned: `functional_design`" in body:
        return "functional_design"

    # Fallback: UX/visual keywords → interaction, else functional
    ux_keywords = ("color", "colour", "layout", "spacing", "font", "button", "ux",
                   "visual", "style", "icon", "animation", "responsive", "mobile")
    if any(kw in body for kw in ux_keywords):
        return "interaction_design"
    return "functional_design"
