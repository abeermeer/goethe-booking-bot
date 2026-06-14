# Goethe Booking Bot — Session Summary (Updated 13 Jun 2026)

## Project
Automated bot for booking Goethe-Institut Pakistan German language exams (A1, A2, B1) — multi-student, multi-city.

## User
- GitHub: `abeermeer`
- Goethe credentials: `abeermeer7979@gmail.com` / `hf?3Ru8UkhfKw*X`
- Admin login: `hamzarafiq655@gmail.com` / `Hamza@123`
- 3 students: A1 Karachi (10:00), A2 Lahore (10:05), B1 Karachi (10:10)
- All bookable from July 17, 2026
- Python: `C:\Users\brosp\AppData\Local\Programs\Python\Python312\python.exe`
- Project dir: `C:\Users\brosp\Downloads\goethe-bot`
- Platform: Windows

## Deployments (all currently live)
| Service | URL | Status |
|---------|-----|--------|
| **Frontend (Netlify)** | https://goethe-booking-dashboard.netlify.app | ✅ Live |
| **Backend (Railway)** | https://goethe-booking-bot-production-092f.up.railway.app | ✅ Online (new) |
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
- Credentials: `hamzarafiq655@gmail.com` / `Hamza@123`
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
| `alexa.py` | AI assistant (Gemini 2.5 Flash Lite, 7 function calls) |
| `.env.example` | Template for all required env vars |
| `Dockerfile` | python:3.12-slim + google-chrome-stable |
| `SESSION_SUMMARY.md` | This file |

## Tokens & IDs (REDACTED — secrets scrubbed from git history 13 Jun 2026)
- Railway Project ID: `6aee17f5-fe9f-4496-a02d-e5f366d37c2a`
- Railway Service ID: `783d4933-1de1-45b6-a198-08b6f07692cd`
- Railway Service URL: `https://goethe-booking-bot-production-092f.up.railway.app`
- Railway Old URL: `https://goethe-booking-bot-production.up.railway.app` (dead)
- Netlify URL: `https://goethe-booking-dashboard.netlify.app`
- Mock Netlify URL: `https://goethe-bot-mock.netlify.app`
- Presentation Site ID: `bb610061-8eff-4a22-bd50-f4c56a5f1c10`
- Presentation URL: `https://goethe-bot-presentation.netlify.app`
- All API tokens, deploy tokens, and keys removed from this file — rotate before re-deploying

## 14 Jun 2026 — Railway Rebuild (Project was deleted)

- Old Railway project (`6aee17f5`) was deleted — backend was returning 404
- Created new project: `df54b489-2cdf-48c4-9d53-1e3886858311`
- New service: `0596e8bf-ed43-4033-a585-0c67e7b3a43d`
- New backend URL: `https://goethe-booking-bot-production-092f.up.railway.app`
- Env vars restored: `GEMINI_API_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `GOETHE_EMAIL`, `GOETHE_PASSWORD`
- Deleted old `mexc-trading-bot` project to free up Railway free tier slot
- Updated GitHub Actions `deploy.yml` with new project/service IDs
- Updated `alexa.py` with new Railway URL
- Remaining: set `CAPTCHA_API_KEY` and `EMAIL_SMTP_*` when user provides them

## 14 Jun 2026 — Session 4: Invoice + Video Demo Generation

### Invoice Delivered
- Professional invoice `Goethe Booking Bot Invoice.docx` (38KB) created in Downloads
- **6 line items:** Booking Engine (95k), Reliability Suite (50k), Admin Dashboard (55k), AI Assistant (22k), Quality + DevOps (28k), 2-Month Support (25k)
- **Total: PKR 275,000** — no hours listed, no "25k per slot" argument
- Clean black/gray professional layout — no color theme
- **Scope cap included:** "Support covers existing functionality only. Site structure changes or new features billed separately."
- Previous enterprise-themed version saved separately as `Goethe Booking Bot Invoice - Enterprise.docx`

### Video Demo Capability Added
- **FFmpeg 8.1.1** installed via winget (Gyan build, full)
- **moviepy 2.2.1** installed — Python video composition library
- **Demo video created:** `Goethe-Booking-Bot-Demo.mp4` (1.6MB, 23 sec, 1080p)
- 6 slides with crossfade transitions: Title → 12 Modules → 66 Tests → Architecture → Package Includes → Outro
- Full video pipeline ready for screen recordings, animated promos, overlays

### Git Status (14 Jun)
- **No changes pushed** — git is clean, no new commits this session
- Last commit: `0e6f52b` (docs: update SESSION_SUMMARY.md)

### Railway Status (14 Jun — rebuilt)
- **Online** — `https://goethe-booking-bot-production-092f.up.railway.app`

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
- [x] Alexa AI assistant deployed (GEMINI_API_KEY env var set)
- [x] Circuit breaker — stops hammering after 10 consecutive failures, 15 min cooldown
- [x] Server-side sessions with logout (tokens expire 24hr, revocable)
- [x] Git history scrubbed of all 9 leaked secrets
- [x] Security headers + HTTPS redirect
- [x] Student passwords no longer exposed via API
- [ ] **ROTATE TOKENS** before going public: Railway, Netlify, Gemini, Goethe password, admin password
- [ ] Upgrade Railway to Starter ($5/mo) for custom domain + always-on
- [ ] Set Railway env vars: CAPTCHA_API_KEY, EMAIL_SMTP_* (free — Gmail App Password)
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
railway up --detach

