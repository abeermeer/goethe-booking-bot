#!/usr/bin/env python3
"""
Goethe Exam Booking Bot - Fully Automated
==========================================
Extends https://github.com/alyankabir17/A1_Bot with:
- Multi-level support (A1, A2, B1)
- Full login automation (CAS)
- Registration form fill + submit
- Multi-student parallel execution
- Telegram notifications
- Screenshot capture on confirmation

Usage:
  python booking_helper.py --config config.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import os
import random
import re
import string
import sys
import time
import threading
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests
from selenium import webdriver
from selector_fallbacks import (
    find_element_fallback,
    find_elements_fallback,
    wait_for_any_selector,
)
from proxy_rotator import ProxyRotator
from confirmation_parser import parse_confirmation_text, parse_confirmation_url, summarize as summarize_confirmation
from circuit_breaker import CircuitBreaker
from selenium.common.exceptions import (
    NoSuchElementException,
    NoSuchWindowException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from webdriver_manager.chrome import ChromeDriverManager

try:
    from plyer import notification as plyer_notify
except Exception:
    plyer_notify = None

import db
import notifications

# ── Exam level → page URL mapping ──
EXAM_URLS = {
    "A1": os.environ.get("MOCK_A1_URL", "https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm"),
    "A2": os.environ.get("MOCK_A2_URL", "https://www.goethe.de/ins/pk/en/spr/prf/gzsd2.cfm"),
    "B1": os.environ.get("MOCK_B1_URL", "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm"),
}

DEFAULT_POLL_INTERVAL = 10
MIN_HUMAN_DELAY = 0.3
MAX_HUMAN_DELAY = 1.0

BURST_BEFORE_SECONDS = 10
BURST_AFTER_SECONDS = 150
BURST_PRE_POLL = 2.0
BURST_POST_POLL_MIN = 1.0
BURST_POST_POLL_MAX = 2.0
BURST_CRASH_RETRY = 1.0

# ── Proxy rotation ──
PROXY_LIST = [p.strip() for p in os.environ.get("PROXY_LIST", "").split(",") if p.strip()]
PROXY_ROTATOR = ProxyRotator(logger=logging.getLogger("proxy_rotator"))
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]
VIEWPORTS = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)]
CAPTCHA_API_KEY = os.environ.get("CAPTCHA_API_KEY", "")
MAX_SMART_RETRIES = int(os.environ.get("MAX_SMART_RETRIES", "2"))
CIRCUIT_BREAKER_THRESHOLD = int(os.environ.get("CIRCUIT_BREAKER_THRESHOLD", "10"))
CIRCUIT_BREAKER_COOLDOWN = int(os.environ.get("CIRCUIT_BREAKER_COOLDOWN", "900"))


CIRCUIT_BREAKER = CircuitBreaker(threshold=CIRCUIT_BREAKER_THRESHOLD, cooldown=CIRCUIT_BREAKER_COOLDOWN)

# ── Exam schedule (Pakistan 2026) ──
EXAM_SCHEDULE = [
    {"level": "A1", "city": "Islamabad", "exam_date": "18-19 Jul 2026", "registration_period": "26 Jun - 17 Jul 2026", "bookable_from": "26.06.2026", "price_full": "PKR 25,000", "price_reduced": "PKR 16,500", "status": "upcoming"},
    {"level": "A1", "city": "Lahore", "exam_date": "24 Jul 2026", "registration_period": "3 Jul - 23 Jul 2026", "bookable_from": "03.07.2026", "price_full": "PKR 25,000", "price_reduced": "PKR 16,500", "status": "upcoming"},
    {"level": "A1", "city": "Karachi", "exam_date": "31 Jul - 1 Aug 2026", "registration_period": "17 Jul - 30 Jul 2026", "bookable_from": "17.07.2026", "price_full": "PKR 25,000", "price_reduced": "PKR 16,500", "status": "upcoming"},
    {"level": "A1", "city": "Lahore", "exam_date": "21 Aug 2026", "registration_period": "7 Aug - 20 Aug 2026", "bookable_from": "07.08.2026", "price_full": "PKR 25,000", "price_reduced": "PKR 16,500", "status": "upcoming"},
    {"level": "A2", "city": "Karachi", "exam_date": "3-4 Jul 2026", "registration_period": "19 Jun - 2 Jul 2026", "bookable_from": "19.06.2026", "price_full": "PKR 25,000", "price_reduced": "PKR 16,500", "status": "upcoming"},
    {"level": "A2", "city": "Islamabad", "exam_date": "18-19 Jul 2026", "registration_period": "26 Jun - 17 Jul 2026", "bookable_from": "26.06.2026", "price_full": "PKR 25,000", "price_reduced": "PKR 16,500", "status": "upcoming"},
    {"level": "A2", "city": "Lahore", "exam_date": "25-26 Jul 2026", "registration_period": "3 Jul - 23 Jul 2026", "bookable_from": "03.07.2026", "price_full": "PKR 25,000", "price_reduced": "PKR 16,500", "status": "upcoming"},
    {"level": "B1", "city": "Lahore", "exam_date": "20-21 Jun 2026", "registration_period": "5 Jun - 18 Jun 2026", "bookable_from": "fully_booked", "price_full": "PKR 30,000", "price_reduced": "PKR 25,000", "status": "fully_booked"},
    {"level": "B1", "city": "Karachi", "exam_date": "3-4 Jul 2026", "registration_period": "19 Jun - 2 Jul 2026", "bookable_from": "19.06.2026", "price_full": "PKR 30,000", "price_reduced": "PKR 25,000", "status": "upcoming"},
    {"level": "B1", "city": "Islamabad", "exam_date": "18-19 Jul 2026", "registration_period": "26 Jun - 17 Jul 2026", "bookable_from": "26.06.2026", "price_full": "PKR 30,000", "price_reduced": "PKR 25,000", "status": "upcoming"},
    {"level": "B1", "city": "Lahore", "exam_date": "25-26 Jul 2026", "registration_period": "3 Jul - 23 Jul 2026", "bookable_from": "03.07.2026", "price_full": "PKR 30,000", "price_reduced": "PKR 25,000", "status": "upcoming"},
    {"level": "B1", "city": "Karachi", "exam_date": "31 Jul - 1 Aug 2026", "registration_period": "17 Jul - 29 Jul 2026", "bookable_from": "17.07.2026", "price_full": "PKR 30,000", "price_reduced": "PKR 25,000", "status": "upcoming"},
    {"level": "B1", "city": "Lahore", "exam_date": "22-23 Aug 2026", "registration_period": "7 Aug - 20 Aug 2026", "bookable_from": "07.08.2026", "price_full": "PKR 30,000", "price_reduced": "PKR 25,000", "status": "upcoming"},
]


def get_schedule() -> list:
    return EXAM_SCHEDULE

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def setup_logger(name: str = "booking_helper") -> logging.Logger:
    log_name = f"booking_helper_{dt.date.today().isoformat()}.log"
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    file_handler = logging.FileHandler(log_name, encoding="utf-8")
    file_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(file_fmt)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    stream_handler.setFormatter(stream_fmt)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.info("Logging initialized. File: %s", log_name)
    return logger


def parse_bool(value: str) -> bool:
    v = str(value).strip().lower()
    return v in {"1", "true", "yes", "y", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Goethe Exam Booking Bot")
    parser.add_argument("--config", default="config.csv", help="Path to config.csv")
    parser.add_argument("--headless", type=parse_bool, default=False, help="Run Chrome headless")
    parser.add_argument("--telegram-token", default="", help="Telegram bot token")
    parser.add_argument("--telegram-chat-id", default="", help="Telegram chat ID")
    return parser.parse_args()


def load_all_students(path: str) -> List[Dict[str, str]]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    if config_path.suffix.lower() != ".csv":
        raise ValueError("Config must be .csv")

    with config_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            data = {k.strip(): str(v).strip() for k, v in row.items()}
            if data.get("name") or data.get("email"):
                rows.append(data)
        if not rows:
            raise ValueError("No student rows found in CSV")
        return rows


def parse_exam_time_str(raw: str) -> Optional[dt.datetime]:
    raw = raw.strip()
    if not raw:
        return None
    if "T" in raw or "-" in raw:
        return dt.datetime.fromisoformat(raw)
    today = dt.date.today().isoformat()
    return dt.datetime.fromisoformat(f"{today}T{raw}")


def random_human_delay(min_sec: float = MIN_HUMAN_DELAY, max_sec: float = MAX_HUMAN_DELAY) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def send_telegram(message: str, logger: logging.Logger) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=10)
        logger.info("Telegram notification sent")
    except Exception as exc:
        logger.warning("Telegram send failed: %s", exc)


def notify(title: str, message: str, logger: logging.Logger) -> None:
    logger.info("NOTIFY: %s - %s", title, message)
    if plyer_notify is not None:
        try:
            plyer_notify.notify(title=title, message=message, timeout=8)
        except Exception as exc:
            logger.warning("Desktop notification failed: %s", exc)
    notifications.notify_all(title, message, logger)


_driver_counter = 0

def create_driver(use_headless: bool, logger: logging.Logger, proxy: Optional[str] = None) -> webdriver.Chrome:
    global _driver_counter
    _driver_counter += 1
    options = Options()

    # ── Browser fingerprint randomization ──
    ua = random.choice(USER_AGENTS)
    vp = random.choice(VIEWPORTS)
    options.add_argument(f"--user-agent={ua}")

    # ── Platform-specific setup ──
    if os.name != "nt":
        for chrome_bin in ["/opt/google/chrome/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]:
            if Path(chrome_bin).exists():
                options.binary_location = chrome_bin
                break
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = "/dev/null"
        os.environ["DISPLAY"] = ":99"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-default-apps")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")

    # ── Memory optimization for Railway 512MB ──
    options.add_argument("--process-per-site")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=VizDisplayCompositor,TranslateUI,ChromeWhatsNewUI,InterestFeedContentSuggestions,OptimizationHints")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--log-level=3")
    options.add_argument("--silent-debugger-extension-api")
    options.add_argument("--disable-search-engine-choice-screen")

    if use_headless or os.name != "nt":
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={min(vp[0],1280)},{min(vp[1],720)}")

    # ── Proxy ──
    if proxy:
        logger.info("Using proxy: %s", proxy)
        options.add_argument(f"--proxy-server={proxy}")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-US,en")
    options.add_experimental_option("prefs", {"intl.accept_languages": "en-US,en"})
    profile_dir = Path.home() / "goethe-bot-profiles" / f"profile_{_driver_counter}"
    profile_dir.mkdir(parents=True, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_dir}")

    if os.name != "nt":
        system_driver = next((p for p in ["/usr/local/bin/chromedriver", "/usr/bin/chromedriver", "/usr/lib/chromium/chromedriver"] if Path(p).exists()), None)
        if system_driver:
            service = Service(system_driver)
        else:
            service = Service(ChromeDriverManager().install())
    else:
        service = Service(ChromeDriverManager().install())
        service.creation_flags = 0
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            driver = webdriver.Chrome(service=service, options=options)
            break
        except Exception as exc:
            if attempt < max_attempts:
                logger.warning("Chrome launch attempt %d/%d failed: %s. Retrying in 5s...", attempt, max_attempts, exc)
                time.sleep(5)
            else:
                raise
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass
    logger.info("Driver created: UA=%s, VP=%sx%s%s", ua[:50], vp[0], vp[1], f", proxy={proxy}" if proxy else "")
    return driver


def is_blocked_response(driver: webdriver.Chrome) -> bool:
    title = (driver.title or "").lower()
    if any(t in title for t in ["429", "503", "too many requests", "access denied", "attention required"]):
        return True
    try:
        body = driver.find_element(By.TAG_NAME, "body").text.lower()
    except Exception:
        body = ""
    strong = ["checking your browser", "verify you are human", "just a moment", "ray id"]
    return any(p in body for p in strong)


def bounded_backoff(attempt: int, base: int = 3, cap: int = 60) -> int:
    return min(cap, int(base * (2 ** max(0, attempt - 1))))


def long_cooldown() -> int:
    return random.randint(120, 300)


def wait_for_finder(driver: webdriver.Chrome, timeout: int = 40) -> WebElement:
    result = wait_for_any_selector(driver, "finder_container", timeout=timeout)
    if result is None:
        raise TimeoutException("Exam finder container did not load.")
    return result


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def looks_clickable(button: WebElement) -> bool:
    if not button.is_displayed():
        return False
    if not button.is_enabled():
        return False
    cls = normalize_text(button.get_attribute("class") or "")
    if any(x in cls for x in ["disabled", "nicht-buchbar", "gray", "grey"]):
        return False
    aria = normalize_text(button.get_attribute("aria-disabled") or "")
    if aria in {"true", "1"}:
        return False
    return True


def find_book_buttons(driver: webdriver.Chrome) -> List[WebElement]:
    buttons = find_elements_fallback(driver, "book_button", timeout=10)
    if not buttons:
        fallback = driver.find_elements(By.CSS_SELECTOR, "a.standard, button.standard")
        text_filtered = []
        for item in fallback:
            txt = normalize_text(item.text)
            if any(t in txt for t in ["book", "next", "buchen", "weiter"]):
                text_filtered.append(item)
        buttons = text_filtered
    return [b for b in buttons if looks_clickable(b)]


def button_row_text(button: WebElement) -> str:
    try:
        row = button.find_element(By.XPATH, "ancestor::*[self::tr or self::li or self::div][1]")
        return normalize_text(row.text)
    except Exception:
        return normalize_text(button.text)


def pick_preferred_button(buttons: Sequence[WebElement], preferred_city: str) -> Optional[WebElement]:
    if not buttons:
        return None
    pref = normalize_text(preferred_city)
    if pref:
        for b in buttons:
            if pref in button_row_text(b):
                return b
    return buttons[0]


def human_move_and_click(driver: webdriver.Chrome, element: WebElement) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    try:
        driver.execute_script("arguments[0].removeAttribute('target');", element)
    except Exception:
        pass
    random_human_delay()
    actions = ActionChains(driver)
    actions.move_to_element(element)
    actions.pause(random.uniform(0.05, 0.2))
    actions.move_by_offset(random.randint(-2, 2), random.randint(-2, 2))
    actions.pause(random.uniform(0.03, 0.1))
    actions.click()
    actions.perform()


# ── Advanced human behavior simulation ──

def random_scroll(driver: webdriver.Chrome):
    """Small random scroll to mimic reading."""
    delta = random.randint(-150, 300)
    driver.execute_script(f"window.scrollBy(0, {delta});")
    time.sleep(random.uniform(0.3, 1.2))


def random_mouse_wander(driver: webdriver.Chrome):
    """Move mouse to a random location on the page."""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        w = body.size.get("width", 800)
        h = body.size.get("height", 600)
        ox = random.randint(0, max(w - 100, 100))
        oy = random.randint(0, max(h - 100, 100))
        actions = ActionChains(driver)
        actions.move_by_offset(ox, oy)
        actions.pause(random.uniform(0.1, 0.4))
        actions.perform()
    except Exception:
        pass


def human_pause_between_fields():
    """Pause as if user is reading the next field."""
    time.sleep(random.uniform(0.4, 1.8))


def simulate_human_typing(element: WebElement, text: str) -> None:
    """Type text with realistic human-like bursts and pauses."""
    element.clear()
    element.click()
    for ch in text:
        element.send_keys(ch)
        if random.random() < 0.08:
            time.sleep(random.uniform(0.3, 0.9))
        elif random.random() < 0.03:
            time.sleep(random.uniform(1.0, 2.5))
        else:
            time.sleep(random.uniform(0.04, 0.15))


# ── CAPTCHA solving (2Captcha) ──

def detect_captcha(driver: webdriver.Chrome) -> Optional[str]:
    """Check if a CAPTCHA iframe or element is on the page."""
    captcha_selectors = [
        "iframe[src*='recaptcha']", "iframe[src*='captcha']",
        ".g-recaptcha", "#recaptcha", "[class*='captcha']",
        "iframe[title*='captcha']",
    ]
    for css in captcha_selectors:
        els = driver.find_elements(By.CSS_SELECTOR, css)
        if els:
            return css
    return None


def solve_captcha(driver: webdriver.Chrome, logger: logging.Logger) -> bool:
    """Solve reCAPTCHA v2 using 2Captcha."""
    if not CAPTCHA_API_KEY:
        logger.warning("CAPTCHA detected but no CAPTCHA_API_KEY set")
        return False
    try:
        site_key_el = driver.find_element(By.CSS_SELECTOR, ".g-recaptcha")
        site_key = site_key_el.get_attribute("data-sitekey")
        if not site_key:
            return False
        page_url = driver.current_url
        logger.info("CAPTCHA site key found: %s", site_key)

        resp = requests.post("https://2captcha.com/in.php", data={
            "key": CAPTCHA_API_KEY, "method": "userrecaptcha",
            "googlekey": site_key, "pageurl": page_url,
            "json": 1,
        }, timeout=30)
        data = resp.json()
        if data.get("status") != 1:
            logger.warning("2Captcha send failed: %s", data)
            return False
        captcha_id = data["request"]

        for _ in range(60):
            time.sleep(5)
            result = requests.get("https://2captcha.com/res.php", params={
                "key": CAPTCHA_API_KEY, "action": "get", "id": captcha_id, "json": 1,
            }, timeout=15).json()
            if result.get("status") == 1:
                token = result["request"]
                driver.execute_script(
                    f"document.getElementById('g-recaptcha-response').innerHTML='{token}';"
                )
                driver.execute_script(f"___grecaptcha_cfg.clients[0].callback('{token}');")
                logger.info("CAPTCHA solved")
                return True
            if result.get("request") == "ERROR_CAPTCHA_UNSOLVABLE":
                logger.warning("CAPTCHA unsolvable")
                return False
        logger.warning("CAPTCHA timeout")
        return False
    except Exception as exc:
        logger.warning("CAPTCHA solve error: %s", exc)
        return False


# ── Proxy support in create_driver ──
# Proxy is applied inside create_driver when a proxy string is passed

# ── Smart retry wrapper ──

def smart_retry(student: Dict[str, str], use_headless: bool, logger: logging.Logger,
                stop_event: threading.Event, attempt: int = 1,
                immediate: bool = False) -> Dict[str, str]:
    """Run student flow with smart retry on failure (new profile, new proxy).
    When immediate=True, skip the scheduled wait and run right away."""
    result = run_student_flow(student, use_headless, logger, stop_event, immediate=immediate)
    status = result.get("status", "failed")
    if status in ("failed", "error") and attempt <= MAX_SMART_RETRIES:
        logger.warning("Smart retry %d/%d for %s", attempt, MAX_SMART_RETRIES, student.get("name", "?"))
        if not CIRCUIT_BREAKER.wait_until_allowed(poll=5.0, stop_event=stop_event):
            result["status"] = "stopped"
            return result
        time.sleep(random.uniform(30, 60))
        result = smart_retry(student, use_headless, logger, stop_event, attempt + 1, immediate=immediate)
    return result


# ── Scheduled mode ──

SCHEDULED_CHECK_INTERVAL = 30  # seconds

def scheduled_wait(booking_time_str: str, logger: logging.Logger, stop_event: threading.Event) -> bool:
    """Wait until the booking time arrives. Returns True if it's time."""
    if not booking_time_str:
        return True
    try:
        target = parse_exam_time_str(booking_time_str)
    except Exception:
        return True

    logger.info("Scheduled mode: waiting until %s", target.strftime("%Y-%m-%d %H:%M:%S"))
    while not stop_event.is_set():
        now = dt.datetime.now()
        if now >= target:
            logger.info("Scheduled time reached, starting bot")
            return True
        remaining = (target - now).total_seconds()
        if remaining <= 10:
            logger.info("Less than 10s to go, entering burst mode")
            time.sleep(0.5)
        else:
            gap = min(SCHEDULED_CHECK_INTERVAL, remaining / 2)
            for _ in range(int(gap)):
                if stop_event.is_set():
                    return False
                time.sleep(1)
    return False


