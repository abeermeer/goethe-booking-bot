"""Form scanner — runs locally on your laptop (bypasses reCAPTCHA issue on Railway).
Usage: python scripts/scan_form_local.py --email YOUR_EMAIL --password YOUR_PASSWORD"""
import sys, os, time, logging, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from booking_helper import scan_booking_form, get_last_login_error

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("form_scan")

parser = argparse.ArgumentParser()
parser.add_argument("--email", default="abeermeer7979@gmail.com")
parser.add_argument("--password", default="hf?3Ru8UkhfKw*X")
args = parser.parse_args()

student = {
    "name": "Abeer Meer",
    "email": args.email,
    "password": args.password,
    "level": "A1",
    "city": "Karachi",
    "booking_datetime": "2026-06-19T10:23",
}

print("=" * 60)
print("FORM SCANNER — LOCAL")
print("=" * 60)
print(f"Email: {args.email}")
print(f"Level: A1 | City: Karachi")
print("Opening browser (NOT headless)...")
print()

result = scan_booking_form(student, logger)

print()
print("=" * 60)
print("RESULT")
print("=" * 60)
if result.get("ok"):
    print(f"✅ {result['message']}")
    print(f"Known selectors matched: {result['known_keys_found']}/{result['known_keys_total']}")
    if result.get("missing_keys"):
        print(f"⚠️  Missing keys: {', '.join(result['missing_keys'])}")
    print()
    print("Form fields found:")
    for f in result.get("fields", []):
        label = f' label="{f["label"]}"' if f.get("label") else ""
        print(f'  <{f["tag"]}{" type="+f["type"] if f.get("type") else ""} name="{f["name"]}" id="{f["id"]}" placeholder="{f["placeholder"]}"{label}>')
else:
    print(f"❌ {result.get('message', 'Unknown error')}")
    if "login" in result.get("message", "").lower():
        print("   (Login failed — check email/password)")

print()
if result.get("ok"):
    print("✅ Form scanner complete. Selectors look good!" if result["known_keys_found"] == result["known_keys_total"]
          else f"⚠️  {result['known_keys_total'] - result['known_keys_found']} selectors need updating.")
else:
    print("❌ Form scanner failed. Fix and retry.")
