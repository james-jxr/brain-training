# Calls issue_prioritisation_agent to select and order issues for the
# current implementation run.

import anthropic
import json
import time

PRIORITISER_MODEL = "claude-sonnet-4-6"


def prioritise_issues(
    issues: list[dict],
    system_prompt: str,
) -> tuple[list[dict], list[dict], dict]:
    """
    Ask issue_prioritisation_agent to select and order issues for this run.

    Args:
        issues: list of GitHub issue dicts with keys:
                number, title, body, labels, created_at, comments (list of body strings)
        system_prompt: loaded from Supabase via agent_loader

    Returns:
        (selected, deferred, usage)
        selected: ordered list of implementation plan items ready for build_agent
        deferred: list of {issue_number, reason} for issues not selected this run
        usage: {input_tokens, output_tokens}
    """
    if not issues:
        return [], [], {"input_tokens": 0, "output_tokens": 0}

    user_message = (
        f"Select and order issues for this implementation run.\n\n"
        f"Open ready-to-implement issues ({len(issues)}):\n\n"
        + json.dumps(issues, indent=2, default=str)
    )

    t0 = time.monotonic()
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=PRIORITISER_MODEL,
        max_tokens=8192,
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

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [prioritiser] ERROR: agent returned non-JSON: {e}")
        print(f"  [prioritiser] raw response (first 300): {raw[:300]}")
        usage = {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}
        return [], [], usage
    selected = result.get("selected", [])
    deferred = result.get("deferred", [])
    rationale = result.get("run_rationale", "")

    usage = {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}

    print(f"  [prioritiser] {len(selected)} selected, {len(deferred)} deferred "
          f"in {duration_ms}ms (in={msg.usage.input_tokens} out={msg.usage.output_tokens})")
    if rationale:
        print(f"  [prioritiser] rationale: {rationale}")

    return selected, deferred, usage