def enforce_single_tab(driver: webdriver.Chrome) -> None:
    handles = driver.window_handles
    if len(handles) <= 1:
        return
    keep = handles[-1]
    for h in handles:
        if h == keep:
            continue
        try:
            driver.switch_to.window(h)
            driver.close()
        except Exception:
            pass
    driver.switch_to.window(keep)


def wait_for_document_ready(driver: webdriver.Chrome, timeout: int = 30) -> None:
    end = time.time() + timeout
    while time.time() < end:
        state = driver.execute_script("return document.readyState")
        if state == "complete":
            return
        time.sleep(0.5)
    raise TimeoutException("Document not ready in time.")


def wait_and_find(driver: webdriver.Chrome, css_selector: str, timeout: int = 15) -> Optional[WebElement]:
    try:
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
    except (TimeoutException, NoSuchElementException):
        return None


def type_slowly(element: WebElement, text: str) -> None:
    element.clear()
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.01, 0.05))


def click_continue_button(driver: webdriver.Chrome, logger: logging.Logger, timeout: int = 90) -> None:
    random_human_delay(0.3, 0.8)
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            wait_for_document_ready(driver, timeout=timeout)
            button = find_element_fallback(driver, "continue_button", timeout=timeout, logger=logger)
            if button is None:
                raise NoSuchElementException("Continue button not found with any selector")
            logger.info("'Continue' button found. Clicking...")
            human_move_and_click(driver, button)
            return
        except StaleElementReferenceException:
            if attempt < max_attempts:
                logger.warning("Stale element on Continue button, retrying %d/%d", attempt, max_attempts)
                time.sleep(2)
            else:
                raise


