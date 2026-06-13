import time
from deadman import DeadManSwitch


def test_alive_on_create():
    d = DeadManSwitch()
    assert d.is_alive is True


def test_ping():
    d = DeadManSwitch()
    d.ping()
    assert d.is_alive is True
    assert d.seconds_since_ping < 1.0


def test_check_within_timeout():
    d = DeadManSwitch()
    d.ping()
    assert d.check() is True


def test_monitor_calls_callback():
    d = DeadManSwitch()
    d._timeout_secs = 0.1
    called = False

    def cb():
        nonlocal called
        called = True

    t = d.start_monitor(interval=0.15, on_death=cb)
    t.join(timeout=2)
    assert called is True
