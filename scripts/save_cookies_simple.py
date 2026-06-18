"""Simple cookie saver — no undetected_chromedriver, works with any Chrome."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

EMAIL = "abeermeer7979@gmail.com"
PASSWORD = "hf?3Ru8UkhfKw*X"
TOKEN = "iColX1q-G5m46A8xL4uCeSFMdSfgUcbZB7E8rnryI_sEpjCP7QrFh4A0mRqvwk4D"
RAILWAY = "https://goethe-booking-bot-production-092f.up.railway.app"

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280,720")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--lang=en-US,en")
options.add_experimental_option("prefs", {"intl.accept_languages": "en-US,en"})
# Use a clean profile
profile_dir = os.path.join(os.environ["USERPROFILE"], "goethe-bot-profiles", "cookie_saver")
os.makedirs(profile_dir, exist_ok=True)
options.add_argument(f"--user-data-dir={profile_dir}")

print("Starting Chrome...")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("Opening Goethe login...")
    driver.get("https://login.goethe.de/cas/login")
    time.sleep(3)

    # Dismiss cookie consent overlay
    try:
        driver.execute_script("document.getElementById('usercentrics-root')?.remove()")
    except Exception:
        pass
    time.sleep(1)

    email_el = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='username']")
    email_el.send_keys(EMAIL)
    time.sleep(1)

    pwd_el = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    pwd_el.send_keys(PASSWORD)
    time.sleep(1)

    # Click submit via JS to bypass any overlay
    submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click()", submit)
    time.sleep(5)

    if "login" in driver.current_url.lower():
        print("[FAILED] Login failed - still on login page")
        driver.quit()
        sys.exit(1)

    print("[OK] Login successful! Extracting cookies...")
    time.sleep(2)
    cookies = driver.get_cookies()
    print(f"Got {len(cookies)} cookies")

    import urllib.request
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}
    data = json.dumps({"cookies": cookies}).encode()
    req = urllib.request.Request(f"{RAILWAY}/api/goethe-cookies", data=data, headers=headers, method="POST")
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read())
    if result.get("ok"):
        print(f"\n[OK] {result['count']} cookies saved to Railway!")
        print("=> Form Scanner ab dashboard se ek click mein kaam karega")
    else:
        print(f"\n[FAILED] {result.get('error', 'Unknown')}")
except Exception as e:
    print(f"\n[Error] {e}")
finally:
    driver.quit()
