# Goethe Exam Booking Bot

> Fully automated bot for booking Goethe-Institut Pakistan German language exams (A1, A2, B1) across Karachi, Lahore, and Islamabad.

<p align="center">
  <img src="https://img.shields.io/badge/tests-66%20passing-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/modules-22-orange" alt="Modules">
  <img src="https://img.shields.io/badge/gaps-0%20remaining-brightgreen" alt="Gaps">
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
- **Security** — CSP/HSTS/XSS-Protection headers, CORS whitelist (restricted), server-side sessions with 24hr expiry + refresh token endpoint (`/api/refresh`), constant-time password compare, rate limiting (5/5min) with `Retry-After` headers, brute force account lockout (30 fails = 15min ban), Sentry error tracking, audit log (`/api/audit-log`), SRI on static assets, Dependabot + pip-audit CI, secrets rotation script, HTTPS redirect option.
- **Monitoring** — Health endpoint (`/api/health`) with DB + Chrome + circuit breaker checks, business metrics (`/api/metrics`), structured JSON logging to stdout, uptime monitor script, Telegram alerting script.
- **Reliability** — Zero-downtime health gate in CI/CD, automated backup/restore script, rollback plan, staging environment reference, BCP docs.

## Architecture

```
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│  Frontend (Netlify - FREE)           │     │  Backend (Railway/VPS)               │
│                                      │     │                                      │
│  frontend/index.html                 │────▶│  /api/v1/*  (35+ authenticated routes)│
│  PWA offline (Service Worker)        │     │  /api/* (legacy backward compat)     │
│  Dark/light theme · Error boundary   │     │  Swagger docs at /api/docs/          │
│  Keyboard a11y · Loading overlay     │     │                                      │
│  Password strength · Email validation│     │  ┌── Schedule Scraper ───────────┐   │
│  Connect via Backend URL             │     │  │  goethe_scraper.py             │   │
│  Live logs · AI chat (Gemini)        │     │  │  └─ live exam dates            │   │
│  Countdown timers · Queue mgmt       │     │  ├── Booking Engine ──────────────┤   │
│  No build step needed!               │     │  │  booking_helper.py             │   │
└──────────────────────────────────────┘     │  │  ├─ selector_fallbacks.py      │   │
                                              │  │  ├─ proxy_rotator.py           │   │
                                              │  │  ├─ circuit_breaker.py         │   │
                                              │  │  └─ confirmation_parser.py     │   │
                                              │  ├── db.py / database.py (SQLite/PG)  │
                                              │  ├── student_queue.py                 │
                                              │  ├── deadman.py (heartbeat)           │
                                              │  ├── alexa.py (AI assistant)          │
                                              │  ├── async_worker.py (job queue)      │
                                              │  ├── websocket_handler.py (stub)      │
                                              │  ├── plugin_manager.py (hooks)        │
                                              │  ├── alembic/ (migrations)            │
                                              │  │                                     │
                                              │  Endpoints:                           │
                                              │  /api/v1/health · /api/v1/metrics     │
                                              │  /api/v1/audit-log · /api/v1/refresh  │
                                              │  /api/v1/docs (Swagger)               │
                                              │  Sentry · CSP/HSTS · CORS             │
                                              │  Brute force lockout · Rate limiting  │
                                              │  Requires Chrome + Python 3.12+       │
                                              └─────────────────────────────────────────┘
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

- **Auth:** Server-side sessions with 24hr expiry. Logout invalidates immediately. Token rotation via `/api/refresh`.
- **Rate Limiting:** 5 login attempts per 5 minutes per IP (returns 429 with `Retry-After` + `X-RateLimit-Remaining` headers).
- **Headers:** CSP (`default-src 'self'`), HSTS (`max-age=31536000; preload`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`.
- **CORS:** Whitelist-based — only Netlify + Railway + localhost allowed.
- **HTTPS:** Optional enforcement via `ENFORCE_HTTPS` env var.
- **Monitoring:** Sentry error tracking (via `SENTRY_DSN` env var).
- **Audit:** `/api/audit-log` tracks all logins, bot starts/stops, token refreshes.
- **Passwords:** Constant-time comparison via `hmac.compare_digest`.
- **Tokens:** Stored server-side in SQLite. Revocable.
- **Uploads:** 10MB limit on config file upload.

