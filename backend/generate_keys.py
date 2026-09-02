#!/usr/bin/env python3
"""
Generate secure random values for SECRET_KEY and JWT_SECRET_KEY.

Usage:
    python3 generate_keys.py            # print the keys
    python3 generate_keys.py --write    # write/update them directly in .env
    python3 generate_keys.py --write --env-file path/to/.env

Run this once per deployment. Never reuse the same keys across
environments (dev/staging/prod), and never commit the resulting .env
file to version control.
"""
import argparse
import os
import secrets


def generate_key(num_bytes: int = 32) -> str:
    """URL-safe, high-entropy random string. 32 bytes -> 43 base64 chars,
    which is comfortably more entropy than either key needs."""
    return secrets.token_urlsafe(num_bytes)


def write_env(env_path: str, secret_key: str, jwt_secret_key: str) -> None:
    """
    Updates SECRET_KEY and JWT_SECRET_KEY in the given .env file,
    preserving every other line. Creates the file from .env.example
    (or from scratch) if it doesn't exist yet.
    """
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    elif os.path.exists(".env.example"):
        with open(".env.example", "r") as f:
            lines = f.readlines()

    seen_secret = seen_jwt = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("SECRET_KEY="):
            new_lines.append(f"SECRET_KEY={secret_key}\n")
            seen_secret = True
        elif stripped.startswith("JWT_SECRET_KEY="):
            new_lines.append(f"JWT_SECRET_KEY={jwt_secret_key}\n")
            seen_jwt = True
        else:
            new_lines.append(line)

    if not seen_secret:
        new_lines.append(f"SECRET_KEY={secret_key}\n")
    if not seen_jwt:
        new_lines.append(f"JWT_SECRET_KEY={jwt_secret_key}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true",
                         help="Write the keys into an .env file instead of just printing them.")
    parser.add_argument("--env-file", default=".env",
                         help="Path to the .env file to write to (default: .env)")
    parser.add_argument("--bytes", type=int, default=32,
                         help="Random bytes of entropy per key (default: 32, i.e. 256 bits)")
    args = parser.parse_args()

    secret_key = generate_key(args.bytes)
    jwt_secret_key = generate_key(args.bytes)

    if args.write:
        write_env(args.env_file, secret_key, jwt_secret_key)
        print(f"Wrote new SECRET_KEY and JWT_SECRET_KEY to {args.env_file}")
        print("(existing values, if any, were overwritten; other lines were left untouched)")
    else:
        print("Add these to your .env file:\n")
        print(f"SECRET_KEY={secret_key}")
        print(f"JWT_SECRET_KEY={jwt_secret_key}")
        print("\nOr re-run with --write to update .env automatically.")


if __name__ == "__main__":
    main()
