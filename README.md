# PIVA

PIVA is a full-stack photo backup and gallery app built around a Flutter mobile client and a Flask JSON API. The app is designed to feel like a lightweight Google Photos clone: account login, media upload, full-image viewing, favorites, trash management, albums, and admin tools.

## Overview

This repository contains both halves of the project:

- Flutter app in the root: a mobile-first client that handles auth, uploads, browsing, and album actions.
- Python backend in `backend/`: a Flask REST API that stores media, manages users, and serves thumbnails and download endpoints.

The app is intended for local/self-hosted usage and focuses on a simple, understandable architecture rather than enterprise complexity.

## Features

- User registration and login
- JWT-based authentication with refresh flow
- Photo and video upload from gallery or camera
- Paginated media browsing
- Favorite toggling
- Soft delete / trash restore / permanent delete
- Album creation and media assignment
- Admin dashboard for user and storage stats
- Delta sync-ready backend for offline-first syncing
- Secure token storage on-device

## Project structure

```text
PIVA/
├── android/                # Android project files
├── ios/                    # iOS project files
├── linux/                  # Linux build files
├── macos/                  # macOS build files
├── windows/                # Windows build files
├── lib/                    # Flutter app source
│   ├── main.dart
│   ├── models/
│   ├── providers/
│   ├── screens/
│   ├── services/
│   └── widgets/
├── backend/                # Flask API server
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── utils.py
│   ├── routes/
│   ├── uploads/
│   ├── thumbnails/
│   ├── data/
│   ├── requirements.txt
│   ├── README.md
│   └── .env.example
├── analysis_options.yaml
├── pubspec.yaml
├── README.md
├── android_manifest_permissions.xml
├── ios_info_plist_permissions.xml
└── .gitignore
```

## Stack

- Frontend: Flutter + Dart
- State management: Provider
- Networking: HTTP client with secure token storage
- Backend: Flask + SQLAlchemy
- Auth: JWT access/refresh tokens
- Storage: local filesystem for uploads and thumbnails
- Database: SQLite by default

## Requirements

### Backend

- Python 3.11+
- pip

### Frontend

- Flutter SDK 3.3+
- Android Studio / Xcode for device builds if you want native apps
- A device or emulator connected to the same local network

## Quick start

### 1) Start the backend

From the project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The backend runs by default on:

```text
http://0.0.0.0:5009
```

HTTP is enabled for local development. Android is configured to allow
cleartext HTTP, and iOS allows it through the development ATS setting. Do
not expose this setup to the internet: bearer tokens and uploaded media
should use HTTPS in production.

To store originals and generated thumbnails somewhere else, set these
environment variables before starting the backend:

```powershell
$env:PIVA_IMAGE_FOLDER = 'D:\PIVA\images'
$env:PIVA_VIDEO_FOLDER = 'D:\PIVA\videos'
$env:PIVA_THUMBNAIL_FOLDER = 'D:\PIVA\thumbnails'
python app.py
```

The backend creates all directories automatically. `PIVA_UPLOAD_FOLDER` can
still be used as one shared fallback for both media types. These are server-side
paths; the Flutter app cannot browse arbitrary folders on a phone. Uploads
from the gallery or camera are copied into the configured server storage.

If you want to inspect the backend API in more detail, see [backend/README.md](backend/README.md).

### 2) Start the Flutter app

From the project root:

```bash
flutter pub get
flutter run
```

On first launch, the app prompts for the backend URL. Use a value such as:

- Android emulator: `http://10.0.2.2:5009`
- Local phone on the same LAN: `http://192.168.1.x:5009`
- Deployed server: `https://your-domain.example`

## Backend behavior and configuration

The Flask app auto-generates secret keys and stores them in:

```text
backend/data/secrets.json
```

The file is created automatically if it does not exist. The app also uses SQLite by default via the `DATABASE_URL` setting in `backend/config.py`, which can be overridden with an environment variable if needed.

The backend supports:

- device-safe JWT auth
- media upload and download routes
- deduplication by checksum
- media listing with pagination
- favorites and trash lifecycle
- album management
- admin API endpoints
- sync-style endpoints ready for offline-first rebuilds

## App flow

Typical usage looks like this:

1. Open the app and set the backend URL.
2. Register or log in.
3. Upload photos or videos.
4. Browse the photo library and open media details.
5. Favorite, trash, restore, or permanently delete items.
6. Create albums and assign media to them.
7. Use the admin screen if your account has admin privileges.

Video uploads receive a JPEG cover frame generated from the video with
`imageio-ffmpeg`, just like photos receive thumbnails. The grid, albums, and
detail screen use that cover image; opening the item plays the original video.

## Development notes

- The app uses `Provider` rather than a heavier state management stack to keep the code approachable.
- Storage and auth tokens are kept in secure storage on the device.
- The backend is intentionally simple and self-contained, which makes it easier to run locally and debug.
- The API is already structured for a future offline sync layer based on `/sync` semantics.

## Security notes

- Do not expose the app over plain HTTP in production without TLS.
- Keep secret keys private and never commit generated secrets to version control.
- For real deployments, consider moving from SQLite to Postgres and adding stronger production hardening.

## Common troubleshooting

### Backend not reachable from phone emulator

Use the correct host address:

- Android emulator: `10.0.2.2`
- iOS simulator: `localhost` or the machine's LAN IP
- Physical device: the computer's LAN IP, not `127.0.0.1`

### CORS issues in web builds

If you run the Flutter app in browser mode, enable CORS in the Flask backend before testing.

### Uploads fail

Check the backend server is running, the media file type is allowed, and your app is pointing to the correct URL.

## License

This project is currently unlicensed unless you add a license file for your own distribution or deployment needs.

## Next ideas

- Add local database caching and offline delta sync
- Add automatic camera-roll backup for new media
- Add thumbnail generation improvements and better video support
- Add stronger admin and quota controls
