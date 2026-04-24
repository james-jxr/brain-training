# Synthesis stage: reads raw feedback, calls the feedback_agent (system prompt loaded
# from Supabase) to produce a structured list of actionable change items.
import anthropic
import os
from pathlib import Path
from feedback_agent.json_utils import extract_json
from feedback_agent.agent_loader import get_system_prompt

REPO_ROOT = str(Path(__file__).parent.parent.resolve())

# Directories to walk for the file tree
SEARCH_DIRS = [
    "frontend/src",
    "backend/routers",
    "backend/models",
    "backend/services",
    "backend/schemas",
]

# Built-in system prompt used when Supabase is unavailable
_BUILTIN_SYSTEM_PROMPT = """You are a product analyst reviewing user feedback for a brain training web app.

The app has these components:
- Baseline assessment (multi-game adaptive cognitive test using a 2-up/1-down staircase)
- Training sessions (exercise types: NBack, DigitSpan, GoNoGo, Stroop, CardMemory, ShapeSort)
- Dashboard, Progress, Onboarding, Settings, Session, SessionSummary, FreePlay pages
- Frontend: React/Vite. Backend: FastAPI/Python. DB: PostgreSQL.

Analyse feedback and produce a JSON array of change items. Each item must have:
- "id": short slug (e.g. "stroop-button-colour")
- "title": one-line description
- "type": one of "bug_fix" | "mechanic_change" | "feature" | "design"
- "priority": "high" | "medium" | "low"
- "description": what to change and why (2-3 sentences)
- "files_likely_affected": array of relative file paths from the file tree provided
- "implementable": true if a coding agent can implement this without further design decisions

Rules:
- Output JSON only — no prose before or after.
- Merge duplicate feedback into a single item.
- Do not create items for vague or already-resolved feedback.
- items with implementable=false will be logged as GitHub Issues for human review.
- files_likely_affected must use real paths from the file tree, not guesses."""


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


def synthesise(feedback_rows: list, resolved_items: list | None = None) -> list:
    """Call the feedback_agent to synthesise feedback rows into structured change items."""
    if not feedback_rows and not resolved_items:
        return []

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

    user_message = f"""## Source file tree

{file_tree}

## Previously resolved design items

The following items were flagged as non-implementable but have since been resolved by the product owner. Mark these implementable=true with the decision reflected in the description:

{resolved_text or "(none)"}

## Raw user feedback

{feedback_text}"""

    system_prompt = get_system_prompt("feedback_agent") or _BUILTIN_SYSTEM_PROMPT

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return extract_json(message.content[0].text, expected_start="[")
