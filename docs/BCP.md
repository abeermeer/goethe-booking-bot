# Business Continuity Plan (BCP)

## Overview
This plan ensures the Goethe Booking Bot can recover from disruptions and continue booking operations with minimal downtime.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Railway outage | App unreachable | Auto-redeploy from Git; Railway SLA 99.95% |
| Netlify outage | Dashboard unreachable | Netlify CDN; fallback to direct Railway URL |
| Goethe website changes | Booking fails | SELENIUM selectors fallback system (3 levels) |
| Database corruption | Lost state | Daily backups via `scripts/backup.py` |
| CAPTCHA service down | Cannot login | 2Captcha backup; manual override option |
| Chrome/Chromium crash | Booking hangs | Dead man switch auto-notifies; circuit breaker resets |
| Telegram API down | No notifications | Notifications degrade gracefully; check polling works |
| Rate limiting by Goethe | Booking slowed | Bounded exponential backoff; configurable delays |

## Recovery Procedures

### App Unreachable
1. Check Railway status: https://status.railway.app
2. Redeploy: `railway up --detach --service 0596e8bf-ed43-4033-a585-0c67e7b3a43d`
3. If persistent, rollback to last known-good deploy (Railway dashboard → Deploys → Redeploy)

### Database Recovery
1. `python scripts/backup.py --list` to find latest backup
2. `python scripts/backup.py --restore` to restore
3. Verify data: `curl https://app/api/v1/db/students`

### Booking Failure
1. Check `/api/v1/health` for circuit breaker state
2. If circuit breaker is OPEN, wait for cooldown (default 15 min)
3. Adjust timing constants in `booking_helper.py` if Goethe changed their site

## Contact
- **Admin**: hamzarafiq655@gmail.com
- **Telegram**: @Hamzabookingbot (notifications)
- **GitHub**: abeermeer/goethe-booking-bot (issues)

## Review Schedule
This BCP should be reviewed quarterly or after any major infrastructure change.
