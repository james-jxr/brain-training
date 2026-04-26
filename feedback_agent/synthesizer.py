# Synthesis stage for pipeline v2.
#
# Key change vs v1: audit and coordination findings are already structured, so
# they bypass the Claude call entirely and are converted directly to change items.
# Only user feedback goes through Claude.
#
# synthesise() returns the same (items, usage) tuple as v1 so the rest of the
# pipeline is unchanged.  Items from audit/coordination are prepended (they are
# already higher-priority from the aggregator's sort order).

import anthropic
import json
import os
from pathlib import Path

REPO_ROOT = str(Path(__file__).parent.parent.resolve())
PROMPTS_DIR = Path(__file__).parent / "prompts"

SEARCH_DIRS = [
    "frontend/src",
    "backend/routers",
    "backend/models",
    "backend/services",
    "backend/schemas",
]


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def build_file_tree() -> str:
    """Walk source dirs and return a sorted list of relative paths."""
    paths = []
    for rel_dir in SEARCH_DIRS:
        base = os.path.join(REPO_ROOT, rel_dir)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules", ".git")]
            for fname in files:
                if fname.startswith("."):
                    continue
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, REPO_ROOT)
                paths.append(rel_path)
    return "\n".join(sorted(paths))


# ── Direct conversion: audit / coordination → change items ────────────────────

def _audit_item_to_change(item) -> dict:
    """Convert an AggregatedItem (source=audit) to a pipeline change item."""
    short_id = (item.supabase_id or "")[:8]
    finding_type = item.raw.get("finding_type") or "code_quality"
    # Map finding_type to pipeline item type
    type_map = {
        "security": "bug_fix",
        "bug": "bug_fix",
        "code_quality": "refactor",
        "performance": "refactor",
        "principles": "refactor",
    }
    item_type = type_map.get(finding_type.lower(), "bug_fix")
    files = [item.file_path] if item.file_path else []
    return {
        "id": f"audit-{short_id}",
        "title": f"Fix {finding_type} issue: {item.description[:80]}",
        "type": item_type,
        "priority": item.priority,
        "implementable": True,
        "description": item.description,
        "files_likely_affected": files,
        "source": "audit",
        "supabase_id": item.supabase_id,
    }


def _coordination_item_to_change(item) -> dict:
    """Convert an AggregatedItem (source=coordination) to a pipeline change item."""
    short_id = (item.supabase_id or "")[:8]
    finding_type = item.raw.get("finding_type") or "coordination"
    files = [item.file_path] if item.file_path else []
    return {
        "id": f"coord-{short_id}",
        "title": f"Fix coordination gap ({finding_type}): {item.description[:80]}",
        "type": "coordination",
        "priority": item.priority,
        "implementable": item.auto_fixable,
        "description": item.description,
        "files_likely_affected": files,
        "route_to": item.route_to,
        "source": "coordination",
        "supabase_id": item.supabase_id,
    }


# ── Claude-powered synthesis for feedback ─────────────────────────────────────

def _synthesise_feedback(feedback_rows: list, resolved_items: list | None = None) -> tuple[list, dict]:
    """Call Claude to synthesise feedback rows. Same logic as v1."""
    feedback_text = "\n".join(
        f"[{row['page_context']}] {row['feedback_text']}"
        for row in feedback_rows
    )

    file_tree = build_file_tree()

    resolved_text = ""
    if resolved_items:
        lines = []
        for item in resolved_items:
            lines.append(f"- [{item['id']}] {item['title']}: {item.get('decision', '(no decision comment)')}")
        resolved_text = "\n".join(lines)

    from feedback_agent.agent_loader import get_system_prompt
    template = get_system_prompt("feedback_synthesis_agent") or load_prompt("synthesis")

    prompt = (template
              .replace("{file_tree}", file_tree)
              .replace("{resolved_items}", resolved_text or "(none)")
              .replace("{feedback_text}", feedback_text))

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    usage = {
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }

    items = json.loads(raw)
    # Tag each item with its source so the pipeline can route correctly
    for item in items:
        item.setdefault("source", "feedback")
    return items, usage


# ── Public API ─────────────────────────────────────────────────────────────────

def synthesise(
    feedback_rows: list,
    resolved_items: list | None = None,
    pre_structured_items: list | None = None,
) -> tuple[list, dict]:
    """
    Produce a unified list of actionable change items.

    Args:
        feedback_rows:        Raw feedback_entries rows (may be empty).
        resolved_items:       GitHub issues with ready-to-implement label (v1 compat).
        pre_structured_items: AggregatedItem objects from audit/coordination sources.
                              These bypass the Claude call — zero tokens consumed.

    Returns:
        (items, usage) — same shape as v1.
        usage reflects only the feedback synthesis call (0 tokens if no feedback).
    """
    all_items: list[dict] = []
    usage: dict = {"input_tokens": 0, "output_tokens": 0}

    # 1. Convert pre-structured items directly (no Claude call)
    for item in (pre_structured_items or []):
        if item.source == "audit":
            all_items.append(_audit_item_to_change(item))
        elif item.source == "coordination":
            all_items.append(_coordination_item_to_change(item))

    if pre_structured_items:
        print(f"  [synthesizer] {len(pre_structured_items)} audit/coordination item(s) "
              f"converted directly (0 tokens)")

    # 2. Call Claude only for user feedback
    if feedback_rows:
        print(f"  [synthesizer] synthesising {len(feedback_rows)} feedback row(s) via Claude...")
        feedback_items, usage = _synthesise_feedback(feedback_rows, resolved_items)
        all_items.extend(feedback_items)
        print(f"  [synthesizer] feedback synthesis: {len(feedback_items)} item(s), "
              f"{usage.get('input_tokens', 0)} in / {usage.get('output_tokens', 0)} out tokens")
    else:
        print("  [synthesizer] no feedback rows — skipping Claude call")

    return all_items, usage