def click_book_for_myself(driver: webdriver.Chrome, logger: logging.Logger, timeout: int = 90) -> None:
    random_human_delay(0.3, 0.8)
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            wait_for_document_ready(driver, timeout=timeout)
            button = find_element_fallback(driver, "book_for_myself", timeout=timeout, logger=logger)
            if button is None:
                raise NoSuchElementException("Book for myself button not found with any selector")
            logger.info("'Book for myself' button found. Clicking...")
            human_move_and_click(driver, button)
            return
        except StaleElementReferenceException:
            if attempt < max_attempts:
                logger.warning("Stale element on Book for Myself button, retrying %d/%d", attempt, max_attempts)
                time.sleep(2)
            else:
                raise


def login_to_goethe(driver: webdriver.Chrome, email: str, password: str, logger: logging.Logger) -> bool:
    logger.info("══ STEP 4: Logging in to My Goethe.de ══")
    for attempt in range(1, 4):
        try:
            return _login_attempt(driver, email, password, logger)
        except StaleElementReferenceException:
            if attempt < 3:
                logger.warning("Stale element during login, retrying %d/3", attempt)
                time.sleep(2)
            else:
                logger.error("Login failed after 3 attempts due to stale elements")
                return False

def _login_attempt(driver: webdriver.Chrome, email: str, password: str, logger: logging.Logger) -> bool:
    try:
        wait_for_document_ready(driver, timeout=30)
        random_human_delay()

        email_input = find_element_fallback(driver, "login_email", timeout=15, logger=logger)
        if email_input is None:
            logger.warning("Email field not found. Dumping page HTML for debugging.")
            logger.info("Page URL: %s", driver.current_url)
            logger.info("Page title: %s", driver.title)
            body = driver.find_element(By.TAG_NAME, "body").text[:500]
            logger.info("Page body preview: %s", body)
            return False

        type_slowly(email_input, email)
        random_human_delay()

        pwd_input = find_element_fallback(driver, "login_password", timeout=10, logger=logger)
        if pwd_input is None:
            logger.warning("Password field not found")
            return False
        type_slowly(pwd_input, password)
        random_human_delay()

        try:
            checkbox = find_element_fallback(driver, "login_checkbox_stay", timeout=5)
            if checkbox and checkbox.is_displayed():
                human_move_and_click(driver, checkbox)
        except (NoSuchElementException, TimeoutException):
            pass

        submit_btn = find_element_fallback(driver, "login_submit", timeout=10, logger=logger)
        if submit_btn is None:
            logger.warning("Submit button not found")
            return False
        logger.info("Clicking login submit button...")
        human_move_and_click(driver, submit_btn)

        wait_for_document_ready(driver, timeout=30)
        random_human_delay()

        current_url = driver.current_url.lower()
        logger.info("Post-login URL: %s", current_url)
        if "login" in current_url or "cas/login" in current_url:
            error_el = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, .message-error, .errortext")
            if error_el:
                logger.error("Login error: %s", error_el[0].text)
            logger.warning("Still on login page after submit — credentials may be wrong")
            return False

        logger.info("★ LOGIN SUCCESSFUL")
        return True

    except NoSuchElementException as exc:
        logger.error("Login failed - element not found: %s", exc)
        logger.info("Current URL: %s", driver.current_url)
        logger.info("Dumping login page HTML to debug_login.html for inspection")
        try:
            page_html = driver.page_source
            with open("debug_login.html", "w", encoding="utf-8") as f:
                f.write(page_html)
            logger.info("Saved to debug_login.html")
        except Exception:
            pass
        return False
    except Exception as exc:
        logger.exception("Login error: %s", exc)
        return False


