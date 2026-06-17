"""Fuzz testing for input parsing and validation."""
import pytest
import random
import string

pytestmark = pytest.mark.skip(reason="Run manually: python -m pytest tests/test_fuzz.py -v")


def _random_string(max_len=50):
    chars = string.ascii_letters + string.digits + " \t\n\r!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
    return "".join(random.choice(chars) for _ in range(random.randint(0, max_len)))


def _random_unicode(max_len=20):
    """Generate random unicode including emoji."""
    chars = " ".join(chr(random.randint(0x80, 0x1FFFF)) for _ in range(random.randint(0, max_len)))
    return chars


class TestBookingParserFuzz:
    def test_parse_exam_time_str_random(self):
        from booking_helper import parse_exam_time_str
        for _ in range(500):
            s = _random_string()
            try:
                parse_exam_time_str(s)
            except (ValueError, AttributeError, TypeError):
                pass

    def test_normalize_text_random(self):
        from booking_helper import normalize_text
        for _ in range(500):
            s = _random_string(100)
            try:
                normalize_text(s)
            except Exception:
                pass

    def test_normalize_unicode(self):
        from booking_helper import normalize_text
        for _ in range(100):
            s = _random_unicode()
            try:
                normalize_text(s)
            except Exception:
                pass


class TestConfirmationParserFuzz:
    def test_parse_known_patterns_random(self):
        from confirmation_parser import parse_confirmation, parse_exam_date, parse_level
        for _ in range(500):
            s = _random_string(200)
            try:
                parse_confirmation(s)
                parse_exam_date(s)
                parse_level(s)
            except Exception:
                pass


class TestDbFuzz:
    def test_db_key_values(self):
        import db
        for _ in range(200):
            key = _random_string(100)
            value = _random_string(200)
            try:
                db.set_state(key, value)
                db.get_state(key)
                db.delete_state(key)
            except Exception:
                pass

    def test_db_special_chars(self):
        import db
        specials = ["\x00", "\x01", "\x1f", "\x7f", "\\'\"", "-- DROP TABLE", "1; DROP TABLE"]
        for s in specials:
            try:
                db.set_state(f"fuzz_{s}", s)
                db.get_state(f"fuzz_{s}")
                db.delete_state(f"fuzz_{s}")
            except Exception:
                pass


class TestPydanticFuzz:
    def test_login_validation_random(self):
        from webapp import LoginRequest
        from pydantic import ValidationError
        for _ in range(200):
            try:
                LoginRequest(email=_random_string(300), password=_random_string(300))
            except ValidationError:
                pass

    def test_start_request_fuzz(self):
        from webapp import StartRequest, StudentItem
        from pydantic import ValidationError
        for _ in range(100):
            students = [StudentItem(student_id=_random_string(50), name=_random_string(100))]
            try:
                StartRequest(students=students, headless=True, immediate=False)
            except ValidationError:
                pass
