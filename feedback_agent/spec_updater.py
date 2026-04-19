# SDK-based spec.md updater. Uses Supabase for system prompt with disk fallback.
import os
import re
import subprocess
from datetime import date
from pathlib import Path

import anthropic
from feedback_agent.agent_loader import get_system_prompt

# Source dirs to diff (relative to repo root)
CODE_DIFF_PATHS = [
    "backend/routers",
    "backend/models",
    "backend/services",
    "backend/schemas",
    "backend/main.py",
    "frontend/src/components",
    "frontend/src/pages",
    "frontend/src/hooks",
    "frontend/src/utils",
]

TEST_DIFF_PATHS = [
    "backend/tests",
    "frontend/src/test",
]

# Built-in system prompt used when Supabase is unavailable
_BUILTIN_SYSTEM_PROMPT = """You are the Spec Updater Agent. You keep spec.md accurate by reflecting code changes.

Given a code diff and the current spec, produce an updated spec that documents what actually changed.

Rules:
- Return the COMPLETE updated spec.md only — no commentary, no preamble, no code fences. Start directly with the first line of the spec.
- Bump the minor version (e.g. v0.8 → v0.9) and update the date if there are meaningful user-facing changes.
- If there is a changelog or version history section, add a concise new entry summarising the changes.
- Update only sections affected by the diff — do not rewrite sections that have not changed.
- If the diff contains only cosmetic or internal refactors with no user-facing change, do not bump the version.
- Output the complete document — do not truncate any section."""


def _git(repo_root: str, *args) -> str:
    result = subprocess.run(
        ["git", "-C", repo_root, *args],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def update_spec(repo_root: str, app_root: str) -> str:
    """
    Update spec.md to reflect code changes since it was last modified.
    Returns the new spec version string (e.g. 'v0.9').
    """
    spec_path = Path(app_root) / "spec.md"
    if not spec_path.exists():
        print("  [spec] spec.md not found — skipping")
        return ""

    # Find the commit where spec.md was last changed
    rel_spec = os.path.relpath(spec_path, repo_root)
    spec_commit = _git(repo_root, "log", "--follow", "-1", "--format=%H", "--", rel_spec)
    if not spec_commit:
        print("  [spec] could not find last spec commit — skipping")
        return ""

    # Code diff since that commit
    code_diff = _git(repo_root, "diff", spec_commit, "HEAD", "--", *CODE_DIFF_PATHS)
    code_diff = code_diff[:25000] if len(code_diff) > 25000 else code_diff

    # Test diff since that commit
    test_diff = _git(repo_root, "diff", spec_commit, "HEAD", "--", *TEST_DIFF_PATHS)
    test_diff = test_diff[:8000] if len(test_diff) > 8000 else test_diff

    # Changed file list
    changed_files = _git(repo_root, "diff", "--name-only", spec_commit, "HEAD",
                         "--", *CODE_DIFF_PATHS, *TEST_DIFF_PATHS)

    # Current spec version
    spec_content = spec_path.read_text()
    current_version = "unknown"
    for line in spec_content.splitlines():
        if line.startswith("**Spec Version:**"):
            m = re.search(r"v\d+\.\d+", line)
            if m:
                current_version = m.group(0)
            break

    if not code_diff and not test_diff:
        print(f"  [spec] no code changes since {spec_commit[:8]} — skipping")
        return current_version

    today = date.today().isoformat()
    system_prompt = get_system_prompt("spec_updater_agent") or _BUILTIN_SYSTEM_PROMPT

    user_message = f"""Current spec version: {current_version}
Today's date: {today}

## Source files changed since spec was last updated

{changed_files or "(none)"}

## Code diff (up to 25 KB)

```diff
{code_diff or "(no code changes)"}
```

## Test diff (up to 8 KB)

```diff
{test_diff or "(no test changes)"}
```

## Current spec.md

{spec_content}"""

    print(f"  [spec] updating from {current_version} (diff since {spec_commit[:8]})")
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    updated = message.content[0].text.strip()
    spec_path.write_text(updated)

    new_version = current_version
    for line in updated.splitlines():
        if line.startswith("**Spec Version:**"):
            m = re.search(r"v\d+\.\d+", line)
            if m:
                new_version = m.group(0)
            break

    print(f"  [spec] {current_version} → {new_version}")
    return new_version
