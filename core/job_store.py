#!/usr/bin/env python3
"""
JSON-based job persistence helpers for submitter and worker.
"""

import json
import os
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .paths import ensure_runtime_dirs, get_scheduler_dir
except ImportError:  # pragma: no cover
    from paths import ensure_runtime_dirs, get_scheduler_dir

ensure_runtime_dirs()

SCHEDULER_DIR = get_scheduler_dir()
JOBS_FILE = SCHEDULER_DIR / "jobs.json"
EVENTS_LOG_FILE = SCHEDULER_DIR / "job_events.jsonl"
LOCK_FILE = SCHEDULER_DIR / ".jobs.lock"

STATUS_PENDING = "pending"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
TRACKED_STATUSES = {STATUS_PENDING, STATUS_PROCESSING, STATUS_COMPLETED, STATUS_FAILED}


def _now_iso() -> str:
    return datetime.now().isoformat()


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


@contextmanager
def _store_lock(timeout_seconds: float = 5.0):
    deadline = time.time() + timeout_seconds
    while True:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.time() > deadline:
                raise TimeoutError(f"timed out acquiring lock: {LOCK_FILE}")
            time.sleep(0.05)

    try:
        yield
    finally:
        try:
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
        except Exception:
            pass


def _read_jobs_unlocked() -> List[Dict[str, Any]]:
    if not JOBS_FILE.exists():
        return []
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_jobs_unlocked(jobs: List[Dict[str, Any]]) -> None:
    _write_json_atomic(JOBS_FILE, jobs)


def init_db() -> None:
    """
    Backward-compatible initializer name. Uses JSON store only.
    """
    with _store_lock():
        if not JOBS_FILE.exists():
            _write_jobs_unlocked([])
        EVENTS_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        EVENTS_LOG_FILE.touch(exist_ok=True)


def save_job(job_id: str, user_id: str, chat_id: str, tool: str, input_params: Dict[str, Any]) -> None:
    record = {
        "job_id": str(job_id),
        "user_id": str(user_id),
        "chat_id": str(chat_id),
        "tool": str(tool),
        "status": STATUS_PENDING,
        "submitted_at": _now_iso(),
        "started_at": None,
        "completed_at": None,
        "input_params": input_params,
        "output_url": None,
        "thumbnail_url": None,
        "error_message": None,
        "attempts": 0,
    }

    with _store_lock():
        jobs = _read_jobs_unlocked()
        replaced = False
        for idx, job in enumerate(jobs):
            if str(job.get("job_id", "")) == record["job_id"]:
                jobs[idx] = record
                replaced = True
                break
        if not replaced:
            jobs.append(record)
        _write_jobs_unlocked(jobs)


def get_pending_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    with _store_lock():
        jobs = _read_jobs_unlocked()

    filtered = [
        job
        for job in jobs
        if str(job.get("status", "")).lower() in {STATUS_PENDING, STATUS_PROCESSING}
    ]
    filtered.sort(key=lambda item: str(item.get("submitted_at") or ""))
    return filtered[: max(limit, 1)]


def update_job_status(
    job_id: str,
    status: str,
    output_url: Optional[Any] = None,
    thumbnail_url: Optional[str] = None,
    error_message: Optional[str] = None,
) -> bool:
    now = _now_iso()
    with _store_lock():
        jobs = _read_jobs_unlocked()
        updated = False
        for job in jobs:
            if str(job.get("job_id", "")) != str(job_id):
                continue

            normalized_status = str(status).lower()
            job["status"] = normalized_status
            if normalized_status == STATUS_COMPLETED:
                job["completed_at"] = now
                job["output_url"] = output_url
                job["thumbnail_url"] = thumbnail_url
                job["error_message"] = None
            elif normalized_status == STATUS_FAILED:
                job["completed_at"] = now
                job["error_message"] = error_message
            else:
                job["attempts"] = int(job.get("attempts") or 0) + 1
            updated = True
            break

        if updated:
            _write_jobs_unlocked(jobs)
        return updated


def append_job_event(
    job_id: str,
    event_type: str,
    message: str,
    level: str = "info",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    event = {
        "event_at": _now_iso(),
        "job_id": str(job_id),
        "event_type": str(event_type),
        "level": str(level),
        "message": str(message),
        "details": details or {},
    }
    with open(EVENTS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _store_lock():
        jobs = _read_jobs_unlocked()
    for job in jobs:
        if str(job.get("job_id", "")) == str(job_id):
            return job
    return None


def get_job_events(job_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    if not EVENTS_LOG_FILE.exists():
        return []

    target = str(job_id)
    tail: deque = deque(maxlen=max(limit, 1))
    with open(EVENTS_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                continue
            if str(event.get("job_id", "")) == target:
                tail.append(event)
    return list(tail)


def get_job_counts() -> Dict[str, int]:
    counts = {
        STATUS_PENDING: 0,
        STATUS_PROCESSING: 0,
        STATUS_COMPLETED: 0,
        STATUS_FAILED: 0,
        "total": 0,
    }
    with _store_lock():
        jobs = _read_jobs_unlocked()

    for job in jobs:
        status = str(job.get("status", "")).lower()
        if status in TRACKED_STATUSES:
            counts[status] += 1
        counts["total"] += 1
    return counts
