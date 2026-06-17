"""Rotate sensitive credentials.

Usage:
  python scripts/rotate_secrets.py
  python scripts/rotate_secrets.py --apply   # actually rotate (default: dry-run)

Rotates:
  - AUTH_PASSWORD (new random 24-char string)
  - AUTH_SALT (new random 32-char string)

After rotation, set the new values as Railway environment variables.
"""
import argparse
import os
import secrets
import string
import sys


def generate_password(length=24):
    chars = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_salt(length=32):
    return secrets.token_hex(length // 2)


def main():
    parser = argparse.ArgumentParser(description="Rotate secrets for Goethe Bot")
    parser.add_argument("--apply", action="store_true", help="Apply rotation (default: dry-run)")
    args = parser.parse_args()

    new_password = generate_password()
    new_salt = generate_salt()

    print("=" * 50)
    print("  Secret Rotation — Dry Run" if not args.apply else "  Secret Rotation — APPLIED")
    print("=" * 50)
    print()
    print("  AUTH_PASSWORD = " + new_password)
    print("  AUTH_SALT     = " + new_salt)
    print()

    if not args.apply:
        print("  Pass --apply to actually rotate.")
        print("  Then update Railway env vars with the new values.")
    else:
        print("  Update Railway env vars:")
        print(f"    railway variables set AUTH_PASSWORD={new_password}")
        print(f"    railway variables set AUTH_SALT={new_salt}")
        print("  Then redeploy:")
        print("    railway up --detach --service 0596e8bf-ed43-4033-a585-0c67e7b3a43d")


if __name__ == "__main__":
    main()
