# Goethe Booking Bot — Session Summary (Updated 12 Jun 2026)

## Project
Automated bot for booking Goethe-Institut Pakistan German language exams (A1, A2, B1) — multi-student, multi-city.

## User
- GitHub: `abeermeer`
- Goethe credentials: `student@example.com` / `GOETHE_PASSWORD_REDACTED`
- Admin login: `admin@example.com` / `ADMIN_PASSWORD_REDACTED`
- 3 students: A1 Karachi (10:00), A2 Lahore (10:05), B1 Karachi (10:10)
- All bookable from July 17, 2026
- Python: `C:\Users\brosp\AppData\Local\Programs\Python\Python312\python.exe`
- Project dir: `C:\Users\brosp\Downloads\goethe-bot`
- Platform: Windows

## Deployments (all currently live)
| Service | URL | Status |
|---------|-----|--------|
| **Frontend (Netlify)** | https://goethe-booking-dashboard.netlify.app | ✅ Live |
| **Backend (Railway)** | https://goethe-booking-bot-production.up.railway.app | ✅ Online |
| **Mock Site (Netlify)** | https://goethe-bot-mock.netlify.app | ✅ Live |
| **Presentation (Netlify)** | https://goethe-bot-presentation.netlify.app | ✅ Live |
| **GitHub** | https://github.com/abeermeer/goethe-booking-bot | ✅ Latest |

## Latest Changes (12 Jun 2026 — Session 2)

### Full 10/10 Upgrade (All 5 Phases)

**Phase 1: Reliability**
- Chrome memory flags optimized: `--process-per-site`, `--disable-component-update`, `--disable-background-timer-throttling`, `--disable-features=VizDisplayCompositor`, etc. (both Windows + Linux)
- Session checkpoint system: `db.save_checkpoint()` / `get_checkpoint()` / `clear_checkpoint()` after each booking step
- Resume from crash: on restart, skips completed steps and continues where it left off
- Health endpoint enhanced: `uptime_seconds`, `uptime_human` fields

**Phase 2: CI/CD + Testing**
- GitHub Actions: `python -m pytest` on PRs, auto-deploy to Railway + Netlify on push to main
- 18 pytest tests (db CRUD, checkpoint cycle, booking helpers, URL parsing)
- `.pre-commit-config.yaml` with trailing-whitespace, yaml check, pytest hook

**Phase 3: Frontend Polish**
- Live countdown timer to next booking slot (updates every second, red at <1min)
- PWA support: manifest.json, theme-color meta tag (installable on mobile)
- Loading states for student cards and error display improvements

**Phase 4: Backend Hardening**
- Rate limiting on `/api/login`: 5 attempts per IP per 5 minutes (returns 429)
- Structured JSON logging: `bot_logs.ndjson` with timestamped JSON records

**Phase 5: Monitoring**
- Health endpoint with uptime tracking
- Frontend status badge shows connection health (idle/running)
- cron-job.org compatible: `https://railway-url/health` returns `{"status":"ok"}`

## Latest Changes (12 Jun 2026 — Session 1)

### Presentation Site (goethe-bot-presentation.netlify.app)
- Built from scratch — dark cinematic theme with starfield canvas background
- Custom cursor with follower, scroll reveal animations (vanilla JS, no CDN deps)
- Sections: Hero, Features, Students, How It Works (6-step flow), Timeline, Tech Stack
- Fixed GSAP CDN failure bug — replaced with `IntersectionObserver` + CSS transitions
- Navbar CTA and hero button link to main dashboard
- Mobile bottom bar with dashboard link for small screens
- Footer credit: "Built by Abeer Meer"

### Bot Dashboard Accidentally Overwritten
- First presentation deploy went to `aesthetic-alpaca-769b17` (wrong site)
- Dashboard was showing presentation content for ~30 mins
- Fixed: redeployed `frontend/` to correct site

## Latest Changes (11 Jun 2026)

### Login Page (Admin Auth)
- Centered login overlay on dashboard load
- Credentials: `admin@example.com` / `ADMIN_PASSWORD_REDACTED`
- Backend: HMAC token auth, `@require_auth` decorator on all `/api/*` routes
- Frontend: `apiFetch()` wrapper auto-adds `Authorization: Bearer` header
- 401 responses auto-redirect to login screen
- SSE logs use `?token=` query param (EventSource limitation)
- Forgot password link (shows reset message to support email)
- **Backend URL field inside login card** — works in incognito mode (no localStorage)

### Run Now / Schedule Toggle Fix
- Mode toggle (Run Now / Schedule) added to Actions card
- Run Now sends `immediate: true` → skips per-student `scheduled_wait()`
- Schedule mode calls `/api/schedule-start` instead
- Initial bug: function override pattern broke onclick — fixed.

### Stop Button Fix
- Previously: `stop_event` checked only in step 1 polling loop
- Steps 2–6 ran without any stop check → Stop button useless after step 1
- Fixed: added `stop_event.is_set()` checks between every step (2→3, 3→4, 4→5, 5→6)
- Now Stop button works at any point in the flow