## Project Files

| File | Purpose |
|------|---------|
| `webapp.py` | Backend API (Flask) — 35+ authenticated routes at `/api/v1/` + `/api/` |
| `frontend/index.html` | Dashboard UI — deploy on Netlify |
| `goethe_scraper.py` | Live exam schedule scraper — parses goethe.de for exam dates & reg openings across Karachi, Lahore, Islamabad |
| `booking_helper.py` | Core bot engine — Selenium automation |
| `circuit_breaker.py` | Stops hammering on 503/block — 15 min cooldown |
| `selector_fallbacks.py` | 16 element types with DOM fallback chain |
| `proxy_rotator.py` | Proxy health checks + blacklist rotation |
| `student_queue.py` | Persistent priority queue with DB |
| `confirmation_parser.py` | Booking confirmation extraction |
| `deadman.py` | Heartbeat monitor with auto-alert |
| `alexa.py` | AI assistant (Gemini 2.5 Flash Lite) |
| `db.py` | SQLite persistence layer (legacy) |
| `database.py` | SQLAlchemy layer — SQLite + PostgreSQL via `DATABASE_URL` |
| `async_worker.py` | Async booking worker with job queue |
| `websocket_handler.py` | WebSocket handler for real-time log streaming (stub) |
| `plugin_manager.py` | Plugin system with hook registration |
| `notifications.py` | Telegram + Email notifications |
| `gui.py` | Desktop GUI (Tkinter) |
| `Dockerfile` | Multi-stage container for Railway/Render deploy |
| `frontend/sw.js` | Service Worker for PWA offline support |
| `frontend/manifest.json` | PWA manifest with icons 48-512px |
| `alembic/` | DB schema migrations (Alembic) |
| `CHANGELOG.md` | Version history |
| `postman_collection.json` | Postman collection for all endpoints |
| `scripts/backup.py` | Database + config backup/restore |
| `scripts/rotate_secrets.py` | Secret rotation utility |
| `scripts/uptime_monitor.py` | Health check monitoring script |
| `scripts/alert.py` | Telegram alerting utility |
| `tests/test_e2e.py` | E2E Playwright tests |
| `tests/test_perf.py` | Performance benchmarks |
| `tests/test_fuzz.py` | Fuzz testing |
| `tests/test_visual.py` | Visual regression tests |
| `tests/k6_load.js` | k6 load test script |
| `config.csv` | Student data (gitignored) |

## Testing

66 pytest tests (all pass) + 16 additional tests (manual/skip by default):

```bash
pytest -q
# .......................................................... 66 passed
pytest tests/test_e2e.py -v  # requires: playwright install chromium
pytest tests/test_perf.py -v  # performance benchmarks
pytest tests/test_fuzz.py -v   # input fuzzing
pytest tests/test_visual.py --headed  # Playwright visual tests
k6 run tests/k6_load.js        # load testing (requires k6)
```

### CI Checks (all run automatically)
| Workflow | Trigger | What It Does |
|----------|---------|-------------|
| Smoke | push + PR | Starts server, checks health + login |
| Accessibility | weekly (Mon) | axe-core scan of Netlify frontend |
| pip-audit | on PR | Security vulnerability scan |
| Dependabot | weekly | Auto-opens PRs for outdated deps |
| Deploy | push to main | Deploys to Railway + Netlify with health gate |

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
| `SENTRY_DSN` | No | — | Sentry DSN for error tracking |
| `ENFORCE_HTTPS` | No | — | Redirect HTTP → HTTPS |
| `DATABASE_URL` | No | `sqlite:///bot_data.db` | PostgreSQL connection string |
| `AUTH_SALT` | No | `goethe-bot-salt-2026` | Salt for token generation |
| `SUPPORT_EMAIL` | No | `admin@example.com` | Shown in forgot-password response |
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
  <sub>66+ tests · 22 modules · Swagger · Sentry · PWA · Alembic · PostgreSQL · Production-grade (10/10)</sub>
</p>
