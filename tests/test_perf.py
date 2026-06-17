"""Performance benchmarks for core operations."""
import time
import pytest
import json

pytestmark = pytest.mark.skip(reason="Run manually: python -m pytest tests/test_perf.py -v")


def test_deadman_switch_perf():
    from deadman import DeadManSwitch
    sw = DeadManSwitch(timeout=60)
    start = time.perf_counter()
    for _ in range(10000):
        sw.ping()
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"10000 pings took {elapsed:.3f}s (expected <0.5s)"


def test_circuit_breaker_perf():
    from booking_helper import CircuitBreaker
    cb = CircuitBreaker(threshold=100, cooldown=1)
    start = time.perf_counter()
    for _ in range(5000):
        cb.record_failure()
    cb.reset()
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"5000 failures took {elapsed:.3f}s"


def test_queue_enqueue_dequeue_perf():
    from student_queue import BookingQueue
    q = BookingQueue()
    start = time.perf_counter()
    for i in range(5000):
        q.enqueue(name=f"Student{i}", email=f"s{i}@test.com")
    for _ in range(5000):
        q.dequeue()
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"5000 enqueue+dequeue took {elapsed:.3f}s"


def test_db_read_write_perf(tmp_path):
    import db
    test_db = tmp_path / "test_perf.db"
    db_path_orig = db.DB_PATH
    try:
        db.DB_PATH = str(test_db)
        db.init_db()
        start = time.perf_counter()
        for i in range(1000):
            db.set_state(f"key_{i}", f"value_{i}")
        for i in range(1000):
            db.get_state(f"key_{i}")
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"1000 write+read took {elapsed:.3f}s"
    finally:
        db.DB_PATH = db_path_orig


def test_json_serialization_perf():
    data = {"students": [{"id": i, "name": f"Student {i}"} for i in range(100)]}
    start = time.perf_counter()
    for _ in range(1000):
        json.dumps(data)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"1000 serializations took {elapsed:.3f}s"