def fill_registration_form(driver: webdriver.Chrome, student: Dict[str, str], logger: logging.Logger) -> bool:
    logger.info("══ STEP 5: Filling registration form ══")
    for attempt in range(1, 4):
        try:
            return _fill_attempt(driver, student, logger)
        except StaleElementReferenceException:
            if attempt < 3:
                logger.warning("Stale element during form fill, retrying %d/3", attempt)
                time.sleep(2)
            else:
                logger.error("Form fill failed after 3 attempts due to stale elements")
                return False

def _fill_attempt(driver: webdriver.Chrome, student: Dict[str, str], logger: logging.Logger) -> bool:
    logger.info("══ STEP 5: Filling registration form ══")
    try:
        wait_for_document_ready(driver, timeout=30)
        random_human_delay(0.5, 1.0)

        logger.info("Current URL after login: %s", driver.current_url)
        logger.info("Page title: %s", driver.title)

        fields = {
            "form_name": student.get("name", ""),
            "form_dob": student.get("dob", ""),
            "form_place_of_birth": student.get("place_of_birth", ""),
            "form_phone": student.get("phone", ""),
        }

        for selector_key, value in fields.items():
            if not value:
                continue
            try:
                el = find_element_fallback(driver, selector_key, timeout=5, logger=logger)
                if el and el.is_displayed():
                    tag = el.tag_name.lower()
                    if tag == "select":
                        Select(el).select_by_visible_text(value)
                    else:
                        type_slowly(el, value)
                    random_human_delay(0.1, 0.2)
                    logger.info("Filled %s = %s", selector_key, value[:30])
            except (NoSuchElementException, TimeoutException):
                logger.debug("Field not found: %s", selector_key)
                continue

        try:
            address = student.get("address", "")
            if address:
                addr_el = find_element_fallback(driver, "form_address", timeout=5)
                if addr_el and addr_el.is_displayed():
                    type_slowly(addr_el, address)
                    random_human_delay()
        except (NoSuchElementException, TimeoutException):
            pass

        try:
            terms = find_elements_fallback(driver, "form_terms", timeout=5)
            for cb in terms:
                if cb.is_displayed() and not cb.is_selected():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
                    driver.execute_script("arguments[0].click();", cb)
                    random_human_delay()
                    break
        except (NoSuchElementException, TimeoutException):
            pass

        try:
            level_val = student.get("level", student.get("exam_level", ""))
            if level_val:
                level_el = find_element_fallback(driver, "form_level", timeout=5)
                if level_el and level_el.is_displayed():
                    Select(level_el).select_by_visible_text(level_val)
                    random_human_delay()
        except (NoSuchElementException, TimeoutException):
            logger.debug("Level dropdown not found")

        random_human_delay(0.3, 0.8)

        submit_btn = find_element_fallback(driver, "form_submit", timeout=10, logger=logger)

        if submit_btn is None:
            for fallback_selector in [
                "button.btn-primary, button.btn, button.standard",
                "input[type='submit'], button[type='submit']",
            ]:
                try:
                    btns = driver.find_elements(By.CSS_SELECTOR, fallback_selector)
                    for btn in btns:
                        if btn.is_displayed() and btn.is_enabled():
                            submit_btn = btn
                            break
                    if submit_btn:
                        break
                except Exception:
                    continue

        if submit_btn is None:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in all_buttons:
                txt = normalize_text(btn.text)
                if any(x in txt for x in ["submit", "book", "register", "confirm", "send", "absenden", "buchen", "bestätigen"]):
                    if btn.is_displayed() and btn.is_enabled():
                        submit_btn = btn
                        break

        if submit_btn:
            logger.info("Clicking submit button...")
            human_move_and_click(driver, submit_btn)
            wait_for_document_ready(driver, timeout=30)
            random_human_delay()
            logger.info("Form submitted. Post-submit URL: %s", driver.current_url)
            return True
        else:
            logger.warning("Submit button not found! Dumping page for debugging.")
            driver.save_screenshot("debug_no_submit.png")
            return False
    except Exception as exc:
        logger.exception("Form fill error: %s", exc)
        return False


