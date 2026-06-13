# Goethe Exam Booking Bot

> Fully automated bot for booking Goethe-Institut Pakistan German language exams (A1, A2, B1) across Karachi, Lahore, and Islamabad.

<p align="center">
  <img src="https://img.shields.io/badge/tests-66%20passing-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/modules-12-orange" alt="Modules">
</p>

## Demo

> 🎥 *Demo video coming soon — shows the full flow: login → upload config → start bot → live logs → booking confirmation.*

## Features

- **All Exam Levels** — A1, A2, B1 (extendable to C1, C2)
- **All 3 Cities** — Karachi, Lahore, Islamabad
- **Multi-Student Parallel** — Runs 3+ students simultaneously (one Chrome each)
- **Burst Mode** — Fast-polls every 2-3s at exact booking-open time
- **Full Automation** — Clicks "Book Now" → "Continue" → "Book for Myself" → Login → Fill Form → Submit → Confirm
- **Selector Fallback System** — 16 element types with 2-5 CSS/XPath fallbacks each. Survives page structure changes.
- **Proxy Rotation** — Health-checked proxies with 5-min blacklist on failure. Self-healing when pool exhausted.
- **Circuit Breaker** — Detects 503/Cloudflare blocks, stops hammering after 10 failures, retries after 15 min cooldown.
- **Student Queue** — Persistent priority queue with DB backing. Enqueue, dequeue, retry, track history.
- **Confirmation Parser** — Extracts booking reference, exam date/time, level, city, errors from confirmation page.
- **Dead Man Switch** — Heartbeat monitor. Auto-alerts via Telegram if process hangs or crashes.
- **Screenshot Capture** — Saves confirmation screenshot on successful booking.
- **Telegram Notifications** — Instant success/failure alerts on your phone.
- **AI Assistant (Alexa)** — Gemini 2.5 Flash Lite chatbot in the dashboard. Ask about booking status, student info, logs, or retry a student — all via natural language.
- **Web Dashboard** — Full admin panel with analytics cards, queue management, activity log, scheduling, countdown timers.
- **Anti-Detection** — Human-like delays, mouse jitter, Cloudflare/503 detection, random user agents.
- **Security** — Server-side sessions with 24hr expiry, constant-time password compare, rate limiting (5/5min), security headers, HTTPS redirect option.

## Architecture

```
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│  Frontend (Netlify - FREE)           │     │  Backend (Railway/VPS)               │
│                                      │     │                                      │
│  frontend/index.html                 │────▶│  /api/*  (30+ authenticated routes)   │
│  (pure HTML/CSS/JS)                  │     │                                      │
│                                      │     │  ┌──────────────────────────────┐    │
│  Connect via Backend URL             │     │  │  booking_helper.py           │    │
│  Live logs via SSE (EventSource)     │     │  │  └─ selector_fallbacks.py    │    │
│  AI chat panel                       │     │  │  └─ proxy_rotator.py         │    │
│  Countdown timers                    │     │  │  └─ circuit_breaker.py       │    │
│  Queue management                    │     │  │  └─ confirmation_parser.py   │    │
│  No build step needed!               │     │  ├── student_queue.py           │    │
└──────────────────────────────────────┘     │  ├── deadman.py (heartbeat)     │    │
                                             │  ├── alexa.py (AI assistant)   │    │
                                             │  ├── db.py (SQLite persistence) │    │
                                             │  └── notifications.py           │    │
                                             │                                  │
                                             │  Requires Chrome + Python 3.9+   │
                                             └──────────────────────────────────┘
```

## Quick Start

### Backend + Frontend (Deployed)
```bash
pip install -r requirements.txt
python webapp.py
# Frontend: drag & drop frontend/ folder to Netlify
```

### Everything Local
```bash
pip install -r requirements.txt
python webapp.py
# Open http://localhost:5000
```

### GUI Desktop App
```bash
python gui.py
```

### Command Line (Headless)
```bash
python booking_helper.py --config config.csv --telegram-token TOKEN --telegram-chat-id CHAT_ID
```

## Config File

Edit `config.csv` with student data:

| Column | Example | Description |
|--------|---------|-------------|
| name | Ali Khan | Student name |
| email | ali@email.com | My Goethe.de login email |
| password | MyPass123! | My Goethe.de login password |
| exam_level | A1 | A1, A2, or B1 |
| city | Karachi | Karachi, Lahore, or Islamabad |
| booking_datetime | 2026-07-17T10:00:00 | Exact booking open time |

## How It Works

1. **Polling** — Opens exam page, monitors for "Book Now" button
2. **Burst Mode** — 10s before booking time, refreshes every 2-3s
3. **Click Flow** — Book Now → Continue → Book for Myself
4. **Auto-Login** — Fills email/password on My Goethe.de
5. **Form Fill** — Completes registration form with all student fields
6. **CAPTCHA** — Auto-solved (if 2Captcha API key configured)
7. **Confirmation** — Screenshots page, extracts booking reference + exam details
8. **Circuit Breaker** — On 503/block → stops after 10 consecutive failures → cools down 15 min → retries automatically
9. **Notifications** — Telegram alert on success, failure, or dead man switch trigger

