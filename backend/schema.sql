-- Standalone SQLite schema for the self-hosted photos backend.
-- This mirrors the SQLAlchemy models in backend/app/models/*.py.
-- It exists so the schema can be inspected, reviewed, or applied
-- independently of the Python ORM, and is what ini.py applies.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS media (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    filename       TEXT NOT NULL,
    object_key     TEXT NOT NULL,
    thumbnail_key  TEXT,
    mime_type      TEXT NOT NULL,
    size           INTEGER NOT NULL,
    file_hash      TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')),
    modified_at    TEXT,
    width          INTEGER,
    height         INTEGER,
    duration       REAL,
    uploaded_at    TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (user_id, file_hash)
);

CREATE INDEX IF NOT EXISTS ix_media_user_id ON media (user_id);
CREATE INDEX IF NOT EXISTS ix_media_created_at ON media (created_at);
CREATE INDEX IF NOT EXISTS ix_media_user_created ON media (user_id, created_at);

-- Revoked JWTs (used to support real logout). A row here means the
-- token's jti is no longer valid, even though it hasn't expired yet.
CREATE TABLE IF NOT EXISTS token_blocklist (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    jti        TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS ix_token_blocklist_jti ON token_blocklist (jti);