def capture_confirmation(driver: webdriver.Chrome, student_name: str, logger: logging.Logger) -> Dict[str, str]:
    logger.info("══ STEP 6: Capturing confirmation ══")
    result = {"name": student_name, "status": "unknown", "url": driver.current_url}

    try:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^a-zA-Z0-9]", "_", student_name)
        screenshot_path = f"confirmation_{safe_name}_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.info("Screenshot saved: %s", screenshot_path)
        result["screenshot"] = screenshot_path
    except Exception as exc:
        logger.warning("Screenshot failed: %s", exc)

    try:
        body = driver.find_element(By.TAG_NAME, "body").text
        parsed = parse_confirmation_text(body)
        url_info = parse_confirmation_url(driver.current_url)

        if parsed["reference"]:
            result["reference"] = parsed["reference"]
            logger.info("Booking reference found: %s", result["reference"])
        if parsed["exam_date"]:
            result["exam_date"] = parsed["exam_date"]
        if parsed["exam_time"]:
            result["exam_time"] = parsed["exam_time"]
        if parsed["exam_level"]:
            result["exam_level"] = parsed["exam_level"]
        if parsed["exam_city"]:
            result["exam_city"] = parsed["exam_city"]
        if url_info.get("booking_reference_url"):
            result["url_reference"] = url_info["booking_reference_url"]

        result["status"] = parsed.get("status", "unknown")
        logger.info("Confirmation parsed: %s", summarize_confirmation(parsed))
    except Exception as exc:
        logger.warning("Error reading confirmation page: %s", exc)

    return result


