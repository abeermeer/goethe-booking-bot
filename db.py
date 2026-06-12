"""
Database persistence layer (SQLite).
Stores students, results, logs persistently.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
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


init_db()
