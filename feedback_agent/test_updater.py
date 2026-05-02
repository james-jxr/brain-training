# Test updater: after code changes are written, keeps test files in sync.
# Reads changed source files + existing tests, asks Claude to add/update tests.
import anthropic
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = Path(__file__).parent / "prompts"

BACKEND_TEST_DIR = REPO_ROOT / "backend" / "tests"
FRONTEND_TEST_DIR = REPO_ROOT / "frontend" / "src" / "test"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def _read_file_safe(path: Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def _build_changed_files_section(changed_file_map: dict) -> str:
    """Format {rel_path: content} dict for the prompt."""
    parts = []
    for rel_path, content in changed_file_map.items():
        parts.append(f"### {rel_path}\n```\n{content}\n```")
    return "\n\n".join(parts)


def _build_test_files_section(test_dirs: list[Path]) -> str:
    """Read all test files and format for the prompt."""
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


def update_tests(changed_file_map: dict) -> tuple[dict, dict]:
    """
    Given a map of {rel_path: new_content} for changed source files,
    produce updated test files if needed.
    Returns (file_map, usage) where usage = {"input_tokens": N, "output_tokens": N}.
    Uses testing_agent from Agent Central with system+user split; falls back to
    local test_update.md template as a single user message.
    """
    if not changed_file_map:
        return {}, {}

    changed_section = _build_changed_files_section(changed_file_map)
    # Cap test section to avoid overflowing context — only include files likely related
    test_section = _build_test_files_section([BACKEND_TEST_DIR, FRONTEND_TEST_DIR])
    test_section = test_section[:30000]  # ~30KB cap before hitting token limits

    if not test_section:
        print("  [tests] no existing test files found, skipping test update")
        return {}, {}

    from feedback_agent.agent_loader import get_system_prompt
    system_prompt = get_system_prompt("testing_agent")

    client = anthropic.Anthropic()

    if system_prompt:
        # Agent Central path: generic role as system, task-specific user message.
        user_message = (
            "Update or add test files to cover the following source changes. "
            "Return a JSON object only — no prose, no markdown.\n\n"
            f"## Changed source files\n\n{changed_section}\n\n"
            f"## Existing test files\n\n{test_section}\n\n"
            "Return only a JSON object mapping relative test file paths to complete "
            "updated file contents, or {} if no test changes are needed. "
            "Start your response with { and end with }."
        )
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message},
            ]
        )
    else:
        # Local fallback: full template as single user message
        try:
            prompt = (load_prompt("test_update")
                      .replace("{changed_files_with_content}", changed_section)
                      .replace("{existing_test_files}", test_section))
        except FileNotFoundError:
            print("  [test_updater] WARNING: agent prompt unavailable (Supabase down, no local fallback); skipping test update")
            return {}, {}
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16000,
            messages=[
                {"role": "user", "content": prompt},
            ]
        )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    if not raw:
        raise ValueError(f"Claude returned empty response for test update (stop_reason={message.stop_reason})")

    try:
        file_map = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned non-JSON for test update (stop_reason={message.stop_reason}): {raw[:200]}") from e

    if not file_map:
        print("  [tests] no test changes needed")
        return {}, {}

    usage = {
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }

    # Write updated test files
    for rel_path, content in file_map.items():
        abs_path = REPO_ROOT / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content)
        print(f"  [tests] updated {rel_path}")

    return file_map, usage
