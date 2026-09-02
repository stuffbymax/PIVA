#!/usr/bin/env python3
"""
Generates strong random SECRET_KEY and JWT_SECRET_KEY values for the
photo backend and writes them into a .env file.

Usage:
    python3 generate_secrets.py                # creates/updates .env in cwd
    python3 generate_secrets.py --path /other/.env
    python3 generate_secrets.py --print-only    # just print, don't write a file
"""
import argparse
import os
import secrets


def generate_key(num_bytes: int = 32) -> str:
    """URL-safe, 32 bytes -> 43-char token. 32 bytes is comfortably more
    entropy than these keys need (HMAC-SHA256 already saturates around
    32 bytes), so this isn't worth going bigger."""
    return secrets.token_urlsafe(num_bytes)


def load_existing(path):
    """Preserve any other lines already in the .env (e.g. DATABASE_URL)
    instead of clobbering the whole file."""
    lines = []
    if os.path.exists(path):
        with open(path, "r") as f:
            lines = f.read().splitlines()
    return lines


def upsert(lines, key, value):
    prefix = f"{key}="
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            lines[i] = f"{key}={value}"
            return lines
    lines.append(f"{key}={value}")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=".env", help="Path to the .env file (default: ./.env)")
    parser.add_argument("--print-only", action="store_true", help="Print the keys instead of writing a file")
    parser.add_argument("--force", action="store_true", help="Overwrite existing keys without prompting")
    args = parser.parse_args()

    secret_key = generate_key()
    jwt_secret_key = generate_key()

    if args.print_only:
        print(f"SECRET_KEY={secret_key}")
        print(f"JWT_SECRET_KEY={jwt_secret_key}")
        return

    lines = load_existing(args.path)
    already_has_keys = any(l.startswith("SECRET_KEY=") or l.startswith("JWT_SECRET_KEY=") for l in lines)

    if already_has_keys and not args.force:
        answer = input(f"{args.path} already has key(s) set. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted. No changes made.")
            return

    lines = upsert(lines, "SECRET_KEY", secret_key)
    lines = upsert(lines, "JWT_SECRET_KEY", jwt_secret_key)

    with open(args.path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote new SECRET_KEY and JWT_SECRET_KEY to {args.path}")
    print("(Keep this file out of git -- it's already in .gitignore.)")


if __name__ == "__main__":
    main()
