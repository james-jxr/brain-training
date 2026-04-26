# Database helpers for the feedback agent pipeline.
import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone


def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    return psycopg2.connect(url)


def fetch_unprocessed_feedback(conn, project_id: str):
    """
    Return unprocessed feedback entries for the given project.
    Filters by project_id so each project's review pipeline only processes
    its own feedback. Returns [] if conn is None, the table doesn't exist,
    or any other DB error.
    """
    if conn is None:
        print("  [db] DATABASE_URL not set — skipping feedback fetch")
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, page_context, feedback_text, created_at
                FROM feedback_entries
                WHERE processed_at IS NULL AND project_id = %s
                ORDER BY created_at ASC
            """, (project_id,))
            return cur.fetchall()
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        print("  [db] WARNING: feedback_entries table does not exist — skipping feedback")
        return []
    except Exception as e:
        conn.rollback()
        print(f"  [db] WARNING: could not fetch feedback: {e}")
        return []


def mark_feedback_processed(conn, ids):
    """Set processed_at = now() for all given IDs."""
    if not ids or conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE feedback_entries SET processed_at = %s WHERE id = ANY(%s)",
                (datetime.now(timezone.utc), ids)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"  [db] WARNING: could not mark feedback processed: {e}")


def insert_feedback_run(conn, run: dict):
    """Insert a row into feedback_runs and return the new ID."""
    import json
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO feedback_runs
                (run_at, feedback_count, themes, changes_applied, branch_name, pr_url, status, error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            run.get("run_at", datetime.now(timezone.utc)),
            run.get("feedback_count", 0),
            json.dumps(run.get("themes")) if run.get("themes") else None,
            json.dumps(run.get("changes_applied")) if run.get("changes_applied") else None,
            run.get("branch_name"),
            run.get("pr_url"),
            run.get("status", "pending"),
            run.get("error"),
        ))
        row_id = cur.fetchone()[0]
    conn.commit()
    return row_id


def update_feedback_run(conn, run_id: int, updates: dict):
    """Patch fields on an existing feedback_runs row."""
    import json
    fields = []
    values = []
    for key, val in updates.items():
        fields.append(f"{key} = %s")
        if key in ("themes", "changes_applied") and val is not None:
            values.append(json.dumps(val))
        else:
            values.append(val)
    values.append(run_id)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE feedback_runs SET {', '.join(fields)} WHERE id = %s",
            values
        )
    conn.commit()


def mark_findings_resolved(conn, finding_ids: list[str], table: str):
    """Mark a list of Supabase finding rows as resolved via direct psycopg2."""
    # Note: in v2, _mark_findings_resolved() in pipeline.py handles this via
    # Supabase REST rather than PostgreSQL, so this function is a no-op stub
    # kept for import compatibility.
    pass
