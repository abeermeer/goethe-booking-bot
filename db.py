"""
Database persistence layer (SQLite).
Stores students, results, logs persistently.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent / "bot_data.db"
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            level TEXT,
            city TEXT,
            booking_datetime TEXT,
            status TEXT DEFAULT 'pending',
            result_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_key TEXT,
            level TEXT,
            message TEXT,
            time TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS bot_state (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS queue_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            level TEXT,
            city TEXT,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            queued_at TEXT DEFAULT (datetime('now')),
            started_at TEXT,
            finished_at TEXT,
            result_json TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            email TEXT,
            details TEXT,
            ip TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()


def save_students(students: List[Dict[str, str]]):
    conn = _get_conn()
    conn.execute("DELETE FROM students")
    for s in students:
        conn.execute(
            "INSERT INTO students (name, email, level, city, booking_datetime, status) VALUES (?, ?, ?, ?, ?, ?)",
            (s.get("name", ""), s.get("email", ""), s.get("level", s.get("exam_level", "")), s.get("city", ""), s.get("booking_datetime", ""), "pending"),
        )
    conn.commit()


def get_students() -> List[Dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def update_student_status(student_key: str, status: str, result: Optional[Dict] = None):
    conn = _get_conn()
    conn.execute(
        "UPDATE students SET status = ?, result_json = ?, updated_at = datetime('now') WHERE name || '|' || level || '|' || city = ?",
        (status, json.dumps(result) if result else None, student_key),
    )
    conn.commit()


def add_log(student_key: str, level: str, message: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO logs (student_key, level, message) VALUES (?, ?, ?)",
        (student_key, level, message),
    )
    conn.commit()


def get_logs(student_key: Optional[str] = None, limit: int = 200) -> List[Dict]:
    conn = _get_conn()
    if student_key:
        rows = conn.execute("SELECT * FROM logs WHERE student_key = ? ORDER BY id DESC LIMIT ?", (student_key, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def set_state(key: str, value: str):
    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)", (key, value))
    conn.commit()


def get_state(key: str, default: str = "") -> str:
    conn = _get_conn()
    row = conn.execute("SELECT value FROM bot_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def delete_state(key: str):
    conn = _get_conn()
    conn.execute("DELETE FROM bot_state WHERE key = ?", (key,))
    conn.commit()


def save_checkpoint(student_key: str, step: int):
    set_state(f"checkpoint_{student_key}", str(step))


def get_checkpoint(student_key: str) -> int:
    val = get_state(f"checkpoint_{student_key}", "0")
    try:
        return int(val)
    except ValueError:
        return 0


def clear_checkpoint(student_key: str):
    delete_state(f"checkpoint_{student_key}")


def clear_all_checkpoints():
    conn = _get_conn()
    conn.execute("DELETE FROM bot_state WHERE key LIKE 'checkpoint_%'")
    conn.commit()


def add_to_queue(name: str, email: str, level: str, city: str, priority: int = 0):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO queue_history (name, email, level, city, status, priority) VALUES (?, ?, ?, ?, 'pending', ?)",
        (name, email, level, city, priority),
    )
    conn.commit()


def get_queue(status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = _get_conn()
    if status:
        rows = conn.execute("SELECT * FROM queue_history WHERE status = ? ORDER BY priority DESC, id ASC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM queue_history ORDER BY priority DESC, id ASC").fetchall()
    return [dict(r) for r in rows]


def update_queue_item(item_id: int, status: str, result: Optional[Dict] = None):
    conn = _get_conn()
    if status == "in_progress":
        conn.execute("UPDATE queue_history SET status = ?, started_at = datetime('now') WHERE id = ?", (status, item_id))
    elif status in ("completed", "failed"):
        conn.execute(
            "UPDATE queue_history SET status = ?, finished_at = datetime('now'), result_json = ? WHERE id = ?",
            (status, json.dumps(result) if result else None, item_id),
        )
    else:
        conn.execute("UPDATE queue_history SET status = ? WHERE id = ?", (status, item_id))
    conn.commit()


def delete_queue_item(item_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM queue_history WHERE id = ?", (item_id,))
    conn.commit()


def clear_queue():
    conn = _get_conn()
    conn.execute("DELETE FROM queue_history")
    conn.commit()


def create_session(email: str, expiry_hours: int = 24) -> str:
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    session_id = secrets.token_urlsafe(48)
    conn.execute(
        "INSERT INTO sessions (session_id, email, expires_at) VALUES (?, ?, datetime('now', '+{} hours'))".format(expiry_hours),
        (session_id, email),
    )
    conn.commit()
    return session_id


def validate_session(session_id: str) -> Optional[str]:
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    conn.commit()
    row = conn.execute(
        "SELECT email FROM sessions WHERE session_id = ? AND expires_at >= datetime('now')",
        (session_id,),
    ).fetchone()
    return row["email"] if row else None


def delete_session(session_id: str):
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()


def clean_expired_sessions():
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    conn.commit()


def add_audit_log(action: str, email: str = "", details: str = "", ip: str = ""):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO audit_log (action, email, details, ip) VALUES (?, ?, ?, ?)",
        (action, email, details, ip),
    )
    conn.commit()


def get_audit_logs(limit: int = 100) -> List[Dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


init_db()
