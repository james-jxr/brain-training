# SDK-based spec.md updater. Replaces update-spec.sh for use in CI.
# Uses the Anthropic Python SDK directly — no `claude` CLI dependency.
import os
import subprocess
from datetime import date
from pathlib import Path
import anthropic

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Extensions treated as source code for the spec diff.
# The feedback_agent/ directory is excluded — it contains pipeline code, not app code.
_SOURCE_EXTS = {"*.py", "*.js", "*.jsx", "*.ts", "*.tsx"}
_EXCLUDE_PATHS = [
    ":(exclude)feedback_agent/",
    ":(exclude)node_modules/",
    ":(exclude)*.min.*",
    ":(exclude)package-lock.json",
]
_TEST_PATTERNS = ["**/test/**", "**/tests/**", "**/*.test.*", "**/*_test.*", "**/test_*"]


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
    Works for any project repo — no hardcoded paths.
    """
    spec_path = Path(app_root) / "spec.md"

    # Find the commit where spec.md was last changed
    rel_spec = os.path.relpath(spec_path, repo_root)
    spec_commit = _git(repo_root, "log", "--follow", "-1", "--format=%H", "--", rel_spec)
    if not spec_commit:
        print("  [spec] could not find last spec commit, skipping")
        return ""

    # Source diff (all app code, excluding pipeline code, tests, and generated files)
    _test_markers = ("test/", "tests/", ".test.", "_test.", "test_")
    source_globs = list(_SOURCE_EXTS) + _EXCLUDE_PATHS + [f":(exclude){rel_spec}"]
    code_diff = _git(repo_root, "diff", spec_commit, "HEAD", "--", *source_globs)
    # Strip test file hunks from the source diff so they don't appear twice
    code_diff = "\n".join(
        l for l in code_diff.splitlines()
        if not any(marker in l for marker in _test_markers)
    )
    code_diff = code_diff[:25000] if len(code_diff) > 25000 else code_diff

    # Test diff (only test files)
    test_globs = _TEST_PATTERNS + _EXCLUDE_PATHS
    test_diff = _git(repo_root, "diff", spec_commit, "HEAD", "--", *test_globs)
    test_diff = test_diff[:8000] if len(test_diff) > 8000 else test_diff

    # Changed file list (all app files except spec itself)
    changed_files = _git(repo_root, "diff", "--name-only", spec_commit, "HEAD",
                         "--", *source_globs)

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
    try:
        template = get_system_prompt("spec_updater_agent") or (PROMPTS_DIR / "spec_update.md").read_text()
    except FileNotFoundError:
        print("  [spec_updater] WARNING: spec_updater_agent prompt unavailable (Supabase down, no local fallback); skipping spec update")
        return current_version
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
