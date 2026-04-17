#!/usr/bin/env python3
"""
fetch-feedback.py — Brain Training App, Mac-side data bridge

Run this script on your Mac to export feedback from the local backend
into a file that the daily pipeline can read from the sandbox.

Usage (from the apps/brain-training/ directory):
    python fetch-feedback.py

Or from the project root:
    python apps/brain-training/fetch-feedback.py

The script writes feedback-export.json next to itself. The daily pipeline
picks that file up on its next run and deletes it after processing.
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

BACKEND_URL = "http://localhost:8000/api/feedback"
OUTPUT_FILE = Path(__file__).parent / "feedback-export.json"


def main():
    print(f"[fetch-feedback] Fetching from {BACKEND_URL} ...")

    try:
        with urllib.request.urlopen(BACKEND_URL, timeout=10) as response:
            if response.status != 200:
                print(f"[fetch-feedback] ERROR: backend returned HTTP {response.status}")
                sys.exit(1)
            raw = response.read()
    except urllib.error.URLError as exc:
        print(f"[fetch-feedback] ERROR: could not reach backend — {exc.reason}")
        print("  Make sure the backend is running:")
        print('  DATABASE_URL="sqlite:////tmp/brain_training.db" python -m uvicorn backend.main:app --reload')
        sys.exit(1)

    data = json.loads(raw)
    total = data.get("total", "?")
    print(f"[fetch-feedback] Got {total} feedback entries from backend.")

    # Stamp the export so the pipeline knows when it was created
    data["_exported_at"] = datetime.now(timezone.utc).isoformat()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[fetch-feedback] Written to {OUTPUT_FILE}")
    print("[fetch-feedback] You can now trigger the daily pipeline — it will pick up this file.")


if __name__ == "__main__":
    main()
