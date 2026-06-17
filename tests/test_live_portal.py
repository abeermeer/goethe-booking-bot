"""Live integration tests against the real Goethe exam portal (requires Playwright).

Usage:
  playwright install chromium
  python -m pytest tests/test_live_portal.py -v --headed  # see browser

These tests hit the actual goethe.de website. Run sparingly to avoid rate limits.
"""
import pytest

pytestmark = pytest.mark.skipif(
    True,
    reason="Requires Playwright + hits live site. Run manually with: pytest tests/test_live_portal.py -v",
)

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def test_exam_page_loads(browser):
    """Verify the Goethe exam page loads and contains expected elements."""
    page = browser.new_page()
    page.goto("https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm", wait_until="networkidle", timeout=30000)
    assert "Goethe-Zertifikat A1" in page.title()
    # The exam finder widget should be present (even if JS hasn't rendered prices)
    finder = page.locator("#content, .finder-container, .pruefungsfinder, [class*='finder']")
    assert finder.first.is_visible()


def test_exam_finder_widget_renders(browser):
    """Wait for the Prüfungsfinder JS widget to fully render with dates."""
    page = browser.new_page()
    page.goto("https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm", wait_until="networkidle", timeout=30000)
    # Give JS time to render the dynamic content
    page.wait_for_timeout(8000)
    # Look for bookable slots or date tables
    body = page.inner_text("body")
    # The page should contain exam-related keywords
    assert any(kw in body for kw in ["B1", "Goethe-Zertifikat", "Date", "Registration", "Book Now"])


def test_multiple_levels_accessible(browser):
    """Verify all exam level pages are reachable."""
    levels = {
        "A1": "gzsd1.cfm",
        "A2": "gzsd2.cfm",
        "B1": "gzb1.cfm",
        "B2": "gzb2.cfm",
        "C1": "gzc1.cfm",
        "C2": "gzc2.cfm",
    }
    for level, path in levels.items():
        page = browser.new_page()
        url = f"https://www.goethe.de/ins/pk/en/spr/prf/{path}"
        resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        assert resp.ok, f"{level} page returned {resp.status}"
        assert level in page.title(), f"{level} not in title: {page.title()}"
        page.close()
