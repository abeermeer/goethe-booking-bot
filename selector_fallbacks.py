from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple

from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ELEMENT_SELECTORS: Dict[str, List[Tuple[str, str]]] = {
    "finder_container": [
        (By.CSS_SELECTOR, "#pr_finder_9523459"),
        (By.CSS_SELECTOR, ".pr-finder"),
        (By.XPATH, "//*[contains(@id, 'pr_finder')]"),
        (By.CSS_SELECTOR, "[class*='finder']"),
    ],
    "book_button": [
        (By.XPATH, (
            "//*[self::a or self::button]"
            "[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'select module')"
            " or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book')"
            " or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buchen')"
            " or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'weiter')]"
            "[contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'standard')]"
            "[not(contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'disabled'))]"
        )),
        (By.CSS_SELECTOR, "a.standard, button.standard"),
        (By.XPATH, "//*[self::a or self::button][contains(text(), 'Select') or contains(text(), 'Book') or contains(text(), 'book')]"),
        (By.XPATH, "//*[self::a or self::button][contains(@href, 'book') or contains(@href, 'buchen')]"),
    ],
    "bookable_from_text": [
        (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bookable from')]"),
        (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bookable from')]"),
    ],
    "coe_wicket_page": [
        (By.CSS_SELECTOR, "[id*='wicket']"),
        (By.XPATH, "//*[contains(@class, 'wicket')]"),
        (By.XPATH, "//*[contains(text(), 'session') or contains(text(), 'timeout') or contains(text(), 'expired')]"),
        (By.XPATH, "//*[contains(@id, 'coesession')]"),
    ],
    "first_name": [
        (By.CSS_SELECTOR, "input[name*='first']"),
        (By.CSS_SELECTOR, "input[id*='first']"),
        (By.CSS_SELECTOR, "input[name*='vorname']"),
        (By.XPATH, "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'first')]"),
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'first name')]/following::input[1]"),
    ],
    "surname": [
        (By.CSS_SELECTOR, "input[name*='surname']"),
        (By.CSS_SELECTOR, "input[name*='last']"),
        (By.CSS_SELECTOR, "input[id*='surname']"),
        (By.CSS_SELECTOR, "input[name*='nachname']"),
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'surname')]/following::input[1]"),
    ],
    "dob_day": [
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'date of birth')]/following::select[1]"),
        (By.CSS_SELECTOR, "select[name*='day']"),
        (By.CSS_SELECTOR, "select[name*='tag']"),
    ],
    "dob_month": [
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'date of birth')]/following::select[2]"),
        (By.CSS_SELECTOR, "select[name*='month']"),
        (By.CSS_SELECTOR, "select[name*='monat']"),
    ],
    "dob_year": [
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'date of birth')]/following::select[3]"),
        (By.CSS_SELECTOR, "select[name*='year']"),
        (By.CSS_SELECTOR, "select[name*='jahr']"),
    ],
    "email_field": [
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.CSS_SELECTOR, "input[name='e-mail']"),
        (By.CSS_SELECTOR, "#email"),
    ],
    "country_dropdown": [
        (By.CSS_SELECTOR, "select[name*='country']"),
        (By.CSS_SELECTOR, "select[id*='country']"),
        (By.CSS_SELECTOR, "select[name*='land']"),
    ],
    "postal_code": [
        (By.CSS_SELECTOR, "input[name*='postal']"),
        (By.CSS_SELECTOR, "input[name*='zip']"),
        (By.CSS_SELECTOR, "input[name*='plz']"),
    ],
    "location_city": [
        (By.CSS_SELECTOR, "input[name*='location']"),
        (By.CSS_SELECTOR, "input[name*='city']"),
        (By.CSS_SELECTOR, "input[name*='ort']"),
        (By.CSS_SELECTOR, "input[name*='stadt']"),
    ],
    "street_field": [
        (By.CSS_SELECTOR, "input[name*='street']"),
        (By.CSS_SELECTOR, "input[name*='strasse']"),
    ],
    "house_number": [
        (By.CSS_SELECTOR, "input[name*='house']"),
        (By.CSS_SELECTOR, "input[name*='haus']"),
        (By.CSS_SELECTOR, "input[name*='number']"),
    ],
    "additional_address": [
        (By.CSS_SELECTOR, "input[name*='additional']"),
        (By.CSS_SELECTOR, "input[name*='address2']"),
        (By.CSS_SELECTOR, "input[name*='addition']"),
    ],
    "phone_prefix": [
        (By.CSS_SELECTOR, "select[name*='phone']"),
        (By.CSS_SELECTOR, "select[name*='code']"),
        (By.CSS_SELECTOR, "select[name*='vorwahl']"),
    ],
    "motivation_dropdown": [
        (By.CSS_SELECTOR, "select[name*='motivation']"),
        (By.CSS_SELECTOR, "select[id*='motivation']"),
    ],
    "invoice_option": [
        (By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'invoice')]"),
        (By.CSS_SELECTOR, "[class*='invoice']"),
        (By.CSS_SELECTOR, "[class*='rechnung']"),
    ],
    "promo_code": [
        (By.CSS_SELECTOR, "input[name*='promo']"),
        (By.CSS_SELECTOR, "input[name*='gutschein']"),
        (By.CSS_SELECTOR, "input[name*='coupon']"),
        (By.CSS_SELECTOR, "input[id*='promo']"),
    ],
    "apply_promo": [
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]"),
        (By.CSS_SELECTOR, "button[name*='apply']"),
    ],
    "confirm_order": [
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]"),
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'order')]"),
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]"),
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buchen')]"),
    ],
    "login_email": [
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[name='email']"),
        (By.CSS_SELECTOR, "input[name='username']"),
        (By.CSS_SELECTOR, "#email"),
        (By.CSS_SELECTOR, "#username"),
        (By.XPATH, "//input[@type='text' or @type='email']"),
    ],
    "login_password": [
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.CSS_SELECTOR, "input[name='password']"),
        (By.CSS_SELECTOR, "#password"),
        (By.CSS_SELECTOR, "#passwort"),
    ],
    "login_submit": [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.CSS_SELECTOR, ".btn-submit"),
        (By.CSS_SELECTOR, "#login-button"),
        (By.CSS_SELECTOR, ".login-button"),
    ],
    "login_checkbox_stay": [
        (By.CSS_SELECTOR, "input[type='checkbox']"),
        (By.XPATH, "//input[@type='checkbox']"),
    ],
    "form_name": [
        (By.CSS_SELECTOR, "input[name*='name']"),
        (By.CSS_SELECTOR, "input[id*='name']"),
        (By.CSS_SELECTOR, "input[placeholder*='Name']"),
        (By.CSS_SELECTOR, "input[placeholder*='name']"),
    ],
    "form_dob": [
        (By.CSS_SELECTOR, "input[name*='birth']"),
        (By.CSS_SELECTOR, "input[id*='birth']"),
        (By.CSS_SELECTOR, "input[name*='geburt']"),
        (By.CSS_SELECTOR, "input[type='date']"),
    ],
    "form_place_of_birth": [
        (By.CSS_SELECTOR, "input[name*='place']"),
        (By.CSS_SELECTOR, "input[id*='place']"),
        (By.CSS_SELECTOR, "input[name*='ort']"),
        (By.CSS_SELECTOR, "input[placeholder*='Place']"),
        (By.CSS_SELECTOR, "input[placeholder*='Birth']"),
    ],
    "form_address": [
        (By.CSS_SELECTOR, "textarea[name*='address']"),
        (By.CSS_SELECTOR, "input[name*='address']"),
        (By.CSS_SELECTOR, "textarea[id*='address']"),
    ],
    "form_phone": [
        (By.CSS_SELECTOR, "input[name*='phone']"),
        (By.CSS_SELECTOR, "input[id*='phone']"),
        (By.CSS_SELECTOR, "input[name*='telefon']"),
        (By.CSS_SELECTOR, "input[name*='mobile']"),
        (By.CSS_SELECTOR, "input[type='tel']"),
    ],
    "form_level": [
        (By.CSS_SELECTOR, "select[name*='level']"),
        (By.CSS_SELECTOR, "select[id*='level']"),
        (By.CSS_SELECTOR, "select[name*='stufe']"),
        (By.CSS_SELECTOR, "select[name*='kurs']"),
    ],
    "form_terms": [
        (By.CSS_SELECTOR, "input[type='checkbox']"),
        (By.CSS_SELECTOR, ".terms input"),
        (By.CSS_SELECTOR, ".agb input"),
        (By.CSS_SELECTOR, "input[name*='agree']"),
        (By.CSS_SELECTOR, "input[name*='confirm']"),
    ],
    "form_submit": [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.CSS_SELECTOR, ".btn-submit"),
        (By.CSS_SELECTOR, ".submit-button"),
    ],
    "continue_button": [
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]"),
        (By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]"),
        (By.XPATH, "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]"),
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'weiter')]"),
    ],
    "book_for_myself": [
        (By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'myself')]"),
        (By.XPATH, "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'myself')]"),
        (By.XPATH, "//*[self::a or self::button][contains(@href, 'book') and contains(@href, 'myself')]"),
    ],
}

