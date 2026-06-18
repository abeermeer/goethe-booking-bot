# Post-Live Test Tasks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven development or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three gaps identified by Claude review — nightly live integration test, graceful shutdown with SIGTERM handler, WebSocket real-time log streaming.

**Architecture:** Three independent subsystems:
1. CI workflow that hits real Goethe portal nightly (separate from smoke tests)
2. `atexit`/`signal` handler in webapp.py that checkpoints all in-progress students before exit
3. Full WebSocket endpoint replacing the stub, broadcasting booking logs in real-time

**Tech Stack:** Python, Flask-Sock, GitHub Actions (cron), Selenium, PostgreSQL/SQLite

---

# Plan A: Live Integration Test (Nightly CI)

## Files
- `.github/workflows/live-integration.yml` — NEW: nightly cron workflow
- `tests/test_live_integration.py` — NEW: tests against real portal

## Steps

### A1. Create the test file

**File:** `tests/test_live_integration.py`

```python
"""Nightly integration tests against real goethe.de portal.
Skipped by default — run with: pytest tests/test_live_integration.py -v
Or via CI cron schedule."""
import pytest
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from booking_helper import get_exam_url, check_slot_availability
from goethe_scraper import get_schedule
import logging

logger = logging.getLogger(__name__)

@pytest.mark.live
def test_exam_pages_load():
    """Verify all 3 exam pages return 200 and contain expected text."""
    import requests
    for level in ["A1", "A2", "B1"]:
        url = get_exam_url(level)
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, f"{level} page returned {resp.status_code}"
        assert "Goethe" in resp.text or "Prüfung" in resp.text

@pytest.mark.live
def test_login_page_loads():
    """Verify Goethe login page is accessible."""
    import requests
    resp = requests.get("https://login.goethe.de/cas/login", timeout=30)
    assert resp.status_code == 200
    assert "Log in" in resp.text or "username" in resp.text

@pytest.mark.live
def test_schedule_scraper_returns_entries():
    """Verify schedule scraper finds exam entries for all cities."""
    entries = get_schedule(force_refresh=True)
    assert len(entries) > 0, "No exam entries found"
    cities = set(e.city for e in entries)
    assert "Karachi" in cities or "Lahore" in cities or "Islamabad" in cities

@pytest.mark.live
def test_slot_pre_check_no_crash():
    """Verify slot pre-check runs without crashing (may find 0 slots)."""
    student = {
        "name": "CI Test", "email": "ci-test@example.com",
        "level": "A1", "city": "Karachi",
        "booking_datetime": "2099-12-31T23:59"
    }
    result = check_slot_availability(student, logger)
    assert "message" in result
    assert "available" in result
```

### A2. Create the CI workflow

**File:** `.github/workflows/live-integration.yml`

```yaml
name: Live Integration

on:
  schedule:
    # Runs at 2:00 AM UTC daily (7:00 AM PKT)
    - cron: '0 2 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install system deps
        run: |
          sudo apt-get update
          sudo apt-get install -y chromium-browser chromium-chromedriver
      - name: Install Python deps
        run: pip install -r requirements.txt
      - name: Run live integration tests
        run: pytest tests/test_live_integration.py -v --tb=short
        continue-on-error: true  # Don't fail CI if portal is down
      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: incoming-webhook
          payload: |
            {"text": "⚠️ Live integration test failed for goethe-booking-bot. Check: https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }}"}
        continue-on-error: true
```

### A3. Run tests to verify

```bash
pytest tests/test_live_integration.py -v --tb=short
```

**Expected:** All 4 tests pass or relevant failures reported.

---

# Plan B: Graceful Shutdown (SIGTERM Handler)

## Files
- `webapp.py` — MODIFY: add signal handler + checkpoint loop
- `booking_helper.py` — MODIFY: expose checkpoint save function

## Steps

### B1. Add checkpoint helper to booking_helper.py

Add after `save_checkpoint` usage:

```python
def checkpoint_all_running_students():
    """Save checkpoint for all in-progress students. Called on shutdown."""
    import db
    students = db.get_students()
    running = [s for s in students if s.get("status") in ("running", "in_progress")]
    for s in running:
        key = f"{s['name']}|{s.get('level', s.get('exam_level', ''))}|{s['city']}"
        db.save_checkpoint(key, 1)  # Save step 1 (post-login) as safety net
        logger = logging.getLogger("shutdown")
        logger.info("Checkpoint saved for %s", key)
    return len(running)
```

### B2. Add signal handler in webapp.py

Add at top of webapp.py (after imports):

