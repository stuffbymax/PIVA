# Photo Backend (Google Photos–style API)

A Flask REST API backend for a photo-backup app, built for a Flutter
frontend. It supports image upload, delta sync, favorites, trash/restore,
permanent delete, albums, and protected administrator endpoints.

This is a from-scratch rewrite, not a patch of the PS3-sharing site you
shared. That app used server-rendered HTML pages and cookie sessions,
which don't make sense for a Flutter client — Flutter needs a JSON API
with token auth it can call from Dart, so that's what this is.

## Why it's structured this way

- **JWT auth, not sessions.** Mobile apps can't rely on cookies the way
  a browser does. Every request instead carries an `Authorization:
  Bearer <token>` header. A short-lived access token (1h) plus a
  long-lived refresh token (90d) means the user logs in once and the
  app quietly refreshes in the background after that.
- **Delta sync (`/sync`), not just a list endpoint.** Google Photos
  doesn't re-download your whole library every time you open the app —
  it asks "what changed since I last checked?" `/sync?since=<time>`
  does exactly that, returning only new/edited/deleted items. This is
  the piece that makes an offline-first Flutter app (using something
  like `sqflite` or `drift` locally) actually pleasant to build.
- **Soft delete -> Trash -> permanent delete**, matching the real
  Google Photos flow: deleting doesn't destroy anything immediately; it
  moves the item to Trash. A separate "permanent delete" (or emptying
  Trash) actually removes the file bytes and turns the DB row into a
  tombstone, so other devices find out via `/sync` that the item is
  really gone instead of just never hearing about it again.
- **Checksum-based dedup.** Every upload is SHA-256 hashed. Re-uploading
  the same photo (e.g. after a reinstall, or a flaky connection retrying)
  doesn't create a duplicate — the server just returns the existing
  record. `/media/check` lets the client batch-check checksums *before*
  uploading, so a camera-roll sync only sends bytes for photos that are
  genuinely new.

## Project layout

```
photobackend/
├── app.py              # app factory, blueprint registration, /health, /storage
├── config.py            # all settings in one place
├── extensions.py         # db, jwt singletons
├── models.py             # User, Media, Album, AlbumMedia
├── utils.py              # checksums, thumbnailing, EXIF extraction
├── routes/
│   ├── auth.py           # register/login/refresh/me
│   ├── media.py           # upload/list/download/thumbnail/favorite/trash/delete
│   ├── albums.py          # album CRUD + membership
│   └── sync.py            # delta sync
├── uploads/               # original files live here
├── thumbnails/            # generated JPEG thumbnails
├── requirements.txt
└── .env.example
```

## Setup

```bash
cd photobackend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit the two secret keys
python app.py           # dev server on http://0.0.0.0:5009
```

For production, don't use `app.run()` — run behind gunicorn/nginx:

```bash
gunicorn -w 4 -b 0.0.0.0:5009 app:app
```

and put nginx (or similar) in front for TLS and to serve large file
uploads efficiently. Also switch `DATABASE_URL` to Postgres for
anything beyond a single-user hobby deployment — SQLite's single-writer
lock will bottleneck concurrent uploads.

## API reference

All endpoints except `/auth/register` and `/auth/login` require:
`Authorization: Bearer <access_token>`