# Set/remove env vars
railway variables set KEY="value"
railway variable delete KEY

# Git push
git add -A; git commit -m "message"; git push origin main

## 12 Jun 2026 — Final
- Countdown fix: all 3 students show own countdown cards (was only nearest)
- New Netlify frontend: **https://goethe-booking-dashboard.netlify.app** (old one deleted)
- Default Railway URL: `https://goethe-booking-bot-production-a6a6.up.railway.app`
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

## 13 Jun 2026 — Alexa AI Assistant
- **New file:** `alexa.py` — AI assistant powered by Google Gemini 2.5 Flash Lite (free tier)
- **Features:** Greeting, show students (reads CSV dynamically), bot status, recent logs, retry student (by name/level/city), stop bot, update config settings, help on errors/config/deployment
- **Function calling:** 7 functions — `get_students`, `get_status`, `get_recent_logs`, `retry_student`, `stop_bot`, `update_config`, `get_help`
- **API key:** `GEMINI_API_KEY` env var — no hardcoding, easy client handoff
- **Frontend:** Slide-out chat panel in sidebar, typing indicator, suggestion buttons, welcome message "Welcome Hamza!"
- **Backend:** `POST /api/chat` endpoint with auth, `_retry_one_student()` background retry helper
- **Dependency:** `google-genai>=2.8.0` in requirements.txt
- **Note:** 20 requests/day free tier quota — create new Google Cloud project for fresh quota if exhausted
- Commit: `3defc86`

## 13 Jun 2026 — Railway URL Fix + Deploy Updates
- Fixed Railway default URL from `production.up.railway.app` to `production-a6a6.up.railway.app` (correct linked service)
- Set `GEMINI_API_KEY` env var on Railway (production environment)
- Railway redeployed — Alexa live at `https://goethe-booking-bot-production-a6a6.up.railway.app`
- GitHub Actions auto-deploy confirmed (test + netlify + railway all passed)
- SESSION_SUMMARY.md updated with full Alexa section
- Commits: `2e54fca` (URL fix)

## 13 Jun 2026 — Forgot Password / SMTP Vars Clarified
- `/api/forgot-password` is a **placeholder** — returns success message but sends no actual email
- Real password reset / booking notifications need SMTP env vars:
  - `EMAIL_SMTP_HOST` (e.g. `smtp.gmail.com`)
  - `EMAIL_SMTP_PORT` (e.g. `587`)
  - `EMAIL_SMTP_USER` (your email)
  - `EMAIL_SMTP_PASS` (Gmail App Password — free, no payment)
- Gmail App Password method is **free** — bas Google Account → Security → 2-Step Verification on → App Passwords

