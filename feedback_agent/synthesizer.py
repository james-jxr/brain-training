# Synthesis stage for pipeline v3.
#
# Changes from v2:
#   - feedback_synthesis_agent is now project-agnostic.
#     The spec and file tree are injected into the user message as context,
#     rather than being baked into the agent's system prompt.
#   - feedback_agent is called after synthesis to get routing decisions.
#   - Returns routed items ready for GitHub issue creation.

import anthropic
import json
import os
from pathlib import Path

REPO_ROOT = str(Path(__file__).parent.parent.resolve())

SEARCH_DIRS = [
    "frontend/src",
    "backend/routers",
    "backend/models",
    "backend/services",
    "backend/schemas",
    "src",          # React-only projects
]


def build_file_tree(app_root: str | None = None) -> str:
    """Walk source dirs and return a sorted list of relative paths."""
    base = app_root or REPO_ROOT
    paths = []
    for rel_dir in SEARCH_DIRS:
        abs_dir = os.path.join(base, rel_dir)
        if not os.path.isdir(abs_dir):
            continue
        for root, dirs, files in os.walk(abs_dir):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules", ".git")]
            for fname in files:
                if fname.startswith("."):
                    continue
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, base)
                paths.append(rel_path)
    return "\n".join(sorted(paths))


def synthesise_feedback(
    feedback_rows: list[dict],
    spec_content: str,
    file_tree: str,
    synthesis_prompt: str,
    routing_prompt: str,
    resolved_items: list | None = None,
) -> tuple[list[dict], dict]:
    """
    Synthesise raw feedback rows into routed change items.

    Steps:
      1. Call feedback_synthesis_agent (project-agnostic) with spec + file_tree as context
      2. Call feedback_agent to get routing for each synthesized item
      3. Return items with 'routing' field added

    Returns (items, usage) where usage is the combined token count.
    """
    if not feedback_rows:
        return [], {"input_tokens": 0, "output_tokens": 0}

    feedback_text = "\n".join(
        f"[{row.get('page_context', 'unknown')}] {row.get('feedback_text', '')}"
        for row in feedback_rows
    )

    resolved_text = ""
    if resolved_items:
        lines = [
            f"- [{item.get('id', '?')}] {item.get('title', '')}: {item.get('decision', '')}"
            for item in resolved_items
        ]
        resolved_text = "\n".join(lines)

    # ── Step 1: Synthesis ──────────────────────────────────────────────────────
    synthesis_user_message = (
        f"## Functional Spec\n\n{spec_content}\n\n"
        f"## File Tree\n\n```\n{file_tree}\n```\n\n"
        f"## Previously resolved design items\n\n{resolved_text or '(none)'}\n\n"
        f"## Raw user feedback\n\n{feedback_text}"
    )

    client = anthropic.Anthropic()

    synth_msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        system=synthesis_prompt,
        messages=[{"role": "user", "content": synthesis_user_message}],
    )
    synth_usage = {
        "input_tokens": synth_msg.usage.input_tokens,
        "output_tokens": synth_msg.usage.output_tokens,
    }

    raw = synth_msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [synthesizer] ERROR: synthesis agent returned non-JSON: {e}")
        print(f"  [synthesizer] raw response (first 300): {raw[:300]}")
        return [], synth_usage
    for item in items:
        item.setdefault("source", "feedback")

    print(f"  [synthesizer] {len(items)} item(s) synthesised "
          f"(in={synth_usage['input_tokens']} out={synth_usage['output_tokens']})")

    if not items:
        return [], synth_usage

    # ── Step 2: Routing ────────────────────────────────────────────────────────
    routing_user_message = (
        f"## Project spec\n\n{spec_content[:4000]}\n\n"
        f"## File tree\n\n```\n{file_tree[:2000]}\n```\n\n"
        f"## Synthesised feedback items\n\n{json.dumps(items, indent=2)}"
    )

    route_msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=routing_prompt,
        messages=[{"role": "user", "content": routing_user_message}],
    )
    route_usage = {
        "input_tokens": route_msg.usage.input_tokens,
        "output_tokens": route_msg.usage.output_tokens,
    }

    raw = route_msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        routing_result = json.loads(raw)
        routed_items = routing_result.get("items", [])
        # Merge routing decisions back into synthesised items by id
        routing_map = {i["id"]: i for i in routed_items}
        for item in items:
            routed = routing_map.get(item["id"], {})
            item["routing"] = routed.get("routing", "skip")
            item["implementable"] = routed.get("implementable", False)
            if "files_likely_affected" not in item and routed.get("files_likely_affected"):
                item["files_likely_affected"] = routed["files_likely_affected"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  [synthesizer] WARNING: routing parse failed ({e}) — defaulting to skip")
        for item in items:
            item.setdefault("routing", "skip")
            item.setdefault("implementable", False)

    total_usage = {
        "input_tokens": synth_usage["input_tokens"] + route_usage["input_tokens"],
        "output_tokens": synth_usage["output_tokens"] + route_usage["output_tokens"],
    }

    print(f"  [synthesizer] routing: "
          f"{sum(1 for i in items if i.get('routing') == 'build')} build, "
          f"{sum(1 for i in items if i.get('routing') == 'functional_design')} functional_design, "
          f"{sum(1 for i in items if i.get('routing') == 'interaction_design')} interaction_design, "
          f"{sum(1 for i in items if i.get('routing') == 'skip')} skip")

    return items, total_usage
