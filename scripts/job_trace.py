#!/usr/bin/env python3
"""
Inspect job lifecycle details from local JSON cache.
"""

import json
import sys
from pathlib import Path

AIRILAB_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIRILAB_PATH))

from core.job_store import EVENTS_LOG_FILE, JOBS_FILE, get_job, get_job_events, init_db  # noqa: E402


def get_job_trace(job_id: str, limit: int) -> dict:
    init_db()
    job = get_job(job_id)
    if not job:
        return {"success": False, "message": f"job not found: {job_id}", "jobs_file": str(JOBS_FILE)}

    events = get_job_events(job_id, limit=max(limit, 1))
    return {
        "success": True,
        "jobs_file": str(JOBS_FILE),
        "events_file": str(EVENTS_LOG_FILE),
        "job": job,
        "events": events,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspect one local AiriLab job trace")
    parser.add_argument("--job-id", required=True, help="Job ID to inspect")
    parser.add_argument("--limit", type=int, default=50, help="Max number of recent events")
    args = parser.parse_args()

    result = get_job_trace(args.job_id, max(args.limit, 1))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success") else 1)

