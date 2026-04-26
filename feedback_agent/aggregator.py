# Aggregation stage: reads all issue sources for a project and returns a
# unified, priority-sorted list ready for the pipeline to act on.
#
# Sources (in priority order):
#   1. code_audit_findings (Supabase) — high severity
#   2. code_audit_findings (Supabase) — medium severity
#   3. coordination_findings (Supabase) — auto_fixable=True
#   4. feedback_entries (PostgreSQL) — unprocessed user feedback
#   5. coordination_findings (Supabase) — auto_fixable=False
#   6. code_audit_findings (Supabase) — low severity
#
# Audit and coordination items are already structured — they bypass the
# Claude synthesis call in the synthesizer.  Feedback items go through it.
#
# Findings where last_attempted_at is within the last RETRY_HOLD_HOURS hours
# are skipped to avoid hammering items that consistently fail to implement.

from __future__ import annotations

import os
import requests
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

RETRY_HOLD_HOURS = 23  # skip a finding if it was attempted this recently

# Priority rank — lower number = higher priority
_PRIORITY_RANK: dict[tuple[str, str | bool], int] = {
    ("audit",        "high"):  1,
    ("audit",        "medium"): 2,
    ("coordination", True):    3,   # key is (source, auto_fixable)
    ("feedback",     None):    4,
    ("coordination", False):   5,
    ("audit",        "low"):   6,
}


def _rank(item: "AggregatedItem") -> int:
    if item.source == "audit":
        return _PRIORITY_RANK.get(("audit", item.priority), 99)
    if item.source == "coordination":
        return _PRIORITY_RANK.get(("coordination", item.auto_fixable), 99)
    return _PRIORITY_RANK.get(("feedback", None), 99)


@dataclass
class AggregatedItem:
    source: str                  # "audit" | "coordination" | "feedback"
    supabase_id: str | None      # UUID — set for audit/coordination rows
    priority: str                # "high" | "medium" | "low"
    title: str
    description: str
    file_path: str | None
    auto_fixable: bool
    route_to: str | None         # build_agent | functional_design_agent | etc.
    raw: dict                    # original DB row, preserved for callers


@dataclass
class AggregationResult:
    """All work items for one pipeline run, in priority order."""
    items: list[AggregatedItem] = field(default_factory=list)

    @property
    def feedback_rows(self) -> list[dict]:
        """Raw PostgreSQL feedback_entries rows (needed by mark_feedback_processed)."""
        return [i.raw for i in self.items if i.source == "feedback"]

    @property
    def audit_ids(self) -> list[str]:
        """Supabase UUIDs for code_audit_findings (needed by mark_findings_resolved)."""
        return [i.supabase_id for i in self.items if i.source == "audit" and i.supabase_id]

    @property
    def coordination_ids(self) -> list[str]:
        """Supabase UUIDs for coordination_findings (needed by mark_findings_resolved)."""
        return [i.supabase_id for i in self.items if i.source == "coordination" and i.supabase_id]


# ── Supabase helpers ───────────────────────────────────────────────────────────

def _sb_get(supabase_url: str, supabase_key: str, table: str, params: dict) -> list[dict]:
    """GET rows from a Supabase REST table with query params."""
    resp = requests.get(
        f"{supabase_url}/rest/v1/{table}",
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Accept": "application/json",
        },
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _is_recently_attempted(row: dict) -> bool:
    """Return True if last_attempted_at is within RETRY_HOLD_HOURS."""
    ts = row.get("last_attempted_at")
    if not ts:
        return False
    try:
        attempted = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - attempted < timedelta(hours=RETRY_HOLD_HOURS)
    except (ValueError, TypeError):
        return False


# ── Source fetchers ────────────────────────────────────────────────────────────

def _fetch_audit_findings(
    supabase_url: str, supabase_key: str, project_id: str
) -> list[AggregatedItem]:
    rows = _sb_get(supabase_url, supabase_key, "code_audit_findings", {
        "project_id": f"eq.{project_id}",
        "resolved": "eq.false",
        "select": "id,finding_type,severity,description,file_path,last_attempted_at",
        "order": "created_at.asc",
    })
    items = []
    for row in rows:
        if _is_recently_attempted(row):
            print(f"  [aggregator] skipping audit finding {row['id']} (attempted recently)")
            continue
        severity = row.get("severity") or "low"
        finding_type = row.get("finding_type") or "code_quality"
        title = f"[audit/{severity}] {finding_type}: {(row.get('description') or '')[:80]}"
        items.append(AggregatedItem(
            source="audit",
            supabase_id=row["id"],
            priority=severity,
            title=title,
            description=row.get("description") or "",
            file_path=row.get("file_path"),
            auto_fixable=True,   # audit findings are always routed to build_agent
            route_to="build_agent",
            raw=row,
        ))
    return items


