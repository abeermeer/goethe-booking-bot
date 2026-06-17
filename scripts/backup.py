"""Database and config backup utility.

Usage:
  python scripts/backup.py                    # backup to default dir
  python scripts/backup.py --dir /tmp/backups  # custom dir
  python scripts/backup.py --restore latest    # restore latest backup
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_BACKUP_DIR = PROJECT_DIR / "backups"
DB_PATH = PROJECT_DIR / "booking_bot.db"
CONFIG_PATH = PROJECT_DIR / "config.csv"


def backup(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subdir = target_dir / f"backup_{ts}"
    backup_subdir.mkdir()

    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_subdir / "booking_bot.db")
        print(f"  DB:  {DB_PATH} → {backup_subdir / 'booking_bot.db'}")
    else:
        print("  DB:  (not found, skipped)")

    if CONFIG_PATH.exists():
        shutil.copy2(CONFIG_PATH, backup_subdir / "config.csv")
        print(f"  CSV: {CONFIG_PATH} → {backup_subdir / 'config.csv'}")
    else:
        print("  CSV: (not found, skipped)")

    print(f"\nBackup complete: {backup_subdir}")
    return backup_subdir


def restore(source_dir: Path) -> None:
    if not source_dir.is_dir():
        print(f"Error: {source_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    db_src = source_dir / "booking_bot.db"
    csv_src = source_dir / "config.csv"

    if db_src.exists():
        shutil.copy2(db_src, DB_PATH)
        print(f"  DB restored: {db_src} → {DB_PATH}")
    if csv_src.exists():
        shutil.copy2(csv_src, CONFIG_PATH)
        print(f"  CSV restored: {csv_src} → {CONFIG_PATH}")

    print(f"\nRestore complete from {source_dir}")


def list_backups(backup_dir: Path) -> list[Path]:
    dirs = sorted(backup_dir.glob("backup_*"))
    if not dirs:
        print("No backups found.")
        return []
    print(f"Backups in {backup_dir}:")
    for i, d in enumerate(dirs, 1):
        size = sum(f.stat().st_size for f in d.glob("*") if f.is_file())
        print(f"  {i}. {d.name}  ({size / 1024:.1f} KB)")
    return dirs


def main():
    parser = argparse.ArgumentParser(description="Goethe Bot backup/restore utility")
    parser.add_argument("--dir", default=str(DEFAULT_BACKUP_DIR), help="Backup directory")
    parser.add_argument("--restore", nargs="?", const="latest", help="Restore from backup")
    parser.add_argument("--list", action="store_true", help="List backups")
    args = parser.parse_args()

    backup_dir = Path(args.dir)

    if args.list:
        list_backups(backup_dir)
        return

    if args.restore:
        dirs = sorted(backup_dir.glob("backup_*"))
        if not dirs:
            print("No backups to restore.")
            sys.exit(1)
        if args.restore == "latest":
            restore(dirs[-1])
        else:
            restore(Path(args.restore))
        return

    backup(backup_dir)


if __name__ == "__main__":
    main()