def get_exam_url(level: str) -> str:
    level = level.upper().strip()
    return EXAM_URLS.get(level, EXAM_URLS["A1"])


def run_student_flow(student: Dict[str, str], use_headless: bool, logger: logging.Logger,
                     stop_event: threading.Event = None, proxy: Optional[str] = None,
                     immediate: bool = False) -> Dict[str, str]:
    name = student.get("name", "Unknown")
    email = student.get("email", "")
    password = student.get("password", "")
    level = student.get("level", student.get("exam_level", ""))
    city = student.get("city", "Karachi")
    booking_time_str = student.get("booking_datetime", "")

    if stop_event is None:
        stop_event = threading.Event()

    # Scheduled mode: wait until booking time (skip if immediate)
    if not immediate:
        if not scheduled_wait(booking_time_str, logger, stop_event):
            return {"name": name, "email": email, "level": level, "city": city, "status": "stopped"}

    # Pick a proxy for this student (rotation via ProxyRotator)
    assigned_proxy = proxy
    if not assigned_proxy:
        assigned_proxy = PROXY_ROTATOR.get()
        if assigned_proxy:
            logger.info("Assigned proxy: %s", assigned_proxy)

    logger.info("=" * 60)
    logger.info("STARTING STUDENT: %s | %s | %s | %s", name, email, level, city)
    logger.info("=" * 60)

    exam_url = get_exam_url(level)
    exam_dt = parse_exam_time_str(booking_time_str) if booking_time_str else dt.datetime.now()

    student_key = f"{name}|{level}|{city}"
    resume_step = db.get_checkpoint(student_key)
    if resume_step > 0:
        logger.info("Resuming from checkpoint step %d", resume_step)

    driver = None
    result = {"name": name, "email": email, "level": level, "city": city, "status": "failed"}

    try:
        driver = create_driver(use_headless, logger, proxy=assigned_proxy)
        logger.info("Monitoring URL: %s", exam_url)
        logger.info("Booking time: %s", booking_time_str)
        logger.info("Burst window: %s to %s",
                    (exam_dt - dt.timedelta(seconds=BURST_BEFORE_SECONDS)).strftime("%H:%M:%S"),
                    (exam_dt + dt.timedelta(seconds=BURST_AFTER_SECONDS)).strftime("%H:%M:%S"))

        step1_done = False
        page_loaded = False
        consecutive_errors = 0

        logger.info("══ STEP 1: Waiting for 'Book Now' button ══")
        while True:
            if stop_event.is_set():
                logger.warning("Stop requested by user. Aborting.")
                result["status"] = "stopped"
                db.clear_checkpoint(student_key)
                return result

            if not CIRCUIT_BREAKER.allow_request():
                logger.warning("Circuit breaker open — pausing until cooldown expires")
                if not CIRCUIT_BREAKER.wait_until_allowed(poll=5.0, stop_event=stop_event):
                    result["status"] = "stopped"
                    return result
                continue

            burst = exam_dt - dt.timedelta(seconds=BURST_BEFORE_SECONDS) <= dt.datetime.now() <= exam_dt + dt.timedelta(seconds=BURST_AFTER_SECONDS)

            try:
                if burst and page_loaded:
                    driver.refresh()
                else:
                    driver.get(exam_url)

                wait_for_document_ready(driver, timeout=15 if burst else 30)
                page_loaded = True

                if not burst and is_blocked_response(driver):
                    CIRCUIT_BREAKER.record_failure()
                    cd = long_cooldown()
                    logger.warning("Block detected. Cooling down %ss", cd)
                    for _ in range(cd):
                        if stop_event.is_set():
                            result["status"] = "stopped"
                            return result
                        time.sleep(1)
                    page_loaded = False
                    continue

                try:
                    wait_for_finder(driver, timeout=10 if burst else 40)
                except TimeoutException:
                    if burst:
                        time.sleep(BURST_CRASH_RETRY)
                        continue
                    raise

                buttons = find_book_buttons(driver)
                logger.info("Found %d clickable button(s).", len(buttons))

                target_button = pick_preferred_button(buttons, city)

                if target_button is None:
                    now = dt.datetime.now()
                    if burst and now < exam_dt:
                        gap = BURST_PRE_POLL
                    elif burst:
                        gap = random.uniform(BURST_POST_POLL_MIN, BURST_POST_POLL_MAX)
                    else:
                        gap = max(20, DEFAULT_POLL_INTERVAL + random.randint(-10, 15))
                    # Sleep in small chunks so stop_event is responsive
                    for _ in range(int(gap)):
                        if stop_event.is_set():
                            result["status"] = "stopped"
                            return result
                        time.sleep(1)
                    continue

                logger.info("★ STEP 1 DONE: 'Book Now' found! Clicking...")
                notify(f"Slot found for {name}", f"Exam: {level} | City: {city}", logger)
                human_move_and_click(driver, target_button)
                enforce_single_tab(driver)
                CIRCUIT_BREAKER.record_success()
                consecutive_errors = 0
                step1_done = True
                db.save_checkpoint(student_key, 1)
                break

            except (TimeoutException, StaleElementReferenceException, NoSuchElementException) as exc:
                consecutive_errors += 1
                gap = BURST_CRASH_RETRY if burst else bounded_backoff(consecutive_errors)
                logger.warning("Selenium error: %s. Retry in %.1fs", exc, gap)
                time.sleep(gap)
                page_loaded = False
            except WebDriverException as exc:
                CIRCUIT_BREAKER.record_failure()
                consecutive_errors += 1
                gap = BURST_CRASH_RETRY * 2 if burst else bounded_backoff(consecutive_errors, base=5, cap=120)
                logger.error("WebDriver error: %s. Retry in %.1fs", exc, gap)
                time.sleep(gap)
                page_loaded = False
            except Exception as exc:
                logger.exception("Unexpected error: %s", exc)
                time.sleep(BURST_CRASH_RETRY)
                page_loaded = False

        if not step1_done:
            raise RuntimeError("Step 1 failed after all retries")

        random_human_delay(0.5, 1.0)
        if stop_event.is_set():
            logger.warning("Stop requested by user. Aborting.")
            result["status"] = "stopped"; return result

        if resume_step >= 2:
            logger.info("⏩ Skipping STEP 2 (already completed)")
        else:
            logger.info("══ STEP 2: Clicking Continue ══")
            click_continue_button(driver, logger)
            enforce_single_tab(driver)
            logger.info("★ STEP 2 DONE")
            db.save_checkpoint(student_key, 2)

        random_human_delay(0.5, 1.0)
        if stop_event.is_set():
            logger.warning("Stop requested by user. Aborting.")
            result["status"] = "stopped"; return result

        if resume_step >= 3:
            logger.info("⏩ Skipping STEP 3 (already completed)")
        else:
            logger.info("══ STEP 3: Clicking Book for Myself ══")
            click_book_for_myself(driver, logger)
            enforce_single_tab(driver)
            logger.info("★ STEP 3 DONE")
            db.save_checkpoint(student_key, 3)

        random_human_delay(0.5, 1.0)
        if stop_event.is_set():
            logger.warning("Stop requested by user. Aborting.")
            result["status"] = "stopped"; return result

        if resume_step >= 4:
            logger.info("⏩ Skipping STEP 4 (already completed)")
        else:
            if email and password:
                logged_in = login_to_goethe(driver, email, password, logger)
                if not logged_in:
                    logger.warning("Login step failed or skipped. Attempting form fill anyway.")
                    driver.save_screenshot(f"debug_login_{name}.png")
            else:
                logger.warning("No credentials provided — skipping login automation.")
                driver.save_screenshot(f"debug_no_creds_{name}.png")
            db.save_checkpoint(student_key, 4)

        random_human_delay(0.5, 1.0)
        #random_scroll(driver)
        if stop_event.is_set():
            logger.warning("Stop requested by user. Aborting.")
            result["status"] = "stopped"; return result

        if resume_step >= 5:
            logger.info("⏩ Skipping STEP 5 (already completed)")
        else:
            # ── CAPTCHA check before form fill ──
            captcha_found = detect_captcha(driver)
            if captcha_found:
                logger.info("CAPTCHA detected (%s), attempting to solve...", captcha_found)
                solve_captcha(driver, logger)

            form_ok = fill_registration_form(driver, student, logger)
            if not form_ok:
                logger.warning("Form fill had issues. Proceeding to capture state.")
                driver.save_screenshot(f"debug_form_{name}.png")
            db.save_checkpoint(student_key, 5)

        random_human_delay(0.3, 0.8)
        #random_mouse_wander(driver)

        conf = capture_confirmation(driver, name, logger)
        result.update(conf)
        result["status"] = conf.get("status", "submitted")
        db.clear_checkpoint(student_key)

        if assigned_proxy:
            PROXY_ROTATOR.mark_success(assigned_proxy)

        notifications.notify_all(f"Booking complete: {name}", f"{level} | {city} | Status: {result['status']}", logger)

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        result["status"] = "interrupted"
    except Exception as exc:
        CIRCUIT_BREAKER.record_failure()
        logger.exception("Flow error for %s: %s", name, exc)
        if assigned_proxy:
            PROXY_ROTATOR.mark_failed(assigned_proxy)
        notify(f"❌ Booking failed: {name}", str(exc), logger)
        if driver:
            try:
                driver.save_screenshot(f"error_{name}.png")
            except Exception:
                pass
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass

    logger.info("=" * 60)
    logger.info("RESULT for %s: %s", name, result["status"])
    logger.info("=" * 60)
    return result


