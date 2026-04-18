# Loads agent system prompts from the Agent Central Supabase database.
# Falls back gracefully if Supabase is not configured (e.g. local dev without creds).
import os
from functools import lru_cache

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


@lru_cache(maxsize=None)
def get_system_prompt(agent_name: str) -> str | None:
    """
    Return the system_prompt for the named agent from Supabase.
    Returns None if Supabase is unconfigured or the agent is not found.
    Result is cached for the lifetime of the process — one DB call per agent per run.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(f"  [agent-loader] Supabase not configured — {agent_name} will use built-in prompt")
        return None

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        result = (
            client.table("agents")
            .select("system_prompt, version")
            .eq("name", agent_name)
            .eq("is_active", True)
            .single()
            .execute()
        )
        if result.data:
            version = result.data.get("version", "?")
            print(f"  [agent-loader] loaded {agent_name} v{version} from Supabase")
            return result.data["system_prompt"]
        print(f"  [agent-loader] {agent_name} not found in Supabase — using built-in prompt")
        return None
    except Exception as e:
        print(f"  [agent-loader] could not fetch {agent_name}: {e}")
        return None


@lru_cache(maxsize=None)
def get_principles(categories: tuple[str, ...] | None = None) -> str:
    """
    Return active principles from Supabase as a formatted markdown string.
    Pass categories as a tuple to filter, e.g. ('code_quality', 'testing').
    Pass None (default) to fetch all active principles.
    Returns an empty string if Supabase is unconfigured or no principles found.
    Result is cached for the lifetime of the process.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return ""

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        query = client.table("principles").select("title, category, content").eq("is_active", True)
        if categories:
            query = query.in_("category", list(categories))
        result = query.order("category").execute()
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
        print(f"  [agent-loader] loaded {len(result.data)} principle(s) from Supabase")
        return principles_text
    except Exception as e:
        print(f"  [agent-loader] could not fetch principles: {e}")
        return ""


def update_system_prompt(agent_name: str, new_prompt: str, new_version: str) -> bool:
    """
    Update an agent's system_prompt and version in Supabase.
    Returns True on success.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print(f"  [agent-loader] Supabase not configured — cannot update {agent_name}")
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
        print(f"  [agent-loader] updated {agent_name} to v{new_version} in Supabase")
        return True
    except Exception as e:
        print(f"  [agent-loader] failed to update {agent_name}: {e}")
        return False