```python
import signal

def _handle_shutdown(signum, frame):
    """On SIGTERM/SIGINT, checkpoint running students before exit."""
    logger = logging.getLogger("shutdown")
    logger.warning("Received signal %s, checkpointing running students...", signum)
    try:
        count = bot.checkpoint_all_running_students()
        logger.info("Checkpointed %d running student(s)", count)
    except Exception as e:
        logger.error("Checkpoint failed: %s", e)
    # Flask will exit after this returns
```

Add after `app = Flask(__name__)` or after blueprint registration:

```python
signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGINT, _handle_shutdown)
```

### B3. Verify

Start server, start a booking, send SIGTERM:

```bash
# In another terminal
python -c "import os, signal; os.kill(3080, signal.SIGTERM)"
```

Check logs show "Checkpointed N running student(s)".

---

# Plan C: WebSocket Real-Time Log Streaming

## Files
- `websocket_handler.py` — REWRITE: full WebSocket implementation
- `webapp.py` — MODIFY: register WebSocket routes properly
- `frontend/index.html` — MODIFY: replace polling with WebSocket connection
- `requirements.txt` — MODIFY: add `flask-sock`

## Steps

### C1. Update requirements.txt

Add line:
```
flask-sock>=0.7.0
```

### C2. Rewrite websocket_handler.py

```python
"""Real-time WebSocket log streaming for booking dashboard."""
from __future__ import annotations

import json
import logging
import threading
from typing import Dict, Set

from flask import Flask
from flask_sock import Server, Sock

_clients: Set[Server] = set()
_lock = threading.Lock()

def broadcast(message: str, msg_type: str = "log") -> None:
    """Send a message to all connected WebSocket clients."""
    payload = json.dumps({"type": msg_type, "data": message})
    dead = set()
    with _lock:
        for ws in _clients:
            try:
                ws.send(payload)
            except Exception:
                dead.add(ws)
        _clients -= dead

def setup_websocket(app: Flask) -> Sock:
    sock = Sock(app)

    @sock.route("/api/ws/logs")
    def log_stream(ws: Server):
        with _lock:
            _clients.add(ws)
        try:
            while True:
                msg = ws.receive(timeout=30)
                if msg is None:
                    break
        except Exception:
            pass
        finally:
            with _lock:
                _clients.discard(ws)

    return sock
```

### C3. Wire into webapp.py

Replace existing WebSocket setup:

```python
from websocket_handler import setup_websocket, broadcast

# After app initialization
sock = setup_websocket(app)
```

Add a broadcast helper endpoint (optional, for testing):

```python
@bp.route("/api/ws/test", methods=["POST"])
@require_auth
def api_ws_test():
    data = request.get_json(silent=True) or {}
    broadcast(data.get("message", "test"), msg_type=data.get("type", "log"))
    return jsonify({"ok": True})
```

### C4. Integrate broadcast into booking flow

In `booking_helper.py` functions (`run_student_flow`, `check_slot_availability`, `scan_booking_form`), add broadcast calls at key checkpoints:

```python
from websocket_handler import broadcast as _ws_broadcast

# After each status update
try:
    _ws_broadcast(f"[{name}] {status_message}", msg_type="status")
except Exception:
    pass
```

Wrap in try/except so WebSocket failures never crash the bot.

### C5. Update frontend — replace polling with WebSocket

In `frontend/index.html`, add after existing JS:

```javascript
// ── WebSocket Log Stream ──
let ws = null;
let wsReconnectTimer = null;

function connectWebSocket() {
  if (ws) ws.close();
  const url = BASE.replace(/^http/, "ws") + "/api/ws/logs";
  try {
    ws = new WebSocket(url);
    ws.onmessage = function(e) {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "log" || msg.type === "status") {
          appendToLiveFeed(msg.data, msg.type === "status" ? "info" : "log");
        }
      } catch(ex) {}
    };
    ws.onclose = function() {
      ws = null;
      wsReconnectTimer = setTimeout(connectWebSocket, 5000);
    };
    ws.onerror = function() {
      ws = null;
    };
  } catch(ex) {}
}

// Update existing connectDashboard() to also connect WS
// Add wsConnect after successful connection
// In the existing connectDashboard function, add after startStatusPoll():
//   connectWebSocket();

// Add disconnect on logout
function disconnectWebSocket() {
  if (ws) { ws.close(); ws = null; }
  if (wsReconnectTimer) { clearTimeout(wsReconnectTimer); wsReconnectTimer = null; }
}
```

### C6. Verify

Start server, open dashboard, start a bot — logs should appear in real-time without polling delay.

---

# Execution Order

1. **Plan C (WebSocket)** first — most visible impact, unblocks live log streaming
2. **Plan A (Live Integration)** second — independent, adds safety net
3. **Plan B (Graceful Shutdown)** third — low risk, simple change
