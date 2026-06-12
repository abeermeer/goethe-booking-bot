import gc
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import db as _db

_original_path = _db.DB_PATH


import gc


def setup_function():
    _db.DB_PATH = Path(tempfile.mkstemp(suffix=".db")[1])
    _db.init_db()


def teardown_function():
    import sqlite3
    try:
        conn = _db._get_conn()
        conn.close()
    except Exception:
        pass
    _db._local.conn = None
    gc.collect()
    if _db.DB_PATH.exists():
        try:
            _db.DB_PATH.unlink()
        except PermissionError:
            pass
    _db.DB_PATH = _original_path


def test_init_db():
    assert _db.get_state("test_key", "not_found") == "not_found"


def test_set_and_get_state():
    _db.set_state("test_key", "test_value")
    assert _db.get_state("test_key") == "test_value"


def test_delete_state():
    _db.set_state("test_key", "test_value")
    _db.delete_state("test_key")
    assert _db.get_state("test_key", "") == ""


def test_checkpoint_roundtrip():
    _db.save_checkpoint("Abeer|A1|Karachi", 3)
    assert _db.get_checkpoint("Abeer|A1|Karachi") == 3


def test_checkpoint_default():
    assert _db.get_checkpoint("nonexistent") == 0


def test_clear_checkpoint():
    _db.save_checkpoint("Abeer|A1|Karachi", 3)
    _db.clear_checkpoint("Abeer|A1|Karachi")
    assert _db.get_checkpoint("Abeer|A1|Karachi") == 0


def test_clear_all_checkpoints():
    _db.save_checkpoint("one", 1)
    _db.save_checkpoint("two", 2)
    _db.clear_all_checkpoints()
    assert _db.get_checkpoint("one") == 0
    assert _db.get_checkpoint("two") == 0


def test_save_and_get_students():
    students = [
        {"name": "Abeer", "level": "A1", "city": "Karachi", "booking_datetime": "2026-07-17T10:00:00", "email": "a@b.com"},
    ]
    _db.save_students(students)
    result = _db.get_students()
    assert len(result) == 1
    assert result[0]["name"] == "Abeer"


def test_update_student_status():
    students = [
        {"name": "Abeer", "level": "A1", "city": "Karachi", "booking_datetime": "2026-07-17T10:00:00", "email": "a@b.com"},
    ]
    _db.save_students(students)
    _db.update_student_status("Abeer|A1|Karachi", "booked", {"ref": "123"})
    result = _db.get_students()
    assert result[0]["status"] == "booked"


def test_add_and_get_logs():
    _db.add_log("Abeer|A1|Karachi", "A1", "Test log message")
    logs = _db.get_logs("Abeer|A1|Karachi")
    assert len(logs) == 1
    assert logs[0]["message"] == "Test log message"
