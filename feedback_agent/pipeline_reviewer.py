# Weekly pipeline self-review: analyses recent run history and improves agent prompts.
# Reads feedback_agent and build_agent prompts from Supabase; writes improvements back.
import anthropic
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from feedback_agent.json_utils import extract_json
from feedback_agent.agent_loader import get_system_prompt, update_system_prompt


def _fetch_run_history(conn, limit: int = 7) -> list:
    """Fetch the last N feedback_runs records."""
    import psycopg2.extras
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT id, run_at, feedback_count, themes, changes_applied,
                   branch_name, pr_url, status, error
            FROM feedback_runs
            ORDER BY run_at DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()


def _format_run_history(runs: list) -> str:
    parts = []
    for run in runs:
        themes = run.get("themes") or []
        applied = run.get("changes_applied") or []
        parts.append(
            f"Run {run['id']} — {run['run_at']} — status: {run['status']}\n"
            f"  Feedback count: {run['feedback_count']}\n"
            f"  Items synthesised: {len(themes)}\n"
            f"  Items applied: {len(applied)} ({', '.join(c['id'] for c in applied) or 'none'})\n"
            f"  PR: {run['pr_url'] or 'none'}\n"
            f"  Error: {(run['error'] or '')[:300] or 'none'}"
        )
    return "\n\n".join(parts)


_REVIEW_SYSTEM_PROMPT = """You are reviewing the effectiveness of an autonomous feedback pipeline for a brain training web app.

The pipeline runs nightly and:
1. Synthesises user feedback into structured change items (feedback_agent)
2. Implements clear items autonomously — writes code (build_agent)
3. Runs tests with auto-fix loop (testing_agent)
4. Updates spec and run log, opens a PR

You will be given the recent run history and the current system prompts for the feedback_agent and build_agent.

Analyse the run history and identify patterns indicating the pipeline is underperforming. Focus on:
1. Synthesis quality — items misclassified, incorrectly marked non-implementable, or repeatedly re-appearing
2. Implementation quality — recurring file-not-found errors, JSON parse errors, reverted changes
3. Test failures — same failure recurring, auto-fix loop exhausting iterations
4. False negatives — feedback that keeps reappearing suggests previous implementations didn't fix the issue

Based on your analysis, suggest specific, targeted improvements to the feedback_agent or build_agent system prompts.
If no improvements are warranted, say so explicitly.

Return a JSON object:
{
  "analysis": "2-3 sentence summary of what you found",
  "improvements_needed": true or false,
  "prompt_updates": {
    "feedback_agent": "complete updated system prompt content, or null if no change",
    "build_agent": "complete updated system prompt content, or null if no change"
  },
  "summary": "one-line description of changes made (for the run log)"
}"""


def _next_version(current: str) -> str:
    """Increment the patch version of a semver string. e.g. '1.0.3' → '1.0.4'."""
    try:
        parts = current.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    except Exception:
        return current + ".1"


def review_and_improve(conn) -> dict:
    """
    Fetch run history, ask Claude to review, update agent prompts in Supabase if improvements found.
    Returns summary dict.
    """
    print("  [review] fetching run history...")
    runs = _fetch_run_history(conn)

    if len(runs) < 2:
        print("  [review] not enough run history yet (need at least 2 runs)")
        return {"improvements_needed": False, "analysis": "insufficient run history"}

    run_history = _format_run_history(runs)

    # Load current prompts from Supabase (or note if unavailable)
    feedback_prompt = get_system_prompt("feedback_agent") or "(not loaded — Supabase unavailable)"
    build_prompt = get_system_prompt("build_agent") or "(not loaded — Supabase unavailable)"

    user_message = f"""## Recent pipeline runs (last {len(runs)})

{run_history}

## Current agent system prompts

### feedback_agent
{feedback_prompt}

### build_agent
{build_prompt}"""

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=_REVIEW_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    result = extract_json(message.content[0].text)
    print(f"  [review] analysis: {result.get('analysis', '')}")

    if not result.get("improvements_needed"):
        print("  [review] no improvements needed this week")
        return result

    updates = result.get("prompt_updates", {})
    updated_agents = []

    for agent_name in ("feedback_agent", "build_agent"):
        new_prompt = updates.get(agent_name)
        if not new_prompt:
            continue

        # Fetch current version to compute next
        from feedback_agent.agent_loader import SUPABASE_URL, SUPABASE_SERVICE_KEY
        current_version = "1.0.0"
        if SUPABASE_URL and SUPABASE_SERVICE_KEY:
            try:
                from supabase import create_client
                client_sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
                r = client_sb.table("agents").select("version").eq("name", agent_name).single().execute()
                if r.data:
                    current_version = r.data.get("version", "1.0.0")
            except Exception:
                pass

        new_version = _next_version(current_version)
        if update_system_prompt(agent_name, new_prompt, new_version):
            updated_agents.append(agent_name)

    result["updated_agents"] = updated_agents
    return result
