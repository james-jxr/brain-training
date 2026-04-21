#!/usr/bin/env python3
"""
Pipeline Monitor Agent
======================
Invoked by GitHub Actions when the nightly feedback pipeline fails.
Fetches the CI logs, calls the pipeline_monitor_agent via Claude, and acts
on the response: commits a fix, creates a GitHub Issue, or hands off.

Usage:
    python feedback_agent/pipeline_monitor.py --run-id <RUN_ID> --repo <OWNER/REPO>

Environment variables:
    ANTHROPIC_API_KEY     Anthropic API key (required)
    GITHUB_TOKEN          GitHub token (required)
    SUPABASE_URL          Agent Central Supabase URL (optional)
    SUPABASE_SERVICE_KEY  Agent Central service role key (optional)
"""

import argparse
import json
import os
import subprocess
import sys
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

import anthropic
import requests

from feedback_agent.json_utils import extract_json
from feedback_agent.agent_loader import get_system_prompt

_FALLBACK_SYSTEM_PROMPT = """You are the Pipeline Monitor Agent. You are invoked when a pipeline run fails. Your job is to read the failure logs, identify the root cause, and either fix it or escalate it — never just report that something failed without a clear action.

## Your responsibilities

1. **Diagnose the failure** — read the full error log and classify the root cause into one of these categories:
   - `code_bug` — a bug in the pipeline code itself (wrong import path, logic error, unhandled exception in pipeline script)
   - `test_failure` — the pipeline ran but tests failed (hand off to the testing_agent)
   - `build_failure` — the pipeline ran but the app build failed (hand off to the build_agent)
   - `config_error` — a missing or malformed environment variable, secret, or external service credential
   - `dependency_error` — a missing or incompatible package/dependency
   - `infrastructure_error` — a transient platform issue (network timeout, runner outage, service unavailable)

2. **Fix code-level issues autonomously** — for `code_bug` and `dependency_error` root causes, produce the minimal fix. Return changed files in the output format.

3. **Escalate non-code failures** — for `config_error` and `infrastructure_error`, produce a GitHub Issue with exact, actionable instructions.

4. **Report findings** — always produce a structured report.

## Output format

Always return valid JSON only — no prose, no markdown fences.

{
  "diagnosis": {
    "root_cause_category": "code_bug | test_failure | build_failure | config_error | dependency_error | infrastructure_error",
    "summary": "One sentence describing exactly what failed and why",
    "error_excerpt": "The key lines from the log that confirm the diagnosis (max 10 lines)"
  },
  "action": "fixed | escalated | handed_off | no_action",
  "fixes": {
    "relative/path/to/file.py": "complete updated file content"
  },
  "github_issue": {
    "title": "Issue title (only if action = escalated or handed_off)",
    "body": "Full issue body with exact steps to fix",
    "labels": ["pipeline-failure", "needs-human"]
  },
  "handoff": {
    "agent": "testing_agent | build_agent",
    "context": "What the receiving agent needs to know"
  },
  "summary": "One paragraph: what you found, what you did, and what still needs doing"
}

## Rules

- Read the full traceback, not just the last line
- Distinguish config errors from code bugs — a KeyError on os.environ is a config error, not a code bug
- For config_error: name the exact variable, where to get it, where to set it, what format it should be
- Never commit secrets or credential values
- Never silently swallow failures — every failure produces either a fix or a GitHub Issue
- Fixes must be minimal — change only the lines required to resolve the failure
"""

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

REPO_ROOT = Path(__file__).parent.parent


def _gh_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_run_logs(repo: str, run_id: str) -> str:
    """Fetch the combined log text for a failed Actions run."""
    headers = _gh_headers()

    # Get jobs for this run
    jobs_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs"
    resp = requests.get(jobs_url, headers=headers, timeout=30)
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])

    log_parts = []
    for job in jobs:
        job_name = job.get("name", "unknown")
        job_id = job["id"]

        # Fetch logs for this job
        logs_url = f"https://api.github.com/repos/{repo}/actions/jobs/{job_id}/logs"
        log_resp = requests.get(logs_url, headers=headers, timeout=30, allow_redirects=True)
        if log_resp.status_code == 200:
            log_parts.append(f"=== JOB: {job_name} ===\n{log_resp.text}")
        else:
            log_parts.append(f"=== JOB: {job_name} — logs unavailable (HTTP {log_resp.status_code}) ===")

    return "\n\n".join(log_parts)


def create_github_issue(repo: str, title: str, body: str, labels: list[str]) -> str:
    """Create a GitHub Issue and return its URL."""
    headers = _gh_headers()

    # Ensure labels exist
    for label in labels:
        requests.post(
            f"https://api.github.com/repos/{repo}/labels",
            headers=headers,
            json={"name": label, "color": "d93f0b"},
            timeout=10,
        )

    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers=headers,
        json={"title": title, "body": body, "labels": labels},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["html_url"]


def apply_fixes(fixes: dict) -> list[str]:
    """Write fixed files to disk. Returns list of paths written."""
    written = []
    for rel_path, content in fixes.items():
        abs_path = REPO_ROOT / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content)
        written.append(rel_path)
        print(f"  [monitor] wrote fix: {rel_path}")
    return written


def commit_and_push(summary: str, paths: list[str]) -> bool:
    """Stage, commit, and push fixed files to main."""
    try:
        subprocess.run(["git", "add"] + paths, check=True, cwd=REPO_ROOT)
        msg = f"[pipeline-monitor] auto-fix: {summary}"
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=REPO_ROOT)
        subprocess.run(["git", "push", "origin", "HEAD:main"], check=True, cwd=REPO_ROOT)
        print("  [monitor] fix committed and pushed to main")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [monitor] git operation failed: {e}")
        return False