**Retry layers:**
- Step 1 poll loop: infinite (never gives up on finding a slot)
- Per-click retries: 3 attempts for stale elements
- Smart retry: 3 full-flow restarts with fresh Chrome + proxy

## AI Assistant (Alexa)

The dashboard includes a built-in AI assistant powered by Google Gemini 2.5 Flash Lite.

**What you can ask:**
- *"Show me the students"* — reads the loaded config
- *"What's the bot status?"* — running/idle, student progress
- *"Show recent logs"* — last 200 log entries
- *"Retry [student name]"* — triggers a fresh booking attempt for a specific student
- *"Stop the bot"* — sends stop signal
- *"Help with deployment"* — deployment guidance

**How to enable:** Set `GEMINI_API_KEY` environment variable. Free tier gives 20 requests/day.

## Security

- **Auth:** Server-side sessions with 24hr expiry. Logout invalidates immediately.
- **Rate Limiting:** 5 login attempts per 5 minutes per IP (returns 429).
- **Headers:** `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- **HTTPS:** Optional enforcement via `ENFORCE_HTTPS` env var.
- **Passwords:** Constant-time comparison via `hmac.compare_digest`.
- **Tokens:** Stored server-side in SQLite. Revocable.
- **Uploads:** 10MB limit on config file upload.

## Project Files

| File | Purpose |
|------|---------|
| `webapp.py` | Backend API (Flask) — 30+ authenticated endpoints |
| `frontend/index.html` | Dashboard UI — deploy on Netlify |
| `booking_helper.py` | Core bot engine — Selenium automation |
| `circuit_breaker.py` | Stops hammering on 503/block — 15 min cooldown |
| `selector_fallbacks.py` | 16 element types with DOM fallback chain |
| `proxy_rotator.py` | Proxy health checks + blacklist rotation |
| `student_queue.py` | Persistent priority queue with DB |
| `confirmation_parser.py` | Booking confirmation extraction |
| `deadman.py` | Heartbeat monitor with auto-alert |
| `alexa.py` | AI assistant (Gemini 2.5 Flash Lite) |
| `db.py` | SQLite persistence layer |
| `notifications.py` | Telegram + Email notifications |
| `gui.py` | Desktop GUI (Tkinter) |
| `Dockerfile` | Container for Railway/Render deploy |
| `config.csv` | Student data (gitignored) |

## Testing

66 pytest tests covering all modules:

```bash
pytest -q
# .......................................................... 66 passed
```

| Module | Tests |
|--------|-------|
| `circuit_breaker.py` | 12 — all states, transitions, concurrency |
| `confirmation_parser.py` | 11 — references, dates, levels, cities, errors |
| `proxy_rotator.py` | 6 — empty pool, single proxy, blacklist, expiry |
| `student_queue.py` | 8 — enqueue, dequeue, priority, clear, reset |
| `deadman.py` | 4 — alive, ping, check, callback |
| `selector_fallbacks.py` | 3 — keys defined, valid By types, error selectors |
| `db.py` | 8 — students, logs, queue, checkpoints |
| `integration.py` | 4 — end-to-end flows |

## Deploy Online

### Frontend → Netlify (Free)
Drag & drop `frontend/` folder to https://app.netlify.com/drop

### Backend → Railway ($5/mo recommended)
Push to GitHub → Railway → New Project → Deploy from GitHub repo. Includes Dockerfile.

### Backend → Free Options
- **ngrok** — Expose local backend instantly: `powershell -File ngrok_setup.ps1`
- **Render.com** — Free tier (sleeps after 15 min idle)
- **Oracle Cloud** — Free forever Ubuntu VM

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH_EMAIL` | Yes | — | Admin login email |
| `AUTH_PASSWORD` | Yes | — | Admin login password |
| `GEMINI_API_KEY` | No | — | Google Gemini API key for Alexa |
| `TELEGRAM_BOT_TOKEN` | No | — | Telegram bot token for notifications |
| `TELEGRAM_CHAT_ID` | No | — | Telegram chat ID for notifications |
| `CAPTCHA_API_KEY` | No | — | 2Captcha API key for CAPTCHA solving |
| `PROXY_LIST` | No | — | Comma-separated proxy list |
| `CIRCUIT_BREAKER_THRESHOLD` | No | 10 | Consecutive failures before cooldown |
| `CIRCUIT_BREAKER_COOLDOWN` | No | 900 | Cooldown seconds after threshold |
| `MAX_SMART_RETRIES` | No | 2 | Full-flow retry attempts per student |
| `ENFORCE_HTTPS` | No | — | Redirect HTTP → HTTPS |
| `PORT` | No | 5000 | Backend server port |

## Important Notes

- Create separate My Goethe.de accounts for each student before running
- Use exact `booking_datetime` from the [official exam dates page](https://www.goethe.de/ins/pk/en/spr/prf/anm.html)
- The bot handles 503 errors, Cloudflare blocks, and server crashes automatically via the circuit breaker
- Keep the computer/Railway awake during the booking window

---

<p align="center">
  <sub>Built by <a href="https://github.com/abeermeer">Abeer Meer</a></sub><br>
  <sub>© 2026 Abeer Meer. Licensed under the <a href="LICENSE">MIT License</a>.</sub><br>
  <sub>66 tests · 12 modules · Production-grade architecture</sub>
</p>
