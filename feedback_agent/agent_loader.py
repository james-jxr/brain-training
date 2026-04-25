# Loads agent system prompts and principles from the Agent Central Supabase database.
# Falls back gracefully if Supabase is not configured (e.g. local dev without creds).
import os
import time
from functools import lru_cache

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# ── Circuit breaker (issue #54) ───────────────────────────────────────────────
# Tracks consecutive Supabase failures within this process.
# After _CIRCUIT_THRESHOLD consecutive failures the circuit opens and all
# subsequent calls skip Supabase entirely until the process restarts.
_CIRCUIT_THRESHOLD = 3
_consecutive_failures = 0
_circuit_open = False


def _record_success() -> None:
    global _consecutive_failures
    _consecutive_failures = 0


def _record_failure() -> None:
    global _consecutive_failures, _circuit_open
    _consecutive_failures += 1
    if _consecutive_failures >= _CIRCUIT_THRESHOLD and not _circuit_open:
        _circuit_open = True
        print(
            "[agent_loader] Circuit open — using local fallback for all agents "
            f"(after {_consecutive_failures} consecutive failures)"
        )


def _fetch_with_retry(fn, max_attempts: int = 3, base_delay: float = 1.0):
    """Call fn() with exponential backoff. Raises on final failure."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(
                f"[agent_loader] Supabase fetch failed (attempt {attempt + 1}): {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)


@lru_cache(maxsize=None)
def get_system_prompt(agent_name: str, environment: str = "production") -> str | None:
    """
    Return the system_prompt for the named agent from Supabase.

    environment: 'production' (default) returns system_prompt.
                 'staging' returns staging_prompt if set, otherwise falls back to system_prompt.

    Returns None if Supabase is unconfigured or the agent is not found.
    Result is cached for the lifetime of the process — one DB call per agent/env pair per run.
    Retries up to 3 times with exponential backoff before falling back.
    After 3 consecutive process-level failures the circuit opens and all calls
    use the local fallback for the remainder of the process.
    """
    global _circuit_open

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(f"  [agent_loader] Supabase not configured — {agent_name} will use built-in prompt")
        return None

    if _circuit_open:
        print(
            f"[agent_loader] WARNING: using local fallback for agent '{agent_name}' "
            "— Supabase unavailable"
        )
        return None

    def _fetch():
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        return (
            client.table("agents")
            .select("system_prompt, version, staging_prompt, staging_version")
            .eq("name", agent_name)
            .eq("is_active", True)
            .single()
            .execute()
        )

    try:
        result = _fetch_with_retry(_fetch)
        _record_success()
        if not result.data:
            print(f"  [agent_loader] {agent_name} not found in Supabase — using built-in prompt")
            return None
        data = result.data
        if environment == "staging" and data.get("staging_prompt"):
            version = data.get("staging_version") or data.get("version", "?")
            print(f"  [agent_loader] loaded {agent_name} v{version} (staging) from Supabase")
            return data["staging_prompt"]
        version = data.get("version", "?")
        print(f"  [agent_loader] loaded {agent_name} v{version} from Supabase")
        return data["system_prompt"]
    except Exception as e:
        _record_failure()
        print(
            f"[agent_loader] WARNING: using local fallback for agent '{agent_name}' "
            f"— Supabase unavailable ({e})"
        )
        return None


@lru_cache(maxsize=None)
def get_principles(categories: tuple[str, ...] | None = None) -> str:
    """
    Return active principles from Supabase as a formatted markdown string.
    Pass categories as a tuple to filter, e.g. ('code_quality', 'testing').
    Pass None (default) to fetch all active principles.
    Returns an empty string if Supabase is unconfigured or no principles found.
    Result is cached for the lifetime of the process.
    Retries up to 3 times with exponential backoff before falling back.
    """
    global _circuit_open

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return ""

    if _circuit_open:
        print("[agent_loader] WARNING: using local fallback for principles — Supabase unavailable")
        return ""

    def _fetch():
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        query = client.table("principles").select("title, category, content").eq("is_active", True)
        if categories:
            query = query.in_("category", list(categories))
        return query.order("category").execute()

    try:
        result = _fetch_with_retry(_fetch)
        _record_success()
        if not result.data:
            return ""

        # Format as a single markdown block grouped by category
        by_category: dict[str, list] = {}
        for p in result.data:
            by_category.setdefault(p["category"], []).append(p)

        lines = ["## Development Principles\n"]
        for cat, items in by_category.items():
            cat_label = cat.replace("_", " ").title()
            for item in items:
                lines.append(f"### {cat_label}: {item['title']}\n")
                lines.append(item["content"].strip())
                lines.append("")

        principles_text = "\n".join(lines).strip()
        print(f"  [agent_loader] loaded {len(result.data)} principle(s) from Supabase")
        return principles_text
    except Exception as e:
        _record_failure()
        print(
            f"[agent_loader] WARNING: using local fallback for principles "
            f"— Supabase unavailable ({e})"
        )
        return ""


def update_system_prompt(agent_name: str, new_prompt: str, new_version: str) -> bool:
    """
    Update an agent's system_prompt and version in Supabase.
    Returns True on success.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(f"  [agent_loader] Supabase not configured — cannot update {agent_name}")
        return False

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        client.table("agents").update({
            "system_prompt": new_prompt,
            "version": new_version,
        }).eq("name", agent_name).execute()
        # Clear the cache so the next call picks up the new prompt
        get_system_prompt.cache_clear()
        print(f"  [agent_loader] updated {agent_name} to v{new_version} in Supabase")
        return True
    except Exception as e:
        print(f"  [agent_loader] failed to update {agent_name}: {e}")
        return False
