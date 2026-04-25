# Implementation stage: for each implementable change item, reads the relevant
# source files and calls Claude to produce the updated file contents.
import anthropic
import json
import os
from pathlib import Path

REPO_ROOT = str(Path(__file__).parent.parent.resolve())
PROMPTS_DIR = Path(__file__).parent / "prompts"

# Directories to search when resolving file paths
SEARCH_DIRS = ["frontend/src", "backend/routers", "backend/models", "backend/services", "backend/schemas"]


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


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
    For a single change item, read the affected files, call Claude to
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

    prompt = (load_prompt("implementation")
              .replace("{title}", item["title"])
              .replace("{description}", item["description"])
              .replace("{file_contents}", file_contents_text))

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    if not raw:
        raise ValueError(f"Claude returned an empty response (stop_reason={message.stop_reason})")

    try:
        file_map = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON (stop_reason={message.stop_reason}): {raw[:200]}") from e

    write_files(file_map)
    return file_map
