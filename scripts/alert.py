"""Alerting utility — sends alerts via Telegram.

Usage:
  python scripts/alert.py "Bot failed to book Student X"
  python scripts/alert.py --critical "Circuit breaker opened"
"""
import argparse
import os
import sys
import urllib.request
import json

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}).encode()
    try:
        urllib.request.urlopen(url, data=payload, timeout=10)
        return True
    except Exception as e:
        print(f"Error sending alert: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Send alerts")
    parser.add_argument("message", help="Alert message")
    parser.add_argument("--critical", action="store_true", help="Mark as critical")
    args = parser.parse_args()

    prefix = "🔴 CRITICAL: " if args.critical else "⚠️ ALERT: "
    full_msg = prefix + args.message

    print(f"Alert: {full_msg}")
    send_telegram(full_msg)


if __name__ == "__main__":
    main()