def run_monitor(run_id: str, repo: str) -> None:
    print(f"\n[pipeline-monitor] Diagnosing failure for run {run_id} in {repo}")

    # 1. Fetch logs
    print("[pipeline-monitor] Fetching CI logs...")
    try:
        log_text = fetch_run_logs(repo, run_id)
    except Exception as e:
        print(f"[pipeline-monitor] Could not fetch logs: {e}")
        # Create a minimal escalation issue
        create_github_issue(
            repo,
            f"Pipeline failure — could not fetch logs for run {run_id}",
            f"The pipeline monitor failed to fetch logs for run {run_id}.\n\nError: {e}\n\nPlease check the run manually: https://github.com/{repo}/actions/runs/{run_id}",
            ["pipeline-failure", "needs-human"],
        )
        return

    # Truncate log to avoid overwhelming the model
    max_log_chars = 30_000
    if len(log_text) > max_log_chars:
        log_text = log_text[-max_log_chars:]
        log_text = f"[... log truncated to last {max_log_chars} chars ...]\n\n" + log_text

    # 2. Load system prompt
    system_prompt = get_system_prompt("pipeline_monitor_agent") or _FALLBACK_SYSTEM_PROMPT

    # 3. Call Claude
    print("[pipeline-monitor] Calling pipeline_monitor_agent...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    user_message = (
        f"A nightly feedback pipeline run has failed.\n\n"
        f"**Run URL:** {run_url}\n"
        f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**Repo:** {repo}\n\n"
        f"## CI Logs\n\n```\n{log_text}\n```\n\n"
        f"Diagnose the failure and respond with the appropriate action."
    )

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text
    except Exception as e:
        print(f"[pipeline-monitor] Claude API call failed: {e}")
        create_github_issue(
            repo,
            f"Pipeline failure — monitor agent could not run (run {run_id})",
            f"The pipeline_monitor_agent failed to call the Claude API.\n\nError: `{e}`\n\nPlease investigate manually: {run_url}",
            ["pipeline-failure", "needs-human"],
        )
        return

    # 4. Parse response
    try:
        result = extract_json(raw)
    except Exception as e:
        print(f"[pipeline-monitor] Could not parse agent response: {e}")
        print(f"[pipeline-monitor] Raw response:\n{raw[:500]}")
        create_github_issue(
            repo,
            f"Pipeline failure — monitor agent response unparseable (run {run_id})",
            f"The pipeline_monitor_agent returned a response that could not be parsed.\n\nRun: {run_url}\n\nPlease investigate manually.",
            ["pipeline-failure", "needs-human"],
        )
        return

    action = result.get("action", "no_action")
    diagnosis = result.get("diagnosis", {})
    summary = result.get("summary", "no summary")

    print(f"[pipeline-monitor] Diagnosis: {diagnosis.get('root_cause_category', 'unknown')} — {diagnosis.get('summary', '')}")
    print(f"[pipeline-monitor] Action: {action}")

    # 5. Act on the response
    if action == "fixed":
        fixes = result.get("fixes", {})
        if fixes:
            written = apply_fixes(fixes)
            if written:
                commit_and_push(summary[:120], written)
            else:
                print("[pipeline-monitor] 'fixed' action but no files to write")
        else:
            print("[pipeline-monitor] 'fixed' action but fixes dict is empty")

    elif action == "escalated":
        issue_data = result.get("github_issue", {})
        title = issue_data.get("title", f"Pipeline failure — {diagnosis.get('summary', 'unknown error')} (run {run_id})")
        body = issue_data.get("body", f"Run: {run_url}\n\nSummary: {summary}")
        labels = issue_data.get("labels", ["pipeline-failure", "needs-human"])
        if "pipeline-failure" not in labels:
            labels.append("pipeline-failure")
        try:
            issue_url = create_github_issue(repo, title, body, labels)
            print(f"[pipeline-monitor] escalation issue created: {issue_url}")
        except Exception as e:
            print(f"[pipeline-monitor] failed to create issue: {e}")

    elif action == "handed_off":
        handoff = result.get("handoff", {})
        agent = handoff.get("agent", "unknown agent")
        context = handoff.get("context", "")
        issue_data = result.get("github_issue", {})
        title = issue_data.get("title", f"Pipeline failure — requires {agent} (run {run_id})")
        body = (
            issue_data.get("body", "")
            or f"The pipeline_monitor_agent has identified that this failure requires the **{agent}** to resolve.\n\n"
               f"**Run:** {run_url}\n\n**Context:**\n{context}\n\n**Summary:** {summary}"
        )
        labels = ["pipeline-failure", "needs-human"]
        try:
            issue_url = create_github_issue(repo, title, body, labels)
            print(f"[pipeline-monitor] handoff issue created: {issue_url}")
        except Exception as e:
            print(f"[pipeline-monitor] failed to create handoff issue: {e}")

    else:
        print(f"[pipeline-monitor] action '{action}' — no further steps taken")
        print(f"[pipeline-monitor] Summary: {summary}")

    print("[pipeline-monitor] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Monitor Agent")
    parser.add_argument("--run-id", required=True, help="GitHub Actions run ID")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    args = parser.parse_args()

    try:
        run_monitor(args.run_id, args.repo)
    except Exception as e:
        # Monitor must never fail the workflow step
        print(f"[pipeline-monitor] Unhandled error (suppressed to protect workflow): {e}")
        import traceback
        traceback.print_exc()
    sys.exit(0)
