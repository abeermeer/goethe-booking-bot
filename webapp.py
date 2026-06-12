#!/usr/bin/env python3
"""
Goethe Booking Bot - API Backend
=================================
Flask-based API for the standalone frontend.

Deploy backend anywhere (Railway, Render, Fly.io, VPS).
Frontend (frontend/index.html) deploys on Netlify.

Usage:
  pip install flask
  python webapp.py

Frontend connects via Backend URL input.
"""

from __future__ import annotations

import gc
import hashlib
import hmac
import json
import logging
import os
import queue
import secrets
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from collections import defaultdict

import flask
from flask import Flask, Response, jsonify, request

PROJECT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_DIR))

import booking_helper as bot
import db
import alexa

app = Flask(__name__)

# ── Auth config ──
AUTH_EMAIL = os.environ.get("AUTH_EMAIL", "admin@example.com")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "ADMIN_PASSWORD_REDACTED")
AUTH_SALT = os.environ.get("AUTH_SALT", "goethe-bot-salt-2026")
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "admin@example.com")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PROCESS_START_TIME = time.time()

def _make_token(email: str) -> str:
    raw = f"{email}:{AUTH_SALT}:{int(time.time() / 86400)}"
    return hmac.new(AUTH_SALT.encode(), raw.encode(), hashlib.sha256).hexdigest()

def _check_auth():
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        return False
    expected = _make_token(AUTH_EMAIL)
    return hmac.compare_digest(token, expected)

# ── Global state ──
bot_stop_event = threading.Event()
bot_thread: Optional[threading.Thread] = None
bot_running = False
log_queue: queue.Queue = queue.Queue()
student_status: Dict[str, Dict] = {}  # name -> {status, color, details}
student_results: List[Dict] = []
config_path: str = ""
telegram_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
telegram_chat_id: str = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── Scheduled mode ──
scheduled_start: Optional[str] = None  # ISO datetime string
scheduler_thread: Optional[threading.Thread] = None
scheduler_stop = threading.Event()


class WebLogHandler(logging.Handler):
    def __init__(self, lq: queue.Queue):
        super().__init__()
        self.lq = lq

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        self.lq.put({"time": record.asctime if hasattr(record, 'asctime') else '',
                     "level": record.levelname,
                     "message": msg,
                     "name": record.name})


class DbLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            db.add_log(record.name, record.levelname, msg)
        except Exception:
            pass


class JsonFileHandler(logging.Handler):
    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord):
        try:
            entry = json.dumps({
                "time": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            })
            with self._lock:
                with open(self.path, "a") as f:
                    f.write(entry + "\n")
        except Exception:
            pass


def setup_web_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = WebLogHandler(log_queue)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.addHandler(DbLogHandler())
    json_handler = JsonFileHandler(str(PROJECT_DIR / "bot_logs.ndjson"))
    logger.addHandler(json_handler)
    return logger


def _student_key(s: Dict) -> str:
    return f"{s.get('name', '?')}|{s.get('level', s.get('exam_level', '?'))}|{s.get('city', '?')}"