LOGIN_ERROR_SELECTORS = [
    (By.CSS_SELECTOR, ".error"),
    (By.CSS_SELECTOR, ".alert"),
    (By.CSS_SELECTOR, ".message-error"),
    (By.CSS_SELECTOR, ".errortext"),
    (By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'alert')]"),
]


def find_element_fallback(driver, element_key: str, timeout: int = 10, logger: Optional[logging.Logger] = None) -> Optional[WebElement]:
    selectors = ELEMENT_SELECTORS.get(element_key)
    if not selectors:
        if logger:
            logger.error("Unknown element key: %s", element_key)
        return None
    per_selector_timeout = max(timeout / len(selectors), 1)
    for by, selector in selectors:
        try:
            element = WebDriverWait(driver, per_selector_timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            if element and element.is_displayed():
                return element
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            continue
    return None


def find_elements_fallback(driver, element_key: str, timeout: int = 10, logger: Optional[logging.Logger] = None) -> List[WebElement]:
    selectors = ELEMENT_SELECTORS.get(element_key)
    if not selectors:
        return []
    per_selector_timeout = max(timeout / len(selectors), 1)
    for by, selector in selectors:
        try:
            elements = WebDriverWait(driver, per_selector_timeout).until(
                EC.presence_of_all_elements_located((by, selector))
            )
            visible = [e for e in elements if e.is_displayed()]
            if visible:
                return visible
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            continue
    return []


def wait_for_any_selector(driver, element_key: str, timeout: int = 15, logger: Optional[logging.Logger] = None) -> Optional[WebElement]:
    selectors = ELEMENT_SELECTORS.get(element_key)
    if not selectors:
        return None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for by, selector in selectors:
            try:
                elements = driver.find_elements(by, selector)
                visible = [e for e in elements if e.is_displayed()]
                if visible:
                    return visible[0]
            except Exception:
                continue
        time.sleep(0.5)
    return None
