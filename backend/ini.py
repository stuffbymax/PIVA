#!/usr/bin/env python3
"""
ini.py - initializes the local SQLite database for the self-hosted
photos backend.

Responsibilities:
    * Create the data directory (and data/sqlite/) if it doesn't exist.
    * Apply schema.sql to create the users/media/token_blocklist tables.
    * Be safe to run multiple times without destroying existing data
      (uses `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS`,
      and never drops or truncates anything).

Usage:
    python ini.py
    python ini.py --db-path data/app.db --schema schema.sql
"""

import argparse
import os
import sqlite3
import sys

DEFAULT_DB_PATH = os.path.join("data", "app.db")
DEFAULT_SCHEMA_PATH = "schema.sql"


def init_db(db_path: str = DEFAULT_DB_PATH, schema_path: str = DEFAULT_SCHEMA_PATH) -> None:
    project_root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_root, db_path) if not os.path.isabs(db_path) else db_path
    schema_path = (
        os.path.join(project_root, schema_path) if not os.path.isabs(schema_path) else schema_path
    )

    data_dir = os.path.dirname(db_path)
    if data_dir and not os.path.isdir(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created data directory: {data_dir}")

    # Also make sure the MinIO data directory exists so it's ready for
    # `minio server` to use on first run.
    minio_dir = os.path.join(project_root, "data", "minio")
    if not os.path.isdir(minio_dir):
        os.makedirs(minio_dir, exist_ok=True)
        print(f"Created MinIO data directory: {minio_dir}")

    if not os.path.isfile(schema_path):
        print(f"ERROR: schema file not found at {schema_path}", file=sys.stderr)
        sys.exit(1)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    db_existed = os.path.isfile(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    action = "Verified existing" if db_existed else "Initialized new"
    print(f"{action} SQLite database at {db_path}")
    print("Tables ready: users, media, token_blocklist")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize the SQLite database.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to the SQLite file")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA_PATH, help="Path to schema.sql")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    init_db(db_path=args.db_path, schema_path=args.schema)