def main() -> int:
    args = parse_args()
    logger = setup_logger()

    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    if args.telegram_token:
        TELEGRAM_BOT_TOKEN = args.telegram_token
    if args.telegram_chat_id:
        TELEGRAM_CHAT_ID = args.telegram_chat_id

    logger.warning("=== Goethe Booking Bot - Personal Use Only ===")

    students = load_all_students(args.config)
    db.save_students(students)
    logger.info("Loaded %d student(s)", len(students))

    for i, s in enumerate(students):
        logger.info("  Student %d: %s | %s | %s | Booking: %s",
                    i + 1, s.get("name"), s.get("level", s.get("exam_level", "")), s.get("city"), s.get("booking_datetime"))

    threads = []
    results_list = []
    results_lock = threading.Lock()

    def run_one(s: Dict):
        key = f"{s.get('name', '?')}|{s.get('level', s.get('exam_level', '?'))}|{s.get('city', '?')}"
        student_logger = setup_logger(f"bot_{s.get('name', 'unknown')}_{s.get('level', '?')}")
        result = smart_retry(s, args.headless, student_logger, threading.Event())
        with results_lock:
            results_list.append(result)
        db.update_student_status(key, result.get("status", "failed"), result)

    for student in students:
        t = threading.Thread(target=run_one, args=(student,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    logger.info("=" * 60)
    logger.info("ALL STUDENTS COMPLETE")
    logger.info("=" * 60)

    summary_lines = []
    for r in results_list:
        line = f"{r.get('name', '?')}: {r.get('status', '?')}"
        if r.get("reference"):
            line += f" (Ref: {r['reference']})"
        summary_lines.append(line)
        logger.info(line)

    summary = "\n".join(summary_lines)
    notifications.notify_all("Booking Summary", summary, logger)

    print("\n" + "=" * 50)
    print("  BOOKING SUMMARY:")
    for line in summary_lines:
        print(f"  {line}")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
