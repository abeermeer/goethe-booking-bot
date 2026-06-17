# Changelog

## [2.0.0] - 2026-06-18 — Security & Polish Release

### Added
- CSP, HSTS, XSS-Protection, Referrer-Policy, Permissions-Policy headers
- CORS whitelist (restricted from `*`)
- Rate limit headers (`Retry-After`, `X-RateLimit-Remaining`) on 429
- `/api/health` endpoint with DB + uptime + circuit breaker metrics
- Sentry error tracking (`SENTRY_DSN` env var)
- Audit log (`audit_log` table, `/api/audit-log` endpoint)
- Session token rotation (`/api/refresh`)
- Brute force account lockout (30 failed = 15min ban)
- Swagger docs at `/api/docs/`
- Alembic DB migrations
- Docker multi-stage build
- PWA offline support (Service Worker)
- PWA icons (48px to 512px)
- Frontend error boundary (global JS error handler)
- Dark/light theme toggle (`T` keyboard shortcut)
- Keyboard accessibility (`:focus-visible` rings, `sr-only`)
- Form validation UX (password strength, email format hints)
- Loading state overlay on API calls
- E2E Playwright test skeleton
- pip-audit security scan in CI
- Deploy notifications via Telegram

### Changed
- README updated with all new features
- SESSION_SUMMARY.md updated with Session 10 & 11
- Dead man switch now only monitors during booking (no false alarms)
