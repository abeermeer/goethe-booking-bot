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
| **Frontend (Netlify)** | https://aesthetic-alpaca-769b17.netlify.app | ✅ Live |
| **Backend (Railway)** | https://goethe-booking-bot-production-a6a6.up.railway.app | ✅ Online |
| **Mock Site (Netlify)** | https://goethe-bot-mock.netlify.app | ✅ Live |
| **Presentation (Netlify)** | https://goethe-bot-presentation.netlify.app | ✅ Live |
| **GitHub** | https://github.com/abeermeer/goethe-booking-bot | ✅ Latest |

## Latest Changes (12 Jun 2026)

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
- Netlify URL: `https://aesthetic-alpaca-769b17.netlify.app`
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
```
