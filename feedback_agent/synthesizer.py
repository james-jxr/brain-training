# Synthesis stage: reads raw feedback, calls Claude to produce a structured
# list of actionable change items classified by type and priority.
import anthropic
import json
import os
from pathlib import Path

REPO_ROOT = str(Path(__file__).parent.parent.resolve())
PROMPTS_DIR = Path(__file__).parent / "prompts"

# Directories to walk for the file tree
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


def synthesise(feedback_rows: list, resolved_items: list | None = None) -> tuple[list, dict]:
    """
    Call Claude to synthesise feedback rows into structured change items.
    Returns (items, usage) where usage = {"input_tokens": N, "output_tokens": N}.
    Loads prompt from Agent Central Supabase; falls back to local synthesis.md.
    """
    if not feedback_rows:
        return [], {}

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

    # Load prompt from Agent Central (or local fallback)
    from feedback_agent.agent_loader import get_system_prompt
    template = get_system_prompt("feedback_synthesis_agent") or load_prompt("synthesis")

    prompt = (template
              .replace("{file_tree}", file_tree)
              .replace("{resolved_items}", resolved_text or "(none)")
              .replace("{feedback_text}", feedback_text))

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-7",
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
    return json.loads(raw), usage
