"""Login to Goethe.de on your laptop, save cookies to Railway.
Run ONCE, then Form Scanner works from dashboard in one click.
Usage: python scripts/save_goethe_cookies.py [--email EMAIL] [--password PASSWORD] [--token AUTH_TOKEN]"""
import sys, os, time, json, logging, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from booking_helper import create_driver, wait_for_document_ready, find_element_fallback, login_to_goethe, type_slowly, random_human_delay
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("cookie_saver")

parser = argparse.ArgumentParser()
parser.add_argument("--email", default="")
parser.add_argument("--password", default="")
parser.add_argument("--token", default="")
parser.add_argument("--railway", default="https://goethe-booking-bot-production-092f.up.railway.app")
args = parser.parse_args()

EMAIL = args.email or input("Goethe email [abeermeer7979@gmail.com]: ").strip() or "abeermeer7979@gmail.com"
PASSWORD = args.password or input("Goethe password: ").strip() or "hf?3Ru8UkhfKw*X"
RAILWAY_URL = args.railway or input("Railway URL [https://goethe-booking-bot-production-092f.up.railway.app]: ").strip() or "https://goethe-booking-bot-production-092f.up.railway.app"
AUTH_TOKEN = args.token or input("Dashboard auth token (from login): ").strip()

print("\nOpening browser...")
driver = create_driver(use_headless=False, logger=logger)
try:
    driver.get("https://login.goethe.de/cas/login")
    wait_for_document_ready(driver)
    random_human_delay()
    print("Logging in...")
    ok = login_to_goethe(driver, EMAIL, PASSWORD, logger)
    if not ok:
        print("\n❌ Login failed! Check email/password.")
        sys.exit(1)
    print("\n✓ Login successful! Extracting cookies...")
    time.sleep(3)
    cookies = driver.get_cookies()
    print(f"Got {len(cookies)} cookies")

    import urllib.request
    token = AUTH_TOKEN
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    data = json.dumps({"cookies": cookies}).encode()
    req = urllib.request.Request(
        f"{RAILWAY_URL}/api/goethe-cookies",
        data=data, headers=headers, method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read())
    if result.get("ok"):
        print(f"\n✅ {result['count']} cookies saved to Railway!")
        print("→ Form Scanner ab dashboard se ek click mein kaam karega")
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown')}")
except Exception as e:
    print(f"\n❌ Error: {e}")
finally:
    driver.quit()
