# Self-Hosted Photos Backend (Prototype)

A Flask + SQLite + MinIO backend for a self-hosted, Google Photos-style
backup service. This repo currently contains the **backend only** —
no Docker, no containers. Everything runs directly on the host.

```
phone (Flutter, not in this checkout) → backup queue → Flask → MinIO → SQLite → gallery
```

## Project layout

```
.
├── backend/            Flask application
│   ├── app/
│   │   ├── models/      SQLAlchemy models (User, Media, TokenBlocklist)
│   │   ├── routes/      HTTP endpoints (auth, media)
│   │   ├── services/    Business logic (auth, media, MinIO, thumbnails)
│   │   └── utils/       Hashing + consistent JSON error handling
│   ├── tests/           pytest suite (MinIO is mocked, no server needed)
│   ├── requirements.txt
│   └── run.py           Entrypoint
├── data/                 Created at init time: data/app.db, data/minio/
├── schema.sql            Standalone SQL schema (mirrors the SQLAlchemy models)
├── ini.py                Initializes SQLite; safe to re-run
├── .env.example
├── API.md                Full endpoint reference with curl examples
└── README.md
```

## 1. Install Python dependencies

Requires Python 3.10+.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure environment variables

From the **project root** (not inside `backend/`):

```bash
cp .env.example .env
```

Open `.env` and adjust `JWT_SECRET_KEY` at minimum. Defaults otherwise
work for local development. `backend/run.py` auto-discovers this `.env`
file even though it's launched from inside `backend/`.

## 3. Initialize SQLite

From the project root:

```bash
python ini.py
```

This creates `data/` (and `data/minio/`) if missing, and applies
`schema.sql` to create the `users`, `media`, and `token_blocklist`
tables. It's safe to run again later — it never drops or truncates
existing tables or data.

You can point it at a different location if needed:

```bash
python ini.py --db-path data/app.db --schema schema.sql
```

## 4. Install and start MinIO (no Docker)

Download the native MinIO server binary for your platform from
https://min.io/download (or via your package manager), then run it
directly against the project's data directory:

```bash
# Linux example
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server ./data/minio --console-address ":9001"
```

* MinIO API: `http://localhost:9000`
* MinIO Console (web UI): `http://localhost:9001`
* Default console credentials: `minioadmin` / `minioadmin` (matches
  `.env.example` — change both if this ever leaves your machine)

Leave this running in its own terminal.

## 5. Create the MinIO bucket

The Flask app tries to create the `photos` bucket automatically on
startup if it doesn't exist (see `app/services/minio_service.py`). If
you'd rather do it explicitly:

```bash
# using the MinIO Client (mc)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/photos
```

Or just open the console at `http://localhost:9001` and create a
bucket named `photos` there.

## 6. Start Flask

In a second terminal, with the virtualenv activated:

```bash
cd backend
python run.py
```

Flask listens on `http://localhost:5000` by default. Check it's alive:

```bash
curl http://localhost:5000/health
# {"status": "ok"}
```

If MinIO isn't running yet, Flask still starts (it logs a warning);
upload requests will return a `STORAGE_UNAVAILABLE` (503) error until
MinIO is reachable.

## 7. Create an account and try the API

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"password123"}'

curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"password123"}'
# copy the access_token from the response

curl -H "Authorization: Bearer TOKEN" \
  -F "file=@/path/to/photo.jpg" \
  http://localhost:5000/api/media/upload

curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/media
```

See `API.md` for the full endpoint reference.

## 8. Configuring a mobile client

Whatever client connects to this backend just needs:

* The base URL, e.g. `http://<your-machine-ip>:5000` (not `localhost`,
  if the client is a phone on the same network).
* To call `/api/auth/register` and `/api/auth/login`, store the
  returned `access_token`, and send it as `Authorization: Bearer
  <token>` on every `/api/media/*` request.
* To upload files as `multipart/form-data` to `/api/media/upload`
  with the file in a field named `file`.

The API never expects or accepts a `user_id` from the client — it's
always derived from the JWT.

## 9. Inspecting SQLite

The database is a plain file at `data/app.db`. Inspect it with the
`sqlite3` CLI or any SQLite GUI:

```bash
sqlite3 data/app.db
sqlite> .tables
sqlite> SELECT id, email, created_at FROM users;
sqlite> SELECT id, user_id, filename, size, uploaded_at FROM media ORDER BY id DESC LIMIT 10;
```

## 10. Accessing the MinIO console

Open `http://localhost:9001` in a browser and log in with the
`MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` from your `.env` (defaults:
`minioadmin` / `minioadmin`). You'll see the `photos` bucket with
objects laid out as:

```
photos/
  <user_id>/
    <year>/
      <month>/
        <media_id>_<filename>
  thumbnails/
    <user_id>/<year>/<month>/<media_id>_<filename>.thumb.jpg
```

## Running tests

The test suite monkeypatches the MinIO calls, so it runs without a
real MinIO server:

```bash
cd backend
pytest
```

## Security notes (prototype scope)

* Passwords are hashed with PBKDF2 (Werkzeug's `generate_password_hash`),
  never stored in plaintext.
* Every `/api/media/*` route requires a valid JWT; the user ID is
  always read from the token, never trusted from client input.
* A user can never fetch, download, or delete another user's media —
  cross-user requests return the same `MEDIA_NOT_FOUND` as a genuinely
  missing ID, so ownership can't be probed.
* MinIO credentials live only in `.env` / Flask config; the mobile
  client never talks to MinIO directly, only to Flask.
* Uploads are validated by both file extension and MIME type, and are
  capped by `MAX_CONTENT_LENGTH_MB`.
* Logout is a real server-side token revocation (a `token_blocklist`
  table), not just "the client forgets the token."

## What's intentionally NOT here yet

Per the prototype scope: no albums, sharing, face/AI recognition, OCR,
video transcoding, signed MinIO URLs, Postgres/Redis, or Kubernetes.
The goal of this slice is a solid `Flask ⇄ MinIO ⇄ SQLite` core that a
mobile client can be built against next.
