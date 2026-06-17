# Client Training Guide

## Overview
The Goethe Booking Bot automates exam slot booking at Goethe-Institut Pakistan. This guide covers the three roles: **Admin**, **Operator**, and **Viewer**.

## Admin Role

### Access
- URL: https://goethe-booking-dashboard.netlify.app
- Login with admin email/password (provided separately)
- Bookmark the URL; it also works as a PWA (install from browser menu)

### Daily Operations
1. **Load Students**: Upload `config.csv` with student data
2. **Start Booking**: Click "Start" — bot works through the queue
3. **Monitor**: Watch logs in real time; check student status table
4. **Handle Failures**: Retry failed students manually from the results view

### Scheduled Booking
1. Set date/time + student list
2. Bot auto-starts at the scheduled time
3. Check Telegram for completion notification

## Operator Role

### Key Screens
- **Dashboard**: Overview of bot status, student counts, success rate
- **Logs**: Real-time and historical logs
- **Results**: Per-student booking outcomes with timestamps

### What to Watch For
- `ERROR` level logs → investigate immediately
- Circuit breaker OPEN state → wait 15 min or check Goethe site manually
- Dead man switch alert → bot may be hung; restart from dashboard

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Bot won't start | Load config.csv first |
| Students stay pending | Check bot status; it may still be running |
| "Invalid email or password" | Check AUTH env vars on Railway |
| Dashboard not loading | Clear browser cache or use incognito |
| Telegram not notifying | Check TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID |

## Best Practices
1. Always verify config.csv before upload
2. Run booking 24+ hours before exam deadline
3. Keep backup of config.csv locally
4. Monitor Telegram for bot alerts
