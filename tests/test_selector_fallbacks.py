from selenium.webdriver.common.by import By

from selector_fallbacks import (
    ELEMENT_SELECTORS,
    LOGIN_ERROR_SELECTORS,
)


def test_element_selectors_defined_for_all_keys():
    keys = [
        "finder_container", "book_button", "login_email", "login_password",
        "login_submit", "login_checkbox_stay", "form_name", "form_dob",
        "form_place_of_birth", "form_address", "form_phone", "form_level",
        "form_terms", "form_submit", "continue_button", "book_for_myself",
    ]
    for key in keys:
        assert key in ELEMENT_SELECTORS, f"Missing selector key: {key}"
        assert len(ELEMENT_SELECTORS[key]) >= 1, f"Need at least 1 selector for {key}"
        assert len(ELEMENT_SELECTORS[key]) >= 2, f"Need >=2 fallbacks for {key} (has {len(ELEMENT_SELECTORS[key])})"


def test_selectors_have_valid_by_types():
    valid_by_types = {getattr(By, attr) for attr in dir(By) if not attr.startswith("_")}
    for key, selectors in ELEMENT_SELECTORS.items():
        for by, selector in selectors:
            assert by in valid_by_types, f"Invalid By type '{by}' in {key}"
            assert isinstance(selector, str) and len(selector) > 0, f"Empty selector in {key}"


def test_login_error_selectors_valid():
    for by, selector in LOGIN_ERROR_SELECTORS:
        valid = hasattr(By, by.replace("By.", "")) if isinstance(by, str) else True
        assert isinstance(selector, str) and len(selector) > 0
