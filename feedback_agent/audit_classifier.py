# Calls audit_findings_agent to classify code audit and coordination findings.
# Returns routing decisions used by the review pipeline to set GitHub issue labels.

import anthropic
import json
import time

AUDIT_MODEL = "claude-sonnet-4-6"
_BATCH_SIZE = 20  # max findings per API call to avoid output truncation


def classify_audit_findings(
    audit_findings: list[dict],
    coord_findings: list[dict],
    system_prompt: str,
) -> list[dict]:
    """
    Send findings to audit_findings_agent for routing classification.

    Returns a list of classification dicts:
      {finding_id, table, routing, design_agent, rationale}

    routing: "ready_to_implement" | "needs_design_review" | "needs_human_review"
    design_agent: "functional_design" | "interaction_design" | null
    """
    if not audit_findings and not coord_findings:
        return [], {"input_tokens": 0, "output_tokens": 0}

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

    client = anthropic.Anthropic()
    all_classifications = []
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    total_ms = 0

    batches = [entries[i:i + _BATCH_SIZE] for i in range(0, len(entries), _BATCH_SIZE)]
    for batch_idx, batch in enumerate(batches):
        user_message = (
            f"Classify the following {len(batch)} finding(s).\n\n"
            + json.dumps(batch, indent=2)
        )
        t0 = time.monotonic()
        msg = client.messages.create(
            model=AUDIT_MODEL,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        total_ms += int((time.monotonic() - t0) * 1000)
        total_usage["input_tokens"] += msg.usage.input_tokens
        total_usage["output_tokens"] += msg.usage.output_tokens

        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"  [audit_classifier] ERROR: batch {batch_idx + 1} returned non-JSON: {e}")
            print(f"  [audit_classifier] raw response (first 300): {raw[:300]}")
            continue
        batch_classifications = result.get("classifications", [])
        all_classifications.extend(batch_classifications)
        if len(batches) > 1:
            print(f"  [audit_classifier] batch {batch_idx + 1}/{len(batches)}: "
                  f"{len(batch_classifications)} classified")

    print(f"  [audit_classifier] classified {len(all_classifications)} finding(s) "
          f"in {total_ms}ms (in={total_usage['input_tokens']} out={total_usage['output_tokens']})")
    return all_classifications, total_usage
