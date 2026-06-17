"""Uptime monitor — pings the health endpoint periodically.

Usage:
  python scripts/uptime_monitor.py                    # single check
  python scripts/uptime_monitor.py --watch            # continuous every 60s
  python scripts/uptime_monitor.py --webhook URL      # alert on failure
"""
import argparse
import sys
import time
import urllib.request
import json

HEALTH_URL = "https://goethe-booking-bot-production-092f.up.railway.app/api/v1/health"


def check(url: str) -> dict:
    try:
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read().decode())
        return {"ok": data.get("status") == "ok", "data": data, "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": str(e)}


def send_alert(webhook: str, msg: str):
    if not webhook:
        return
    try:
        payload = json.dumps({"text": msg}).encode()
        urllib.request.urlopen(webhook, data=payload, timeout=10)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Uptime monitor")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--webhook", default="", help="Alert webhook URL")
    parser.add_argument("--url", default=HEALTH_URL, help="Health endpoint URL")
    args = parser.parse_args()

    if args.watch:
        failures = 0
        print(f"Uptime monitor started — checking every {args.interval}s")
        while True:
            result = check(args.url)
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            if result["ok"]:
                print(f"{ts}  OK  uptime={result['data'].get('uptime_seconds', '?')}s")
                failures = 0
            else:
                failures += 1
                print(f"{ts}  FAIL  {result['error']}")
                if failures >= 3:
                    send_alert(args.webhook, f"Uptime Alert: {failures} consecutive failures. URL: {args.url}")
            time.sleep(args.interval)
    else:
        result = check(args.url)
        if result["ok"]:
            print(f"OK — uptime={result['data'].get('uptime_seconds', '?')}s")
            sys.exit(0)
        else:
            print(f"FAIL — {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