### WhatsApp / WHAPI Removed
- WHAPI integration removed from `notifications.py` (403 errors, unstable)
- `send_whatsapp()` and all WHAPI env vars deleted
- Only Telegram and Email notifications remain

### Mock URL Override Restored
- `EXAM_URLS` in `booking_helper.py` now reads `MOCK_A1/A2/B1_URL` env vars
- Falls back to real Goethe URLs when env vars not set
- Tested with mock → confirmed working

## Key Files
| File | Purpose |
|------|---------|
| `booking_helper.py` | Core bot engine (1165 lines) |
| `webapp.py` | Flask backend API with auth (500+ lines) |
| `frontend/index.html` | Web dashboard with login page |
| `presentation/index.html` | Presentation site (cinematic theme, scroll reveals) |
| `config.csv` | Student credentials (gitignored) |
| `db.py` | SQLite persistence |
| `notifications.py` | Telegram + Email notifications (WHAPI removed) |
| `Dockerfile` | python:3.12-slim + google-chrome-stable |
| `SESSION_SUMMARY.md` | This file |

## Tokens & IDs
- Railway API Token: `RAILWAY_TOKEN_REDACTED`
- Railway Project ID: `6aee17f5-fe9f-4496-a02d-e5f366d37c2a`
- Railway Service ID: `783d4933-1de1-45b6-a198-08b6f07692cd`
- Railway URL: `https://goethe-booking-bot-production-a6a6.up.railway.app`
- Netlify Site ID: `NETLIFY_SITE_ID_REDACTED`
- Netlify Deploy Token: `NETLIFY_DEPLOY_TOKEN_REDACTED`
- Netlify URL: `https://goethe-booking-dashboard.netlify.app`
- Mock Netlify URL: `https://goethe-bot-mock.netlify.app`
- Presentation Site ID: `bb610061-8eff-4a22-bd50-f4c56a5f1c10`
- Presentation URL: `https://goethe-bot-presentation.netlify.app`

## Current Config (3 students — all same account)
| Name | Level | City | Booking DateTime |
|------|-------|------|-----------------|
| Abeer Meer | A1 | Karachi | 2026-07-17T10:00:00 |
| Abeer Meer | A2 | Lahore | 2026-07-17T10:05:00 |
| Abeer Meer | B1 | Karachi | 2026-07-17T10:10:00 |

## Pre-July 17 Checklist
- [x] Login page with admin auth
- [x] Run Now / Schedule mode toggle
- [x] Stop button works at any step
- [x] Mock URL override via env vars
- [x] Telegram notifications working
- [x] Presentation site deployed
- [ ] Connect custom domain to Netlify (CNAME or nameservers)
- [ ] Set Railway env vars: CAPTCHA_API_KEY, SMTP_* (as needed)
- [ ] On July 17: open Netlify URL → connect to Railway → login → click Start Bot ~10 min before 10:00

## Commands
```powershell
# Run backend locally
python webapp.py

# Deploy frontend to Netlify
netlify deploy --prod --dir=frontend

# Deploy presentation to Netlify
netlify deploy --prod --dir=presentation --site bb610061-8eff-4a22-bd50-f4c56a5f1c10

# Deploy backend to Railway
$env:RAILWAY_API_TOKEN = "RAILWAY_TOKEN_REDACTED"
railway up --detach

# Set/remove env vars
railway variables set KEY="value"
railway variable delete KEY

# Git push
git add -A; git commit -m "message"; git push origin main

## 12 Jun 2026 — Final
- Countdown fix: all 3 students show own countdown cards (was only nearest)
- New Netlify frontend: **https://goethe-booking-dashboard.netlify.app** (old one deleted)
- Default Railway URL: `https://goethe-booking-bot-production.up.railway.app`
- Railway link fix in GitHub Actions (added `--project` flag)
- Old Netlify site `aesthetic-alpaca-769b17` deleted from Netlify
- Presentation site updated with new dashboard URL
- All old URL references cleaned from codebase
- Commits: `9b856c8` `40cd763` `cf488b4` `6d0efc9` `0dda669` `35bbfdb` `7693017`

## 13 Jun 2026 — Frontend Redesign
- Complete visual redesign: dark charcoal/blue theme (was purple)
- Sidebar navigation added (Dashboard, Settings, Sign out)
- Login page redesigned — clean card, no emoji, label+input groups
- Student cards redesigned — grid layout, exam tags (A1/A2/B1), detail rows, progress bar
- All emojis removed from UI (status, buttons, labels, section titles)
- Buttons flattened — no gradients, consistent 6px radius
- Activity log updated — monospace, subtle colors
- Settings section: Config + Notifications + History in one tab
- PWA manifest updated: theme `#0a0a0f`, blue icon
- Commit: `9b48be3`
```
