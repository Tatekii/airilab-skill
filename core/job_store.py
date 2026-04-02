#!/usr/bin/env python3
"""
Shared job persistence helpers for submitter and worker.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from .paths import ensure_runtime_dirs, get_scheduler_dir

ensure_runtime_dirs()

SCHEDULER_DIR = get_scheduler_dir()
DB_PATH = SCHEDULER_DIR / "jobs.db"
EVENTS_LOG_FILE = SCHEDULER_DIR / "job_events.log"

STATUS_PENDING = "pending"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            tool TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            submitted_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            input_params TEXT,
            output_url TEXT,
            thumbnail_url TEXT,
            error_message TEXT,
            attempts INTEGER DEFAULT 0
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user ON jobs(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submitted ON jobs(submitted_at)")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS job_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            event_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_events_job ON job_events(job_id, id)")
    conn.commit()
    conn.close()


def save_job(job_id: str, user_id: str, chat_id: str, tool: str, input_params: Dict[str, Any]) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO jobs
        (job_id, user_id, chat_id, tool, status, submitted_at, input_params)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            user_id,
            chat_id,
            tool,
            STATUS_PENDING,
            datetime.now().isoformat(),
            json.dumps(input_params, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def append_job_event(
    job_id: str,
    event_type: str,
    message: str,
    level: str = "info",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    event_at = datetime.now().isoformat()
    details_json = json.dumps(details, ensure_ascii=False) if details else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO job_events (job_id, event_at, event_type, level, message, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (job_id, event_at, event_type, level, message, details_json),
    )
    conn.commit()
    conn.close()

    EVENTS_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "event_at": event_at,
        "job_id": job_id,
        "event_type": event_type,
        "level": level,
        "message": message,
        "details": details or {},
    }
    with open(EVENTS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