### Auth
| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/auth/register` | `username, password, email?` | Returns `access_token` + `refresh_token` |
| POST | `/auth/login` | `username, password` | Same as above |
| POST | `/auth/refresh` | — | Send the **refresh** token as Bearer; returns a new access token |
| GET | `/auth/me` | — | Current user + storage usage |

### Media
| Method | Path | Notes |
|---|---|---|
| POST | `/media/upload` | multipart `file`, optional `taken_at` (unix epoch). Dedupes by checksum. |
| POST | `/media/check` | body `{"checksums": [...]}` → which already exist, for pre-upload filtering |
| GET | `/media?page=&per_page=&trashed=&favorites=` | Paginated grid |
| GET | `/media/<id>` | Single item's metadata |
| GET | `/media/<id>/file` | Download/stream original bytes |
| GET | `/media/<id>/thumbnail` | JPEG thumbnail (photos only currently) |
| POST | `/media/<id>/favorite` | body `{"favorite": true}` or omit to toggle |
| DELETE | `/media/<id>` | Moves to Trash (soft delete) |
| POST | `/media/<id>/restore` | Restores from Trash |
| DELETE | `/media/<id>/permanent` | Frees storage, leaves a sync tombstone |
| POST | `/media/trash/empty` | Permanently deletes everything in Trash |

### Albums
| Method | Path | Notes |
|---|---|---|
| GET | `/albums` | List albums (no items) |
| POST | `/albums` | body `{"name": "..."}` |
| GET | `/albums/<id>` | Album + its items |
| PATCH | `/albums/<id>` | body `name?`, `cover_media_id?` |
| DELETE | `/albums/<id>` | Deletes the album, not the photos in it |
| POST | `/albums/<id>/items` | body `{"media_ids": [1,2,3]}` |
| DELETE | `/albums/<id>/items/<media_id>` | Remove one item from the album |

### Sync & misc
| Method | Path | Notes |
|---|---|---|
| GET | `/sync?since=<epoch>` | Delta sync — see below |
| GET | `/storage` | `used_bytes` / `quota_bytes` |
| GET | `/health` | Liveness check |

## Using `/sync` from Flutter

```
1. First launch: GET /sync?since=0
   -> store every item locally, remember `server_time` from the response.
2. Every subsequent sync: GET /sync?since=<last stored server_time>
   -> apply only the returned media/albums (upsert by id).
      If an item has "deleted": true, delete it locally instead.
   -> store the new `server_time`.
3. If the response has "more": true, immediately call /sync again with
   the same `since` (there were >1000 changes; it's paginated).
```

This is the same "sync token" pattern Google Drive/Photos, Dropbox, and
most offline-first apps use — you never have to diff the whole library,
just replay what changed.

## Suggested Flutter-side pieces

- `dio` or `http` for the API client; store tokens with
  `flutter_secure_storage`.
- `sqflite` or `drift` as the local cache that `/sync` writes into —
  your photo grid reads from this local DB, not the network, so it's
  instant and works offline.
- `workmanager` (Android) / `background_fetch` for periodic background
  camera-roll backup, calling `/media/check` first, then `/media/upload`
  only for what's missing — mirrors how the real Google Photos app
  backs up efficiently.
- `photo_manager` package to enumerate the device's camera roll.

## Administration

The first registered account becomes an administrator. Authenticated admins
can use `GET /admin/users`, `GET /admin/stats`, and `PATCH
/admin/users/<id>` with `quota_bytes` or `is_admin`. Non-admin users receive
403 responses. Backend signing keys are generated automatically and stored in
`backend/data/secrets.json`; this file is ignored by git. No dotenv package or
manual `.env` setup is required.

Uploads accept images and common video formats. Video thumbnails are not
generated, but videos can be opened and played from the detail viewer.

## Extending this backend

- **Face grouping / search**: out of scope here, but this is where
  you'd add a background job that runs a face-detection model on new
  uploads and stores embeddings for search.
- **Multi-device push**: pair `/sync` with a push notification (FCM) so
  other devices know to sync immediately rather than polling.
- **Rate limiting / abuse protection**: add `Flask-Limiter` before
  exposing this publicly.

## Security notes before you deploy this anywhere public

- Set real, random `SECRET_KEY` and `JWT_SECRET_KEY` values (the
  `.env.example` placeholders are not safe to use as-is).
- Put this behind HTTPS — bearer tokens over plain HTTP can be
  intercepted.
- The quota check in `/media/upload` is best-effort (checked before
  disk write, not atomic under heavy concurrency); fine for a personal
  or small-team deployment, worth hardening with a DB-level lock or
  advisory lock if you expect many simultaneous uploads per user.
