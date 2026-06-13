import pytest


def _clean():
    import sqlite3
    import db
    conn = sqlite3.connect(str(db.DB_PATH))
    conn.execute("DELETE FROM queue_history")
    conn.execute("DELETE FROM logs")
    conn.execute("DELETE FROM students")
    conn.execute("DELETE FROM bot_state")
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def clean_db():
    _clean()
