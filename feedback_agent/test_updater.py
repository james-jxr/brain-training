# Test updater: after code changes are written, keeps test files in sync.
# Calls the testing_agent (system prompt from Supabase) to add/update tests.
import anthropic
import json
import os
from pathlib import Path
from feedback_agent.json_utils import extract_json
from feedback_agent.agent_loader import get_system_prompt

REPO_ROOT = Path(__file__).parent.parent

BACKEND_TEST_DIR = REPO_ROOT / "backend" / "tests"
FRONTEND_TEST_DIR = REPO_ROOT / "frontend" / "src" / "test"

# Built-in system prompt used when Supabase is unavailable
_BUILTIN_SYSTEM_PROMPT = """You are a senior software engineer keeping tests in sync with code changes for a brain training web app.

Review the code changes and update the test files to maintain coverage.
Return ONLY a JSON object mapping file paths to complete updated file contents.
Only include test files that actually need changes. If no changes are needed, return {}.

Rules:
- Return valid JSON only — no prose, no markdown fences.
- Keys are relative file paths. Values are complete file content as a string.
- Add tests for new behaviour introduced by the code changes.
- Update existing tests that would break due to the code changes.
- Do not remove tests unless the feature they test was removed.
- Do not add tests for unchanged behaviour.
- Backend tests use pytest + httpx TestClient with SQLite (DATABASE_URL env var).
- Frontend tests use Vitest + jsdom.
- ALWAYS prefer testing exported pure functions over rendering React components. Pure function tests never timeout.
- If a component exports computeResult, calculateScore, or similar, test that function directly.
- If you must render a component, use vi.useFakeTimers() and vi.advanceTimersByTime() — never rely on real delays."""


def _read_file_safe(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def _build_changed_files_section(changed_file_map: dict) -> str:
    parts = []
    for rel_path, content in changed_file_map.items():
        parts.append(f"### {rel_path}\n```\n{content}\n```")
    return "\n\n".join(parts)


def _build_test_files_section(test_dirs: list[Path]) -> str:
    parts = []
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for path in sorted(test_dir.rglob("*")):
            if path.is_file() and not path.name.startswith(".") and path.name != "setup.js":
                rel = os.path.relpath(path, REPO_ROOT)
                content = _read_file_safe(path)
                parts.append(f"### {rel}\n```\n{content}\n```")
    return "\n\n".join(parts)


def update_tests(changed_file_map: dict) -> dict:
    """
    Given a map of {rel_path: new_content} for changed source files,
    produce updated test files if needed. Returns {rel_path: content} of changed tests.
    """
    if not changed_file_map:
        return {}

    changed_section = _build_changed_files_section(changed_file_map)
    test_section = _build_test_files_section([BACKEND_TEST_DIR, FRONTEND_TEST_DIR])
    test_section = test_section[:30000]  # ~30KB cap

    if not test_section:
        print("  [tests] no existing test files found, skipping test update")
        return {}

    user_message = f"""## Code changes made in this pipeline run

{changed_section}

## Existing test files

{test_section}"""

    system_prompt = get_system_prompt("testing_agent") or _BUILTIN_SYSTEM_PROMPT

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text
    if not raw.strip():
        raise ValueError(f"Claude returned empty response for test update (stop_reason={message.stop_reason})")

    try:
        file_map = extract_json(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON for test update (stop_reason={message.stop_reason}): {raw[:200]}") from e

    if not file_map:
        print("  [tests] no test changes needed")
        return {}

    for rel_path, content in file_map.items():
        abs_path = REPO_ROOT / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content)
        print(f"  [tests] updated {rel_path}")

    return file_map
