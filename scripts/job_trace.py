#!/usr/bin/env python3
"""
Inspect job lifecycle details from local runtime store.
"""

import json
import sqlite3
import sys
from pathlib import Path

AIRILAB_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIRILAB_PATH))

from core.paths import get_scheduler_dir  # noqa: E402

DB_PATH = get_scheduler_dir() / "jobs.db"


def get_job_trace(job_id: str, limit: int) -> dict:
    if not DB_PATH.exists():
        return {"success": False, "message": f"jobs.db not found: {DB_PATH}"}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    job = cursor.fetchone()
    if not job:
        conn.close()
        return {"success": False, "message": f"job not found: {job_id}"}

    try:
        cursor.execute(
            """
            SELECT event_at, event_type, level, message, details
            FROM job_events
            WHERE job_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (job_id, limit),
        )
        events = cursor.fetchall()
    except sqlite3.OperationalError:
        events = []
    conn.close()

    formatted_events = []
    for event in reversed(events):
        details_raw = event["details"]
        if details_raw:
            try:
                details = json.loads(details_raw)
            except json.JSONDecodeError:
                details = {"raw": details_raw}
        else:
            details = {}
        formatted_events.append(
            {
                "event_at": event["event_at"],
                "event_type": event["event_type"],
                "level": event["level"],
                "message": event["message"],
                "details": details,
            }
        )

    job_data = dict(job)
    if job_data.get("input_params"):
        try:
            job_data["input_params"] = json.loads(job_data["input_params"])
        except json.JSONDecodeError:
            pass
    if job_data.get("output_url"):
        try:
            job_data["output_url"] = json.loads(job_data["output_url"])
        except json.JSONDecodeError:
            pass

    return {"success": True, "job": job_data, "events": formatted_events}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect one local AiriLab job trace")
    parser.add_argument("--job-id", required=True, help="Job ID to inspect")
    parser.add_argument("--limit", type=int, default=50, help="Max number of recent events")
    args = parser.parse_args()

    result = get_job_trace(args.job_id, max(args.limit, 1))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)
