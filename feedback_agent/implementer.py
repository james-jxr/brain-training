# Implementation stage: for each implementable change item, reads the relevant
# source files and calls the build_agent (system prompt from Supabase) to produce
# updated file contents.
import anthropic
import json
import os
from pathlib import Path
from feedback_agent.json_utils import extract_json
from feedback_agent.agent_loader import get_system_prompt

REPO_ROOT = str(Path(__file__).parent.parent.resolve())

# Directories to search when resolving file paths
SEARCH_DIRS = ["frontend/src", "backend/routers", "backend/models", "backend/services", "backend/schemas"]

# Built-in system prompt used when Supabase is unavailable
_BUILTIN_SYSTEM_PROMPT = """You are a senior software engineer implementing a specific change to a brain training web app.
Frontend: React/Vite. Backend: FastAPI/Python. DB: PostgreSQL.

Implement the described change. Return ONLY a JSON object mapping each file path to its complete updated content.

Rules:
- Return valid JSON only — no prose, no markdown fences.
- Each key is the relative file path (e.g. "frontend/src/components/exercises/Stroop.jsx").
- Each value is the complete updated file content as a string.
- Make the minimal change needed — do not refactor or add features beyond what is described.
- Do not change existing function signatures, parameter names, or return types unless the description explicitly requires it.
- Export pure functions for testable logic (scoring, game results) so tests can verify without rendering components.
- Do not add comments explaining what you changed.
- Do not include files that have not changed."""


def _build_index() -> dict:
    """Build a map of lowercase basename (no ext) → list of real relative paths."""
    index: dict = {}
    for rel_dir in SEARCH_DIRS:
        base = os.path.join(REPO_ROOT, rel_dir)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules")]
            for fname in files:
                key = os.path.splitext(fname)[0].lower()
                rel = os.path.relpath(os.path.join(root, fname), REPO_ROOT)
                index.setdefault(key, []).append(rel)
    return index


def _resolve_path(rel_path: str, index: dict) -> str | None:
    """Return the best matching real path for rel_path, or None if not found."""
    abs_path = os.path.join(REPO_ROOT, rel_path)
    if os.path.exists(abs_path):
        return rel_path
    basename = os.path.splitext(os.path.basename(rel_path))[0].lower()
    candidates = index.get(basename, [])
    if len(candidates) == 1:
        print(f"  [resolved] {rel_path} → {candidates[0]}")
        return candidates[0]
    if len(candidates) > 1:
        guess_dir = os.path.dirname(rel_path).lower()
        scored = sorted(
            candidates,
            key=lambda p: len(os.path.commonprefix([guess_dir, os.path.dirname(p).lower()])),
            reverse=True,
        )
        print(f"  [resolved] {rel_path} → {scored[0]} (from {len(candidates)} candidates)")
        return scored[0]
    return None


def read_files(file_paths: list) -> dict:
    """Read source files relative to repo root. Falls back to fuzzy matching."""
    index = _build_index()
    contents = {}
    for rel_path in file_paths:
        resolved = _resolve_path(rel_path, index)
        if resolved:
            with open(os.path.join(REPO_ROOT, resolved), "r") as f:
                contents[resolved] = f.read()
        else:
            print(f"  [warn] file not found: {rel_path}")
    return contents


def write_files(file_map: dict):
    """Write updated file contents to disk. Skips entries with null/non-string content."""
    for rel_path, content in file_map.items():
        if not isinstance(content, str):
            print(f"  [warn] skipping {rel_path} — content is {type(content).__name__}, not str")
            continue
        abs_path = os.path.join(REPO_ROOT, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w") as f:
            f.write(content)
        print(f"  [wrote] {rel_path}")


def implement_change(item: dict) -> dict:
    """
    For a single change item, read the affected files, call the build_agent to
    produce updates, write them to disk. Returns the updated file map.
    """
    file_paths = item.get("files_likely_affected", [])
    if not file_paths:
        print(f"  [skip] {item['id']} — no files specified")
        return {}

    contents = read_files(file_paths)
    if not contents:
        print(f"  [skip] {item['id']} — no readable files")
        return {}

    file_contents_text = "\n\n".join(
        f"### {path}\n```\n{content}\n```"
        for path, content in contents.items()
    )

    user_message = f"""## Change to implement

Title: {item["title"]}
Description: {item["description"]}

## Current file contents

{file_contents_text}"""

    system_prompt = get_system_prompt("build_agent") or _BUILTIN_SYSTEM_PROMPT

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text
    if not raw.strip():
        raise ValueError(f"Claude returned an empty response (stop_reason={message.stop_reason})")

    try:
        file_map = extract_json(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON (stop_reason={message.stop_reason}): {raw[:200]}") from e

    write_files(file_map)
    return file_map