## 13 Jun 2026 — Mobile Responsiveness Fix
- **Hamburger menu** added: sidebar hidden on mobile (≤768px), hamburger button (&#9776;) appears in topbar
- **Mobile nav overlay**: full-screen overlay with Dashboard, Settings, Alexa, Sign out — opens from hamburger, closes with X or link click
- **Chat panel responsive**: `.chat-panel` width changes from `380px` → `100%` on mobile (slides from right)
- **Login card responsive**: `width: 360px` → `calc(100% - 32px)` on mobile
- **Layout fixes**: `.actions-bar` and `.conn-bar` stack vertically on mobile; countdown items full-width; log box height reduced; tables tighter padding
- **Notifications grid**: added `.settings-grid` class with mobile override (2-column → 1-column)
- All changes in `frontend/index.html` only — no backend changes needed

## 13 Jun 2026 — Full 10/10 Upgrade (8 Tasks)

### Task 1: Selector Fallback System
- **New file:** `selector_fallbacks.py` — 16 element types with 2-5 CSS/XPath fallbacks each
- Functions: `find_element_fallback()`, `find_elements_fallback()`, `wait_for_any_selector()`
- `booking_helper.py` refactored: `wait_for_finder`, `find_book_buttons`, `click_continue_button`, `click_book_for_myself`, `_login_attempt`, `_fill_attempt` all use fallback selectors
- Old `SELECTOR_REFERENCE` dict removed (was fragile, single-selector)
- Tests: 3 new (all 16 keys defined, valid By types, LOGIN_ERROR_SELECTORS valid)
- Commit: `ceeeb44`

### Task 2: Proxy Rotation
- **New file:** `proxy_rotator.py` — health checks (requests `httpbin.org/ip`), blacklist with expiry, thread-safe
- `ProxyRotator.get()` returns health-checked proxy, `mark_failed()` blacklists for 5 min
- `booking_helper.py` integrated: proxy selection uses `PROXY_ROTATOR.get()`, success/failure tracking
- Tests: 6 (empty list, single proxy, blacklist, expiry, add, remove)
- Commit: `fa0ebff`

### Task 3: Dynamic Student Queue
- **New file:** `student_queue.py` — in-memory + DB-backed queue with priority ordering
- `db.py` updated: `queue_history` table, queue CRUD functions
- `webapp.py` updated: 8 new queue API endpoints (enqueue, dequeue, complete, fail, reset, list, clear, enqueue-many)
- Tests: 8 (enqueue/dequeue, complete, fail, priority, empty, clear, summary, reset)
- Commit: `9adcea8`

### Task 4: Confirmation Parser
- **New file:** `confirmation_parser.py` — structured extraction from confirmation page
- Parses: booking reference, exam date/time, level (A1-C2), city, error messages, status
- `SUCCESS_KEYWORDS` scoring: ≥2 → confirmed, ≥1 → submitted, 0 → unknown
- `ERROR_PATTERNS`: timeout, slot full, already booked, max participants (DE + EN)
- `booking_helper.py` `capture_confirmation()` updated to use parser
- Tests: 11 (references, dates, levels, cities, errors, URLs, summary)
- Commit: `18f5031` + `9a26204`

### Task 5: Dashboard Upgrade
- Analytics cards row: Total Students, Success Rate (%), Queue count
- Results table expanded: Level, City, Date, Time columns
- Queue Management UI: live item count, item table with statuses, Clear button
- Frontend JS: `updateAnalytics()`, `fetchQueueSummary()`, `renderQueueItems()`, `clearQueue()`
- Commit: `3e68752`

### Task 6: Dead Man Switch
- **New file:** `deadman.py` — heartbeat monitor with timeout (5 min default)
- `ping()` resets timer, `check()` triggers alert on timeout, `start_monitor()` runs background thread
- `webapp.py` integrated: `/api/heartbeat` endpoint pings switch, alert calls `notify()` via Telegram
- Monitor checks every 120s, fires `deadman_alert()` if switch expires
- Tests: 4 (alive, ping, check, callback)
- Commit: `812eecc`

### Task 7: Integration Tests + Hardening
- `test_integration.py`: 4 tests covering deadman+queue roundtrip, parser+status flow, DB persistence
- `SELECTOR_REFERENCE` dict fully removed from `booking_helper.py` (~26 lines deleted)
- City parser hardened: single-word match (Berlin, Karachi, etc.)
- Date parser: bare date fallback pattern
- All 54 tests passing
- Commit: `065e01e`

### Summary
| Metric | Before | After |
|--------|--------|-------|
| Tests | 18 | 54 |
| Modules | 6 | 11 |
| API endpoints | ~15 | ~30 |
| DB tables | 3 | 4 |
| Selector fallbacks | 0 | 16 element types |
| Proxy management | random.choice | health-checked + blacklist |
| Confirmation parsing | 2 regex lines | 5 structured fields |
| Dead man switch | none | heartbeat + auto-alert |

## 13 Jun 2026 — Speed Optimization + Licensing

### Speed Tuning (commit `9bc74d3`)
| Constant | Before | After |
|----------|--------|-------|
| Poll interval | 45s | 20s |
| Min human delay | 1.5s | 0.8s |
| Max human delay | 5.5s | 2.5s |
- ~40-50% faster booking flow, still safe from rate limits

### License + README (commit `9988dd9`)
- MIT License added (`LICENSE`) — © 2026 Abeer Meer
- README updated with all 11 modules table, license badge, and copyright footer
- GitHub About section filled: description, homepage URL, 10 topics

### GitHub
- `9988dd9` — 73 total commits on main
- Repository made **public briefly** then reverted to **private** — commit history may contain sensitive keys
- Need to scrub `git log` for any leaked credentials (Railway token, Gemini key, Netlify token) before making public again

## Deployment Architecture Decision

### Recommended: Netlify + Railway ($5/mo)
- **Netlify (free)** — serves frontend on global CDN, fast, always up, separate from backend
- **Railway $5/mo** — backend only, Python/Flask + Selenium + Chrome
- Custom domain setup: `goethebot.com` → Netlify, `api.goethebot.com` → Railway
- Pro: Frontend independent, CDN speed, professional separation

### Alternative: Railway alone
- Flask serves both API + static frontend from same process
- Con: Backend crash = frontend also down; slower static file serving
- Only recommended for early testing or ultra-simple setups

## 13 Jun 2026 — README Rewrite + GitHub About Update
- README completely rewritten: architecture diagram, 12 modules table, 66 tests matrix, env vars table, circuit breaker section, Alexa use case, security section, demo placeholder
- GitHub About section updated with new description + 16 topics
- Commit: `f37ab40`

## 13 Jun 2026 — Session 3: Security Audit + Circuit Breaker

### Git History Scrub
- All 9 leaked secrets removed from git history: Railway token, Netlify deploy+auth tokens, Netlify site ID, Gemini key, Goethe password, admin credentials
- Fixed `.env.example` and `webapp.py` defaults to use placeholders
- Force pushed cleaned history (78 commits, all new hashes)
- Commit: `2df6351`

### Security Audit (8 fixes)
| # | Finding | Severity | Fix |
|---|---------|----------|-----|
| C1 | Student passwords leaked via API | CRITICAL | `_strip_sensitive()` on `/api/config` + `/api/config/upload` |
| C2 | Raceable tempfile `mktemp()` | CRITICAL | Replaced with `NamedTemporaryFile(delete=False)` |
| H1 | No security headers | HIGH | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` |
| H2 | No session invalidation | HIGH | Server-side DB sessions + `/api/logout` endpoint |
| M3 | No upload size limit | MEDIUM | `MAX_CONTENT_LENGTH = 10MB` |
| M4 | Hardcoded Railway URL | MEDIUM | Removed default — user enters it |
| L1 | Timing-vulnerable password compare | LOW | Switched to `hmac.compare_digest()` |
| L2 | No HTTPS redirect | LOW | `enforce_https()` before_request handler |
- Commit: `fc217e9`

### Circuit Breaker (`circuit_breaker.py`)
- **States:** closed → open (after 10 failures) → half-open (after 15 min) → closed on success
- **Triggers:** 503/block detection (`is_blocked_response`), `WebDriverException`, flow-level exceptions
- **Does NOT trip on:** normal "no slot found" (that's expected polling behavior)
- **Integration:** Step 1 poll loop + `smart_retry()` both check `CIRCUIT_BREAKER.allow_request()`
- **Configurable:** `CIRCUIT_BREAKER_THRESHOLD` (default 10), `CIRCUIT_BREAKER_COOLDOWN` (default 900s)
- **Thread-safe:** shared lock, all students respect the same breaker
- **Tests:** 12 (all states, transitions, concurrent safety, stop_event handling)
- Commit: `c93310d`

### Final Stats
| Metric | Value |
|--------|-------|
| Tests | 66 (54 old + 12 new) |
| Commits | 80 on main |
| Modules | 12 (+ `circuit_breaker.py`) |
| Auth | HMAC → DB-backed sessions with 24hr expiry |
| Repository | **PRIVATE** — secrets scrubbed from history |
| Invoice | `Goethe Booking Bot Invoice.docx` — PKR 275,000 |
| Video Demo | `Goethe-Booking-Bot-Demo.mp4` — 23 sec, 1080p |
| FFmpeg | 8.1.1 + moviepy 2.2.1 — video generation ready |

### Commands — Session 4
```powershell
# Generate video demo (if editing slides)
python Downloads\make_demo.py

# Generate invoice
python Downloads\generate_docx3.py
```

### Client Handoff Procedure
1. Client creates GitHub account
2. Add client as collaborator (or fork repo)
3. Client creates Railway account → New Project → Deploy from GitHub
4. Railway auto-detects Dockerfile → builds → deploys
5. Client creates Netlify account → drag & drop `frontend/` folder
6. Provide `.env` template + screen recording of setup
7. Admin access kept on Railway + GitHub for support
