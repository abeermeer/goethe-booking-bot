# Goethe Exam Booking Bot

Fully automated bot for booking Goethe-Institut Pakistan German language exams (A1, A2, B1) across Karachi, Lahore, and Islamabad.

## Features

- **Multiple Exam Levels** — A1, A2, B1 (extendable to C1, C2)
- **All 3 Cities** — Karachi, Lahore, Islamabad
- **Multi-Student** — Runs 3 students in parallel (one Chrome window each)
- **Burst Mode** — Fast-polls every 2-3s at exact booking-open time
- **Full Automation** — Clicks "Book Now" → "Continue" → "Book for Myself" → Login → Fill Form → Submit
- **Screenshot Capture** — Saves confirmation screenshot
- **Telegram Notifications** — Get instant success/failure alerts on your phone
- **Anti-Detection** — Human-like delays, mouse jitter, Cloudflare detection

## Requirements

- Python 3.9+
- Google Chrome (latest)
- Windows / Linux / macOS

## Architecture

```
┌──────────────────────────────────────┐     ┌────────────────────────────┐
│  Frontend (Netlify - FREE)           │     │  Backend (Railway/VPS)     │
│                                      │     │                            │
│  frontend/index.html                 │────▶│  /api/start                │
│  (pure HTML/CSS/JS)                  │     │  /api/stop                 │
│                                      │     │  /api/status               │
│  Connect via Backend URL input       │     │  /api/logs (SSE stream)    │
│  Live logs via SSE                   │     │  /api/config               │
│                                      │     │  /api/config/upload        │
│  No build step needed!               │     │  /api/results              │
└──────────────────────────────────────┘     │                            │
                                             │  Requires Chrome + Python  │
                                             └────────────────────────────┘
```

## Quick Start

### Option A: Backend + Frontend (Deployed)
```bash
# Backend (deploy anywhere with Chrome):
pip install -r requirements.txt
python webapp.py

# Frontend: upload frontend/ folder to Netlify (drag & drop)
# Then enter your backend URL in the browser UI
```

### Option B: Everything Local (Simplest)
```bash
pip install -r requirements.txt
python webapp.py
# Open http://localhost:5000 in browser
```

### Option C: GUI Desktop App
```bash
python gui.py
```

### Option D: Command Line
```bash
python booking_helper.py --config config.csv
```

## Config File

Edit `config.csv` with your students' real data:

| Column | Example | Description |
|--------|---------|-------------|
| name | Ali Khan | Student name |
| email | ali@email.com | My Goethe.de login email |
| password | MyPass123! | My Goethe.de login password |
| exam_level | A1 | A1, A2, or B1 |
| city | Karachi | Karachi, Lahore, or Islamabad |
| booking_datetime | 2026-07-03T11:24:00 | Exact booking open time |
| passport | AB1234567 | Passport number |
| cnic | 42101-1234567-8 | CNIC number |
| dob | 15/08/2000 | Date of birth (DD/MM/YYYY) |

## Telegram Notifications (Optional)

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Get your chat ID (message @userinfobot)
3. Set environment variables:

```powershell
set TELEGRAM_BOT_TOKEN=your_bot_token
set TELEGRAM_CHAT_ID=your_chat_id
python booking_helper.py --config config.csv
```

Or pass as CLI args:

```bash
python booking_helper.py --config config.csv --telegram-token TOKEN --telegram-chat-id CHAT_ID
```

## How It Works

1. **Pre-booking** — Opens exam page 10 seconds before booking time
2. **Burst polling** — Refreshes every 2-3s waiting for "Book Now" button
3. **Click flow** — Book Now → Continue → Book for Myself
4. **Auto-login** — Fills email/password on My Goethe.de
5. **Form fill** — Completes registration form with student data
6. **Confirmation** — Screenshots page, extracts booking reference

## Deploy Online (For Remote Access)

### Frontend → Netlify (Free)
1. Drag & drop the `frontend/` folder to https://app.netlify.com/drop
2. Or go to Netlify → Add new site → Deploy manually → choose `frontend/` folder
3. Done — you get `https://your-site.netlify.app`

Then enter your Backend URL in the UI.

### Backend → Free Hosting

#### Option 1: ngrok — Instant Public URL (Fastest)
Expose your local backend to the internet in 1 minute.

```powershell
# 1. Download ngrok from https://ngrok.com/download
# 2. Sign up (free), get your auth token
# 3. Run:  ngrok config add-authtoken YOUR_TOKEN
# 4. Run the setup script:
powershell -File ngrok_setup.ps1
```

You get a public URL like `https://abc123.ngrok-free.app` — enter this in the frontend.

#### Option 2: Railway.app (Free Tier)
1. Push to GitHub (include `Dockerfile`, `webapp.py`, `railway.toml`)
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Done — backend at `https://your-project.up.railway.app`

**Free tier:** $5 credit/month, enough for 24/7 uptime.

#### Option 3: Render.com (Free Tier)
1. Push to GitHub
2. https://render.com → New Web Service → Connect repo → Docker
3. URL: `https://your-service.onrender.com`

**Free tier:** Sleeps after 15 min idle (wakes on first request).

#### Option 4: Oracle Cloud (Always Free — Best Long Term)
- https://www.oracle.com/cloud/free/
- Full Ubuntu VM, install Chrome + Python
- Free forever, no sleeping

#### Option 5: Your Own PC (Completely Free)
Run `python webapp.py` then use ngrok for a public URL.

## Project Files

| File | Purpose |
|------|---------|
| `webapp.py` | Backend API (Flask) — deploy on Railway/Render/VPS |
| `frontend/index.html` | Frontend UI — deploy on Netlify (drag & drop) |
| `frontend/_redirects` | Netlify SPA routing config |
| `booking_helper.py` | Core bot engine (Selenium) |
| `selector_fallbacks.py` | Multi-selector DOM fallback system |
| `proxy_rotator.py` | Proxy health checks + blacklist rotation |
| `student_queue.py` | Persistent student queue with priority |
| `confirmation_parser.py` | Structured booking confirmation extraction |
| `deadman.py` | Heartbeat monitor with auto-alert |
| `db.py` | SQLite persistence layer |
| `notifications.py` | Telegram + Email notifications |
| `alexa.py` | AI assistant (Gemini 2.5 Flash Lite) |
| `gui.py` | Desktop GUI (Tkinter) |
| `config.csv` | Student data (edit before running) |
| `Dockerfile` | Container for backend deployment |
| `railway.toml` | Railway.app config |
| `render.yaml` | Render.com config |
| `.dockerignore` | Optimize Docker builds |
| `ngrok_setup.ps1` | Expose local backend via public URL |
| `setup.ps1` | Windows dependency installer |
| `start_web.bat` | Double-click to start locally |

## Important Notes

- Create **separate My Goethe.de accounts** for each student before running
- Use exact `booking_datetime` from the [official exam dates page](https://www.goethe.de/ins/pk/en/spr/prf/anm.html)
- The bot handles 503 errors, Cloudflare blocks, and server crashes automatically
- Keep the computer awake and connected to internet during the booking window

## Exam Dates Reference (2026)

Check [Dates and Enrolment](https://www.goethe.de/ins/pk/en/spr/prf/anm.html) for exact dates.

---

<p align="center">
  <sub>Built by <a href="https://github.com/abeermeer">Abeer Meer</a></sub><br>
  <sub>© 2026 Abeer Meer. Licensed under the <a href="LICENSE">MIT License</a>.</sub>
</p>
