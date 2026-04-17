# Git and GitHub helpers for the feedback agent pipeline.
import os
import shutil
import subprocess
from pathlib import Path


def run(cmd: list, cwd: str = None) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


REPO_ROOT = str(Path(__file__).parent.parent.resolve())


def create_branch(branch_name: str) -> str:
    run(["git", "checkout", "main"], cwd=REPO_ROOT)
    run(["git", "pull", "origin", "main"], cwd=REPO_ROOT)
    run(["git", "checkout", "-b", branch_name], cwd=REPO_ROOT)
    return branch_name


def commit_all(message: str):
    run(["git", "add", "-A"], cwd=REPO_ROOT)
    status = run(["git", "status", "--porcelain"], cwd=REPO_ROOT)
    if not status:
        print("  [git] nothing to commit")
        return False
    run(["git", "commit", "-m", message], cwd=REPO_ROOT)
    return True


def push_branch(branch_name: str):
    run(["git", "push", "origin", branch_name], cwd=REPO_ROOT)



def open_pr(branch_name: str, title: str, body: str) -> str:
    """Open a GitHub PR using the gh CLI. Returns the PR URL."""
    gh = shutil.which("gh") or "/opt/homebrew/bin/gh"
    result = subprocess.run(
        [gh, "pr", "create",
         "--title", title,
         "--body", body,
         "--base", "main",
         "--head", branch_name],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh pr create failed:\n{result.stderr}")
    # gh prints the PR URL as the last line
    return result.stdout.strip().split("\n")[-1]
