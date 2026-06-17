# Backup & Rollback

## Automated Backups

The backup script copies `booking_bot.db` + `config.csv` into timestamped folders:

```bash
python scripts/backup.py             # backup to backups/
python scripts/backup.py --list      # list recent backups
python scripts/backup.py --restore   # restore latest
```

Backups are stored under `backups/backup_YYYYMMDD_HHMMSS/`.

## Railway Deploy Rollback

1. Open [Railway Dashboard](https://railway.app/dashboard)
2. Select project `df54b489-2cdf-48c4-9d53-1e3886858311`
3. Select service `0596e8bf-ed43-4033-a585-0c67e7b3a43d`
4. Click **Deploys** → find the last known-good deploy
5. Click **⋮** → **Redeploy**

## Git Rollback (Code)

```bash
git revert HEAD                 # revert last commit
git revert <sha>..HEAD          # revert a range
git push origin main
```

## Emergency Rollback Checklist

1. **Is the app down?** → Redeploy last-known-good Railway deploy
2. **Is it a DB schema issue?** → Restore DB from latest backup via `scripts/backup.py --restore`
3. **Is it a config issue?** → Revert config.csv, re-upload via dashboard
4. **Is it a code bug?** → `git revert` and push, Railway auto-deploys

## Recovery Objective

| Metric | Target |
|--------|--------|
| RPO (data loss tolerance) | 24 hours |
| RTO (restore time) | < 15 minutes |
