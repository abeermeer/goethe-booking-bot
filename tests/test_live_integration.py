"""Nightly integration tests against real goethe.de portal.
Skipped by default — run with: pytest tests/test_live_integration.py -v
Or via CI cron schedule."""
import pytest
import sys, os, time, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from booking_helper import get_exam_url, check_slot_availability
from goethe_scraper import get_schedule

logger = logging.getLogger(__name__)

@pytest.mark.live
def test_exam_pages_load():
    """Verify all 3 exam pages return 200 and contain expected text."""
    import requests
    for level in ["A1", "A2", "B1"]:
        url = get_exam_url(level)
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, f"{level} page returned {resp.status_code}"
        assert "Goethe" in resp.text or "Prüfung" in resp.text

@pytest.mark.live
def test_login_page_loads():
    """Verify Goethe login page is accessible."""
    import requests
    resp = requests.get("https://login.goethe.de/cas/login", timeout=30)
    assert resp.status_code == 200
    assert "Log in" in resp.text or "username" in resp.text

@pytest.mark.live
def test_schedule_scraper_returns_entries():
    """Verify schedule scraper finds exam entries for all cities."""
    entries = get_schedule(force_refresh=True)
    assert len(entries) > 0, "No exam entries found"
    cities = set(e.city for e in entries)
    assert "Karachi" in cities or "Lahore" in cities or "Islamabad" in cities

@pytest.mark.live
def test_slot_pre_check_no_crash():
    """Verify slot pre-check runs without crashing (may find 0 slots)."""
    student = {
        "name": "CI Test", "email": "ci-test@example.com",
        "level": "A1", "city": "Karachi",
        "booking_datetime": "2099-12-31T23:59"
    }
    result = check_slot_availability(student, logger)
    assert "message" in result
    assert "available" in result