def run_students_web(students: List[Dict], headless: bool, immediate: bool = False):
    global bot_stop_event, bot_running, student_status, student_results
    bot_stop_event.clear()
    bot_running = True

    db.save_students(students)
    master_logger = setup_web_logger("web_bot")
    master_logger.info("Bot started with %d student(s)", len(students))

    threads = []
    results_lock = threading.Lock()

    def run_one(s: Dict):
        key = _student_key(s)
        name = s.get("name", "Unknown")
        level = s.get("level", s.get("exam_level", "?"))
        student_logger = setup_web_logger(f"bot_{name}_{level}")
        student_status[key] = {"status": "Waiting...", "color": "warning", "details": "Polling for slot"}

        result = bot.smart_retry(
            s, use_headless=headless,
            logger=student_logger,
            stop_event=bot_stop_event,
            immediate=immediate,
        )
        with results_lock:
            student_results.append(result)

        db.update_student_status(key, result.get("status", "failed"), result)

        status = result.get("status", "failed")
        if status == "confirmed":
            student_status[key] = {"status": "Confirmed!", "color": "success", "details": f"Ref: {result.get('reference', 'N/A')}"}
        elif status == "submitted":
            student_status[key] = {"status": "Submitted", "color": "success", "details": "Form submitted"}
        elif status == "stopped":
            student_status[key] = {"status": "Stopped", "color": "danger", "details": "Cancelled by user"}
        elif status == "failed":
            student_status[key] = {"status": "Failed", "color": "danger", "details": "Error occurred"}
        else:
            student_status[key] = {"status": status, "color": "warning", "details": ""}

    for s in students:
        key = _student_key(s)
        student_status[key] = {"status": "Starting...", "color": "info", "details": "Launching browser"}
        t = threading.Thread(target=run_one, args=(s,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    bot_running = False
    master_logger.info("All students finished")
    log_queue.put(None)  # Signal SSE stream to end


# ── CORS (allow frontend from anywhere) ──
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    if flask.request.method == "OPTIONS":
        resp.status_code = 200
    return resp


# ── Rate limiter ──
_login_attempts = defaultdict(list)
RATE_LIMIT = 5  # max attempts
RATE_WINDOW = 300  # seconds (5 min)


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < RATE_WINDOW]
    if len(_login_attempts[ip]) >= RATE_LIMIT:
        return False
    _login_attempts[ip].append(now)
    return True


# ── Auth routes ──

@app.route("/api/login", methods=["POST"])
def api_login():
    ip = request.remote_addr or "unknown"
    if not _check_rate_limit(ip):
        return jsonify({"ok": False, "error": "Too many attempts. Try again in 5 minutes."}), 429
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if email == AUTH_EMAIL.lower() and password == AUTH_PASSWORD:
        return jsonify({"ok": True, "token": _make_token(AUTH_EMAIL), "email": AUTH_EMAIL})
    return jsonify({"ok": False, "error": "Invalid email or password"}), 401


@app.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if email == AUTH_EMAIL.lower():
        return jsonify({"ok": True, "message": f"Reset link sent to {SUPPORT_EMAIL}"})
    return jsonify({"ok": True, "message": "If that email is registered, a reset link has been sent"})


def require_auth(f):
    """Decorator to require valid auth token."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if _check_auth():
            return f(*args, **kwargs)
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    return decorated


# ── Routes ──

@app.route("/")
@app.route("/health")
def health():
    uptime_secs = int(time.time() - PROCESS_START_TIME)
    return jsonify({
        "status": "ok",
        "running": bot_running,
        "uptime_seconds": uptime_secs,
        "uptime_human": f"{uptime_secs // 3600}h {(uptime_secs % 3600) // 60}m",
    })


@app.route("/api/status")
@require_auth
def api_status():
    return jsonify({
        "running": bot_running,
        "students": [
            {
                "name": s.get("name", "?"),
                "level": s.get("level", s.get("exam_level", "?")),
                "city": s.get("city", "?"),
                "booking_time": s.get("booking_datetime", "?"),
                "status": student_status.get(_student_key(s), {}).get("status", "Not started"),
                "color": student_status.get(_student_key(s), {}).get("color", "secondary"),
                "details": student_status.get(_student_key(s), {}).get("details", ""),
            }
            for s in _get_loaded_students()
        ],
        "config_loaded": len(_get_loaded_students()) > 0,
    })


@app.route("/api/config", methods=["GET"])
@require_auth
def api_get_config():
    students = _get_loaded_students()
    return jsonify({
        "path": config_path,
        "count": len(students),
        "students": [
            {k: v for k, v in s.items()}
            for s in students
        ],
    })


@app.route("/api/config/load", methods=["POST"])
@require_auth
def api_load_config():
    global config_path
    data = request.get_json(silent=True) or {}
    path = data.get("path", str(PROJECT_DIR / "config.csv"))
    if not Path(path).exists():
        return jsonify({"ok": False, "error": "File not found"}), 400
    try:
        bot.load_all_students(path)
        config_path = path
        return jsonify({"ok": True, "path": path, "count": len(bot.load_all_students(path))})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/config/upload", methods=["POST"])
@require_auth
def api_config_upload():
    global config_path
    csv_content = request.get_data(as_text=True)
    if not csv_content.strip():
        return jsonify({"ok": False, "error": "Empty CSV data"}), 400
    try:
        import tempfile
        tmp = Path(tempfile.mktemp(suffix=".csv"))
        tmp.write_text(csv_content, encoding="utf-8")
        students = bot.load_all_students(str(tmp))
        config_path = str(tmp)
        return jsonify({"ok": True, "count": len(students), "students": [{k: v for k, v in s.items()} for s in students]})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/start", methods=["POST"])
@require_auth
def api_start():
    global bot_thread

    if bot_running:
        return jsonify({"ok": False, "error": "Bot is already running"}), 400

    students = _get_loaded_students()
    if not students:
        return jsonify({"ok": False, "error": "No students loaded. Load a config.csv first"}), 400

    data = request.get_json(silent=True) or {}
    headless = data.get("headless", not os.environ.get("DISPLAY"))
    immediate = data.get("immediate", False)
    if not headless and not os.environ.get("DISPLAY"):
        headless = True

    global telegram_token, telegram_chat_id
    telegram_token = data.get("telegram_token", telegram_token)
    telegram_chat_id = data.get("telegram_chat_id", telegram_chat_id)

    bot.TELEGRAM_BOT_TOKEN = telegram_token
    bot.TELEGRAM_CHAT_ID = telegram_chat_id

    global student_status, student_results
    student_status.clear()
    student_results.clear()

    # Clear log queue
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break

    bot_thread = threading.Thread(target=run_students_web, args=(students, headless, immediate), daemon=True)
    bot_thread.start()

    return jsonify({"ok": True, "message": f"Started bot for {len(students)} student(s)"})


@app.route("/api/stop", methods=["POST"])
@require_auth
def api_stop():
    if not bot_running:
        return jsonify({"ok": False, "error": "Bot is not running"}), 400
    bot_stop_event.set()
    return jsonify({"ok": True, "message": "Stop signal sent"})


@app.route("/api/logs")
def api_logs():
    # SSE needs token via query param (EventSource doesn't support custom headers)
    query_token = request.args.get("token", "")
    if query_token:
        expected = _make_token(AUTH_EMAIL)
        if not hmac.compare_digest(query_token, expected):
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
    elif not _check_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    def generate():
        while True:
            try:
                record = log_queue.get(timeout=30)
                if record is None:
                    break
                yield f"data: {json.dumps(record)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/results")
@require_auth
def api_results():
    return jsonify(student_results)


@app.route("/api/schedule")
@require_auth
def api_schedule():
    return jsonify(bot.get_schedule())


# ── Scheduled mode ──

def scheduler_loop(target_iso: str):
    global bot_running, scheduled_start, scheduler_thread
    try:
        target = datetime.fromisoformat(target_iso)
    except Exception:
        return
    while not scheduler_stop.is_set():
        now = datetime.now()
        if now >= target:
            break
        remaining = (target - now).total_seconds()
        gap = min(15, remaining)
        scheduler_stop.wait(gap)
    if not scheduler_stop.is_set():
        scheduled_start = None
        # Auto-start the bot
        with app.app_context():
            students = _get_loaded_students()
            if students:
                bot_stop_event.clear()
                bot_thread = threading.Thread(target=run_students_web, args=(students, True), daemon=True)
                bot_thread.start()


@app.route("/api/schedule-start", methods=["POST"])
@require_auth
def api_schedule_start():
    global scheduled_start, scheduler_thread, scheduler_stop
    data = request.get_json(silent=True) or {}
    dt_str = data.get("datetime", "")
    if not dt_str:
        return jsonify({"ok": False, "error": "Missing datetime"}), 400
    try:
        datetime.fromisoformat(dt_str)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid datetime format"}), 400

    scheduler_stop.clear()
    scheduled_start = dt_str
    scheduler_thread = threading.Thread(target=scheduler_loop, args=(dt_str,), daemon=True)
    scheduler_thread.start()
    return jsonify({"ok": True, "message": f"Scheduled for {dt_str}"})


@app.route("/api/schedule-status")
@require_auth
def api_schedule_status():
    return jsonify({
        "scheduled": scheduled_start is not None,
        "datetime": scheduled_start,
    })


@app.route("/api/schedule-cancel", methods=["POST"])
@require_auth
def api_schedule_cancel():
    global scheduled_start
    scheduler_stop.set()
    scheduled_start = None
    return jsonify({"ok": True, "message": "Schedule cancelled"})


# ── Database-backed endpoints ──

@app.route("/api/db/students")
@require_auth
def api_db_students():
    return jsonify(db.get_students())


@app.route("/api/db/logs")
@require_auth
def api_db_logs():
    student_key = request.args.get("student_key", "")
    limit = int(request.args.get("limit", 200))
    return jsonify(db.get_logs(student_key or None, limit))


def _get_loaded_students() -> List[Dict]:
    global config_path
    if not config_path or not Path(config_path).exists():
        return []
    try:
        return bot.load_all_students(config_path)
    except Exception:
        return []


# ── Alexa AI Assistant ──

def _alexa_context() -> dict:
    return {
        "students": _get_loaded_students(),
        "running": bot_running,
        "status": {k: v for k, v in student_status.items()},
        "_actions": {
            "stop": lambda: bot_stop_event.set(),
            "retry": lambda student: _retry_one_student(student),
        },
    }

def _retry_one_student(student: Dict):
    global bot_stop_event, bot_running, student_status, student_results
    import db
    bot_stop_event.clear()
    key = _student_key(student)
    student_logger = setup_web_logger(f"retry_{student.get('name', '?')}")
    student_logger.info("Manual retry for %s", key)
    result = bot.smart_retry(student, use_headless=True, logger=student_logger, stop_event=bot_stop_event, immediate=True)
    student_results.append(result)
    db.update_student_status(key, result.get("status", "failed"), result)
    status = result.get("status", "failed")
    if status == "confirmed":
        student_status[key] = {"status": "Confirmed!", "color": "success", "details": f"Ref: {result.get('reference', 'N/A')}"}
    elif status == "submitted":
        student_status[key] = {"status": "Submitted", "color": "success", "details": "Form submitted"}
    elif status == "stopped":
        student_status[key] = {"status": "Stopped", "color": "danger", "details": "Cancelled by user"}
    elif status == "failed":
        student_status[key] = {"status": "Failed", "color": "danger", "details": "Error occurred"}
    else:
        student_status[key] = {"status": status, "color": "warning", "details": ""}

if GEMINI_API_KEY:
    alexa_assistant = alexa.AlexaAssistant(api_key=GEMINI_API_KEY, context_provider=_alexa_context)
else:
    alexa_assistant = None


@app.route("/api/chat", methods=["POST"])
@require_auth
def api_chat():
    if not alexa_assistant:
        return jsonify({"ok": False, "error": "Alexa is not configured. Set GEMINI_API_KEY environment variable."}), 400
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])
    if not message:
        return jsonify({"ok": False, "error": "Message is required"}), 400
    try:
        reply = alexa_assistant.process(message, history)
        return jsonify({"ok": True, "reply": reply})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


def main():
    global config_path
    default_cfg = PROJECT_DIR / "config.csv"
    if default_cfg.exists():
        config_path = str(default_cfg)

    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")

    public_url = f"http://localhost:{port}" if host == "0.0.0.0" else f"http://{host}:{port}"

    print("=" * 55)
    print("  Goethe Booking Bot - Web Control Panel")
    print()
    print(f"  Local:   http://localhost:{port}")
    print(f"  Network: http://{host}:{port}")
    print()
    print("  Use ngrok for a public URL:")
    print("    ngrok http http://localhost:{port}")
    print()
    print("  Deploy on Railway / Fly.io / Render:")
    print("    Set PORT env to your port (default 5000)")
    print("=" * 55)
    print("  Press Ctrl+C to stop the server")

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
