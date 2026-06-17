# Live Dashboard + Level Filter + Goethe Schedule Scraper

## 1. Live Dashboard
- New `/api/v1/live-status` endpoint returns `{summary: {total, booked, failed, pending}, students: [{name, level, status, updated_at}]}`
- Frontend: Summary cards (4 counters) + per-student table with color-coded status badges
- Auto-refresh every 2s via `setInterval` — clean up on page unload

## 2. Exam Level Dropdown
- `<select>` with All/A1/A2/B1 near Start button
- `POST /api/v1/start` accepts optional `level` field
- `run_students_web()` filters student list by level before booking

## 3. Goethe Schedule Scraper
- `goethe_scraper.py` uses `requests` + `BeautifulSoup` to scrape goethe.de exam dates
- Caches result for 1 hour (in-memory) to avoid hammering
- Returns A1/A2/B1 dates, fees, locations
- `/api/v1/goethe-schedule` endpoint serves scraped data
- Frontend: Table showing exam dates, fees, locations — refreshed on page load
