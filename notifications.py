"""
Multi-channel notifications: Telegram + Email + WhatsApp.
"""

from __future__ import annotations

import logging
import os
import smtplib
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from typing import Optional

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8928235858:AAEOgYkyuiMBA_e0gEMnFdjkvSW5uQ4hJMA")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6137210278")

EMAIL_SMTP_HOST = os.environ.get("EMAIL_SMTP_HOST", "")
EMAIL_SMTP_PORT = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASS = os.environ.get("EMAIL_PASS", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")




def send_telegram(message: str, logger: logging.Logger) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        urllib.request.urlopen(req, timeout=10)
        logger.info("Telegram sent")
        return True
    except Exception as exc:
        logger.warning("Telegram failed: %s", exc)
        return False


def send_email(subject: str, body: str, logger: logging.Logger) -> bool:
    if not all([EMAIL_SMTP_HOST, EMAIL_USER, EMAIL_PASS, EMAIL_TO]):
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM or EMAIL_USER
        msg["To"] = EMAIL_TO
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=15) as s:
            s.starttls()
            s.login(EMAIL_USER, EMAIL_PASS)
            s.send_message(msg)
        logger.info("Email sent to %s", EMAIL_TO)
        return True
    except Exception as exc:
        logger.warning("Email failed: %s", exc)
        return False





def notify_all(title: str, message: str, logger: logging.Logger):
    full = f"<b>{title}</b>\n{message}"
    logger.info("NOTIFY: %s - %s", title, message)
    send_telegram(full, logger)
    send_email(title, message, logger)
