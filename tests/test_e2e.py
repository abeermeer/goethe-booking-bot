"""E2E tests using Playwright (sync API).
Run: playwright install chromium
     python -m pytest tests/test_e2e.py -v --headed
"""

import pytest
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.absolute()
FRONTEND = PROJECT_DIR / "frontend" / "index.html"

pytest.importorskip("playwright")

BASE_URL = "http://localhost:5000"
FRONTEND_URL = FRONTEND.as_uri()


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def test_frontend_loads(browser):
    """Dashboard loads and shows login card."""
    page = browser.new_page()
    page.goto(FRONTEND_URL, wait_until="networkidle")
    assert "Goethe" in page.title()
    login_btn = page.locator("#loginBtn")
    assert login_btn.is_visible()
    page.close()


def test_backend_health(browser):
    """Health endpoint returns 200 with ok status."""
    page = browser.new_page()
    resp = page.request.get(f"{BASE_URL}/api/health")
    assert resp.status == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "uptime_seconds" in data
    page.close()
