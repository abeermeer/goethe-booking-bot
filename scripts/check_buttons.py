"""Login and check booking availability for A1/B1 using real bot helpers."""
import sys, os, time, logging
sys.path.insert(0, r'C:\Users\brosp\Downloads\goethe-bot')
os.chdir(r'C:\Users\brosp\Downloads\goethe-bot')

from booking_helper import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("check")

EMAIL = "abeermeer7979@gmail.com"
PASSWORD = "hf?3Ru8UkhfKw*X"

level_urls = {
    "A1": "https://www.goethe.de/ins/pk/en/spr/prf/gzsd1.cfm",
    "B1": "https://www.goethe.de/ins/pk/en/spr/prf/gzb1.cfm",
}

for level in ["A1", "B1"]:
    print(f"\n{'='*50}")
    print(f"Checking {level}...")
    print('='*50)

    driver = create_driver(use_headless=True, logger=logger)
    try:
        url = level_urls[level]

        # Step 1: Go to exam page
        print("Step 1: Load exam page...")
        driver.get(url)
        wait_for_document_ready(driver, 20)
        time.sleep(3)
        print(f"  Title: {driver.title[:80]}")

        # Step 2: Go directly to CAS login
        print("Step 2: Navigate to CAS login...")
        driver.get("https://www.goethe.de/services/cas/login/goethe/?locale=en&langId=1&module=default")
        time.sleep(3)
        wait_for_document_ready(driver, 20)

        print(f"  Login page URL: {driver.current_url[:80]}")

        # Step 3: Dismiss Usercentrics cookie overlay, then login
        print("Step 3: Dismiss cookie consent...")
        try:
            driver.execute_script("document.querySelector('#usercentrics-root')?.remove()")
            time.sleep(1)
            # Also try clicking deny/accept
            for btn_text in ["Accept", "Deny", "Decline", "Accept all", "Deny all"]:
                try:
                    btn = driver.find_element(By.XPATH, f"//button[contains(text(), '{btn_text}')]")
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click()", btn)
                        time.sleep(1)
                        break
                except:
                    pass
        except:
            pass

        print("Step 4: Fill login form...")
        try:
            email_el = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_el.clear()
            email_el.send_keys(EMAIL)
            pwd_el = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            pwd_el.clear()
            pwd_el.send_keys(PASSWORD)
            # Use JS to click submit bypassing overlay
            submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            driver.execute_script("arguments[0].click()", submit)
            time.sleep(5)
            wait_for_document_ready(driver, 20)
            print(f"  Post-login URL: {driver.current_url[:80]}")
        except Exception as e:
            print(f"  Login failed: {e}")
            driver.quit()
            continue

        # Step 5: Go to exam page (now logged in)
        print(f"Step 5: Go to {level} page (logged in)...")
        driver.get(url)
        time.sleep(5)
        wait_for_document_ready(driver, 20)
        time.sleep(5)
        print(f"  Title: {driver.title[:80]}")

        # Step 6: Check for booking buttons
        print("Step 6: Check for Book Now buttons...")
        buttons = find_book_buttons(driver)
        print(f"  Found {len(buttons)} Book Now button(s)")

        # Dump any button-like elements with booking text
        for el in driver.find_elements(By.CSS_SELECTOR, "a, button, .btn, [role='button']"):
            txt = el.text.strip()
            if txt and any(k in txt.lower() for k in ['book', 'buchen', 'jetzt', 'platz', 'register', 'anmeld', 'freie']):
                print(f"  Keyword match: '{txt[:80]}'")

        # Check body text for availability hints
        body = driver.find_element(By.TAG_NAME, "body").text
        for line in body.split('\n'):
            if any(k in line.lower() for k in ['book', 'platz', 'free', 'frei', 'available', 'buchen', 'register', 'anmeldung', 'noch', 'ausgebucht', 'voll']):
                print(f"  Text: '{line.strip()[:120]}'")

        if buttons:
            print(">>> ✅ BOOKING AVAILABLE!")
        else:
            print(">>> ❌ NO BOOKING SLOTS AVAILABLE")

        # Check finder container
        try:
            finder = driver.find_element(By.CSS_SELECTOR, ".finder-container, .exam-finder, [class*='finder']")
            print(f"  Finder visible: {finder.is_displayed()}")
            finder_html = finder.get_attribute('outerHTML')[:500]
            print(f"  Finder HTML: {finder_html[:200]}")
        except:
            print("  No finder container found")

    except Exception as e:
        print(f"  ERROR: {e}")
    finally:
        driver.quit()
        time.sleep(2)

print("\nDone!")
