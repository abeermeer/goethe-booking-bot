import threading
import time
from circuit_breaker import CircuitBreaker


def test_starts_closed():
    cb = CircuitBreaker(threshold=5, cooldown=60)
    assert cb.state == "closed"
    assert cb.allow_request() is True


def test_opens_after_threshold_failures():
    cb = CircuitBreaker(threshold=3, cooldown=60)
    for _ in range(3):
        assert cb.allow_request() is True
        cb.record_failure()
    assert cb.state == "open"
    assert cb.allow_request() is False


def test_stays_closed_below_threshold():
    cb = CircuitBreaker(threshold=10, cooldown=60)
    for _ in range(5):
        cb.record_failure()
    assert cb.state == "closed"
    assert cb.allow_request() is True


def test_success_resets():
    cb = CircuitBreaker(threshold=3, cooldown=60)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == "open"
    cb.record_success()
    assert cb.state == "closed"
    assert cb.consecutive_failures == 0


def test_half_open_transition():
    cb = CircuitBreaker(threshold=2, cooldown=0.1)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "open"
    assert cb.allow_request() is False
    time.sleep(0.15)
    assert cb.allow_request() is True
    assert cb.state == "half-open"


def test_success_closes_from_half_open():
    cb = CircuitBreaker(threshold=2, cooldown=0.1)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.15)
    cb.allow_request()
    assert cb.state == "half-open"
    cb.record_success()
    assert cb.state == "closed"


def test_failure_during_half_open_reopens():
    cb = CircuitBreaker(threshold=2, cooldown=0.3)
    cb.record_failure()
    cb.record_failure()
    time.sleep(0.35)
    cb.record_failure()
    assert cb.state == "open"


def test_wait_until_allowed():
    cb = CircuitBreaker(threshold=1, cooldown=0.2)
    cb.record_failure()
    assert cb.allow_request() is False
    start = time.monotonic()
    cb.wait_until_allowed(poll=0.05)
    elapsed = time.time() - start
    assert elapsed >= 0.15
    assert cb.allow_request() is True


def test_wait_until_allowed_stop_event():
    cb = CircuitBreaker(threshold=1, cooldown=30)
    cb.record_failure()
    stop = threading.Event()
    result = []
    def waiter():
        result.append(cb.wait_until_allowed(poll=0.05, stop_event=stop))
    t = threading.Thread(target=waiter, daemon=True)
    t.start()
    time.sleep(0.1)
    stop.set()
    t.join(timeout=2)
    assert result[0] is False


def test_reset():
    cb = CircuitBreaker(threshold=3, cooldown=60)
    for _ in range(5):
        cb.record_failure()
    assert cb.state == "open"
    cb.reset()
    assert cb.state == "closed"
    assert cb.consecutive_failures == 0
    assert cb.allow_request() is True


def test_consecutive_failures_property():
    cb = CircuitBreaker(threshold=10, cooldown=60)
    assert cb.consecutive_failures == 0
    cb.record_failure()
    assert cb.consecutive_failures == 1
    cb.record_failure()
    assert cb.consecutive_failures == 2
    cb.record_success()
    assert cb.consecutive_failures == 0


def test_thread_safety():
    cb = CircuitBreaker(threshold=50, cooldown=60)
    errors = []

    def hammer():
        for _ in range(20):
            cb.record_failure()
            cb.allow_request()
            cb.consecutive_failures

    threads = [threading.Thread(target=hammer, daemon=True) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert cb.consecutive_failures == 100
