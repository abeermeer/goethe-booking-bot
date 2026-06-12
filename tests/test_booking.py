import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import booking_helper as bot


def test_bounded_backoff():
    assert bot.bounded_backoff(1) >= 3
    assert bot.bounded_backoff(10) <= 60


def test_long_cooldown():
    cd = bot.long_cooldown()
    assert 120 <= cd <= 300


def test_parse_exam_time_str():
    dt = bot.parse_exam_time_str("2026-07-17T10:00:00")
    assert dt.year == 2026
    assert dt.month == 7
    assert dt.day == 17
    assert dt.hour == 10


def test_parse_exam_time_str_empty():
    assert bot.parse_exam_time_str("") is None


def test_get_exam_url_real():
    urls = bot.get_exam_url("A1")
    assert "goethe.de" in urls


def test_normalize_text():
    assert bot.normalize_text("  Hello  ") == "hello"
    assert bot.normalize_text("Hello-World") == "hello-world"


def test_looks_clickable():
    class MockElement:
        def is_enabled(self):
            return True

        def is_displayed(self):
            return True

        def get_attribute(self, _):
            return None

        def tag_name(self):
            return "button"

    el = MockElement()
    assert bot.looks_clickable(el) is True


def test_random_human_delay():
    import time
    start = time.time()
    bot.random_human_delay(0.1, 0.2)
    elapsed = time.time() - start
    assert 0.05 <= elapsed <= 0.5