def _fetch_coordination_findings(
    supabase_url: str, supabase_key: str, project_id: str
) -> list[AggregatedItem]:
    rows = _sb_get(supabase_url, supabase_key, "coordination_findings", {
        "project_id": f"eq.{project_id}",
        "resolved": "eq.false",
        "select": "id,finding_type,severity,description,artifact_a,artifact_b,auto_fixable,route_to,last_attempted_at",
        "order": "created_at.asc",
    })
    items = []
    for row in rows:
        if _is_recently_attempted(row):
            print(f"  [aggregator] skipping coordination finding {row['id']} (attempted recently)")
            continue
        severity = row.get("severity") or "medium"
        finding_type = row.get("finding_type") or "coordination"
        auto_fixable = bool(row.get("auto_fixable", False))
        artifact_note = ""
        if row.get("artifact_a") or row.get("artifact_b"):
            artifact_note = f" ({row.get('artifact_a', '?')} ↔ {row.get('artifact_b', '?')})"
        title = f"[coord/{finding_type}]{artifact_note}: {(row.get('description') or '')[:80]}"
        items.append(AggregatedItem(
            source="coordination",
            supabase_id=row["id"],
            priority=severity,
            title=title,
            description=row.get("description") or "",
            file_path=row.get("artifact_b"),   # artifact_b is typically what needs fixing
            auto_fixable=auto_fixable,
            route_to=row.get("route_to") or "build_agent",
            raw=row,
        ))
    return items


def _fetch_feedback(conn: Any) -> list[AggregatedItem]:
    """Fetch unprocessed feedback_entries from PostgreSQL."""
    import psycopg2.extras
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT id, page_context, feedback_text, created_at
            FROM feedback_entries
            WHERE processed_at IS NULL
            ORDER BY created_at ASC
        """)
        rows = cur.fetchall()

    items = []
    for row in rows:
        row = dict(row)
        title = f"[feedback] {row.get('page_context', '')}: {(row.get('feedback_text') or '')[:80]}"
        items.append(AggregatedItem(
            source="feedback",
            supabase_id=None,
            priority="medium",   # feedback priority is determined by synthesizer
            title=title,
            description=row.get("feedback_text") or "",
            file_path=None,
            auto_fixable=True,
            route_to=None,
            raw=row,
        ))
    return items


# ── Public API ─────────────────────────────────────────────────────────────────

def aggregate(
    project_id: str,
    supabase_url: str,
    supabase_key: str,
    db_conn: Any,
) -> AggregationResult:
    """
    Fetch and merge all issue sources for project_id.
    Returns an AggregationResult with items sorted by priority.

    Args:
        project_id:    e.g. "brain-training"
        supabase_url:  SUPABASE_URL env var
        supabase_key:  SUPABASE_SERVICE_KEY env var
        db_conn:       open psycopg2 connection to the project PostgreSQL DB
    """
    print(f"  [aggregator] fetching sources for project: {project_id}")

    audit_items: list[AggregatedItem] = []
    coordination_items: list[AggregatedItem] = []
    feedback_items: list[AggregatedItem] = []

    # Audit findings (Supabase)
    try:
        audit_items = _fetch_audit_findings(supabase_url, supabase_key, project_id)
        print(f"  [aggregator] audit findings: {len(audit_items)}")
    except Exception as e:
        print(f"  [aggregator] WARNING: could not fetch audit findings: {e}")

    # Coordination findings (Supabase)
    try:
        coordination_items = _fetch_coordination_findings(supabase_url, supabase_key, project_id)
        print(f"  [aggregator] coordination findings: {len(coordination_items)}")
    except Exception as e:
        print(f"  [aggregator] WARNING: could not fetch coordination findings: {e}")

    # User feedback (PostgreSQL)
    try:
        feedback_items = _fetch_feedback(db_conn)
        print(f"  [aggregator] feedback entries: {len(feedback_items)}")
    except Exception as e:
        print(f"  [aggregator] WARNING: could not fetch feedback entries: {e}")

    all_items = audit_items + coordination_items + feedback_items
    all_items.sort(key=_rank)

    total = len(all_items)
    print(f"  [aggregator] total items: {total} "
          f"(audit={len(audit_items)}, coord={len(coordination_items)}, feedback={len(feedback_items)})")

    return AggregationResult(items=all_items)
