# Calls audit_findings_agent to classify code audit and coordination findings.
# Returns routing decisions used by the review pipeline to set GitHub issue labels.

import anthropic
import json
import time

AUDIT_MODEL = "claude-sonnet-4-6"


def classify_audit_findings(
    audit_findings: list[dict],
    coord_findings: list[dict],
    system_prompt: str,
) -> tuple[list[dict], dict]:
    """
    Send findings to audit_findings_agent for routing classification.

    Returns a 2-tuple of:
      - list of classification dicts, each containing:
          {finding_id, table, routing, design_agent, rationale}
      - usage dict containing token counts:
          {input_tokens, output_tokens}

    routing: "ready_to_implement" | "needs_design_review" | "needs_human_review"
    design_agent: "functional_design" | "interaction_design" | null
    """
    if not audit_findings and not coord_findings:
        return [], {}

    entries = []
    for f in audit_findings:
        entries.append({
            "finding_id": f["id"],
            "table": "code_audit_findings",
            "finding_type": f.get("finding_type", "code_quality"),
            "severity": f.get("severity", "medium"),
            "description": f.get("description", ""),
            "file_path": f.get("file_path", ""),
        })
    for f in coord_findings:
        entries.append({
            "finding_id": f["id"],
            "table": "coordination_findings",
            "finding_type": f.get("finding_type", ""),
            "severity": f.get("severity", "medium"),
            "description": f.get("description", ""),
            "artifact_a": f.get("artifact_a", ""),
            "artifact_b": f.get("artifact_b", ""),
            "auto_fixable": f.get("auto_fixable", False),
            "route_to": f.get("route_to", ""),
        })

    user_message = (
        f"Classify the following {len(entries)} finding(s).\n\n"
        + json.dumps(entries, indent=2)
    )

    t0 = time.monotonic()
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=AUDIT_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    duration_ms = int((time.monotonic() - t0) * 1000)

    raw_response = msg.content[0].text.strip()
    if raw_response.startswith("```"):
        raw_response = raw_response.split("```")[1]
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]
    raw_response = raw_response.strip()

    result = json.loads(raw_response)
    classifications = result.get("classifications", [])
    print(f"  [audit_classifier] classified {len(classifications)} finding(s) "
          f"in {duration_ms}ms (in={msg.usage.input_tokens} out={msg.usage.output_tokens})")
    return classifications, {
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
    }
