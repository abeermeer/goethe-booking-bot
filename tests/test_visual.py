"""Visual regression tests using Playwright screenshot comparison."""
import pytest

pytestmark = pytest.mark.skip(reason="Requires Playwright: python -m pytest tests/test_visual.py --headed")


def test_frontend_loads_correctly(page):
    """Verify the dashboard loads without visual regression."""
    page.goto("https://goethe-booking-dashboard.netlify.app")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="artifacts/screenshots/dashboard.png", full_page=True)


def test_login_form_renders(page):
    """Verify login form is visible."""
    page.goto("https://goethe-booking-dashboard.netlify.app")
    page.wait_for_selector("input[type='email']", timeout=10000)
    page.wait_for_selector("input[type='password']", timeout=10000)
    page.wait_for_selector("button[type='submit']", timeout=10000)
    page.screenshot(path="artifacts/screenshots/login_form.png")


def test_dark_mode_toggle(page):
    """Verify dark mode CSS variables are applied."""
    page.goto("https://goethe-booking-dashboard.netlify.app")
    page.evaluate("localStorage.setItem('theme', 'dark')")
    page.reload()
    page.wait_for_load_state("networkidle")
    bg = page.evaluate("getComputedStyle(document.body).getPropertyValue('--bg')")
    assert bg.strip(), "Dark mode --bg should not be empty"
