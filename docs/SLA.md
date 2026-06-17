# Service Level Agreement (SLA)

## Service Description
The Goethe Booking Bot automates the booking of exam slots at Goethe-Institut Pakistan. The system consists of:
- **Backend API** (Railway): Booking engine, queue management, authentication
- **Frontend Dashboard** (Netlify): Web UI for monitoring and control
- **Telegram Bot**: Notifications and alerts

## Availability Targets

| Component | Target | Measurement |
|-----------|--------|-------------|
| Backend API | 99.5% uptime (monthly) | Health endpoint every 60s |
| Frontend Dashboard | 99.9% uptime (monthly) | Netlify CDN SLA |
| Telegram Notifications | 99% delivery within 5 min | End-to-end ping |

## Performance Targets

| Metric | Target | Measured By |
|--------|--------|-------------|
| Booking time per student | < 60s | Bot internal timing |
| Health check latency | < 500ms p95 | k6 load test |
| Login response time | < 1s p95 | k6 load test |
| Log delivery to dashboard | < 3s | Real-time log viewer |
| Queue processing rate | > 10 students/min | Throughput monitoring |

## Support

| Priority | Response Time | Examples |
|----------|--------------|----------|
| Critical | < 1 hour | Bot not booking, all students failing |
| High | < 4 hours | Single student failing, dashboard slow |
| Medium | < 24 hours | UI bugs, non-critical errors |
| Low | < 72 hours | Feature requests, cosmetic issues |

## Escalation
1. **First response**: Telegram alert automations
2. **Admin contact**: hamzarafiq655@gmail.com
3. **Emergency**: Redeploy or rollback via Railway dashboard

## Exclusions
The following are NOT covered by this SLA:
- Goethe-Institut website downtime or changes
- CAPTCHA service (2Captcha) availability
- Internet connectivity issues at client location
- Third-party API rate limiting

## Reporting
- Uptime and performance data available at `/api/v1/metrics`
- Audit log available at `/api/v1/audit-log`
- Deployment history visible at GitHub Actions
