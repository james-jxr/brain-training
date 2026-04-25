# SDK-based spec.md updater. Replaces update-spec.sh for use in CI.
# Uses the Anthropic Python SDK directly — no `claude` CLI dependency.
import os
import subprocess
from datetime import date
from pathlib import Path
import anthropic

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Source dirs to diff (relative to repo root)
CODE_DIFF_PATHS = [
    "apps/brain-training/backend/routers",
    "apps/brain-training/backend/models",
    "apps/brain-training/backend/services",
    "apps/brain-training/backend/schemas",
    "apps/brain-training/backend/main.py",
    "apps/brain-training/frontend/src/components",
    "apps/brain-training/frontend/src/pages",
    "apps/brain-training/frontend/src/hooks",
    "apps/brain-training/frontend/src/api",
    "apps/brain-training/frontend/src/utils",
]

TEST_DIFF_PATHS = [
    "apps/brain-training/backend/tests",
    "apps/brain-training/frontend/src/test",
]


def _git(repo_root: str, *args) -> str:
    result = subprocess.run(
        ["git", "-C", repo_root, *args],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def update_spec(repo_root: str, app_root: str) -> str:
    """
    Update spec.md to reflect code changes since it was last modified.
    Returns the new spec version string (e.g. 'v0.8').
    """
    spec_path = Path(app_root) / "spec.md"

    # Find the commit where spec.md was last changed
    rel_spec = os.path.relpath(spec_path, repo_root)
    spec_commit = _git(repo_root, "log", "--follow", "-1", "--format=%H", "--", rel_spec)
    if not spec_commit:
        print("  [spec] could not find last spec commit, skipping")
        return ""

    # Code diff since that commit
    code_diff = _git(repo_root, "diff", spec_commit, "HEAD", "--", *CODE_DIFF_PATHS)
    code_diff = code_diff[:25000] if len(code_diff) > 25000 else code_diff

    # Test diff since that commit
    test_diff = _git(repo_root, "diff", spec_commit, "HEAD", "--", *TEST_DIFF_PATHS)
    test_diff = test_diff[:8000] if len(test_diff) > 8000 else test_diff

    # Changed file list
    changed_files = _git(repo_root, "diff", "--name-only", spec_commit, "HEAD",
                         "--", "apps/brain-training/", f":!{rel_spec}")

    # Current spec version
    spec_content = spec_path.read_text()
    current_version = "unknown"
    for line in spec_content.splitlines():
        if line.startswith("**Spec Version:**"):
            import re
            m = re.search(r"v\d+\.\d+", line)
            if m:
                current_version = m.group(0)
            break

    if not code_diff and not test_diff:
        print(f"  [spec] no code changes since {spec_commit[:8]}, skipping update")
        return current_version

    today = date.today().isoformat()
    from feedback_agent.agent_loader import get_system_prompt
    template = get_system_prompt("spec_updater_agent") or (PROMPTS_DIR / "spec_update.md").read_text()
    prompt = (template
              .replace("{current_version}", current_version)
              .replace("{today}", today)
              .replace("{changed_files}", changed_files or "(none)")
              .replace("{code_diff}", code_diff or "(no code changes)")
              .replace("{test_diff}", test_diff or "(no test changes)")
              .replace("{spec_content}", spec_content))

    print(f"  [spec] updating from {current_version} (diff since {spec_commit[:8]})")
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    updated = message.content[0].text.strip()
    spec_path.write_text(updated)

    # Read new version
    new_version = current_version
    for line in updated.splitlines():
        if line.startswith("**Spec Version:**"):
            import re
            m = re.search(r"v\d+\.\d+", line)
            if m:
                new_version = m.group(0)
            break

    print(f"  [spec] {current_version} → {new_version}")
    return new_version
