# PIVA - Personal Image & Video Archive

A cross-platform photo and video management application with a Flutter frontend and Flask backend. Store, organize, and manage your media with cloud-like features including albums, soft delete (trash), and efficient thumbnail generation.

## Features

### Core Capabilities
- **User Authentication**: JWT-based secure authentication with access/refresh token pattern
- **Media Management**: Upload and organize photos and videos
- **Albums**: Create, organize, and manage collections of media
- **Smart Storage**: Track storage usage with per-user quota management
- **Trash/Soft Delete**: Recover deleted items with Google Photos-like trash functionality
- **Favorites**: Mark and filter favorite media
- **Thumbnails**: Automatic thumbnail generation for all images

### Media Support
- **Images**: JPG, JPEG, PNG, HEIC, WebP, GIF, BMP
- **Videos**: MP4, MOV, AVI, MKV, 3GP, WebM
- **Metadata**: Extract EXIF data (capture time, dimensions)
- **Deduplication**: SHA256 checksums prevent duplicate uploads

### Cross-Platform
- iOS (native Swift)
- Android (Gradle)
- macOS (native Swift)
- Linux (GTK)
- Windows (Win32)
- Web (Responsive)

## Architecture

### Backend (`/backend`)
Flask REST API with SQLAlchemy ORM
- `app.py` - Application factory and route registration
- `config.py` - Configuration and environment settings
- `models.py` - Database models (User, Media, Album, AlbumMedia)
- `extensions.py` - Flask extensions (SQLAlchemy, JWT)
- `utils.py` - Utilities (hashing, thumbnail generation, metadata extraction)
- `routes/` - API endpoints (auth, media, albums, sync)

### Frontend (`/lib`)
Flutter application with platform-specific implementations

### Platform Implementations
- `ios/`, `macos/` - Native iOS/macOS code (Swift)
- `android/` - Android native code (Kotlin/Java)
- `linux/`, `windows/` - Desktop implementations
- `web/` - Web platform

## Setup

### Backend Setup

1. **Requirements**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment Variables** (optional, uses defaults)
   ```bash
   export SECRET_KEY="your-secret-key"
   export JWT_SECRET_KEY="your-jwt-secret"
   export DATABASE_URL="sqlite:///database.db"  # or PostgreSQL URL
   ```

3. **Run Development Server**
   ```bash
   python app.py
   ```
   Server runs on `http://localhost:5009`

4. **Production Deployment**
   - Use gunicorn/uwsgi behind nginx
   - Set proper environment variables for secrets
   - Use PostgreSQL instead of SQLite
   - Configure CORS appropriately
   - See `backend/README.md` for details

### Frontend Setup

1. **Requirements**
   - Flutter SDK 3.0+
   - For native builds: Xcode (iOS/macOS), Android Studio (Android)

2. **Get Dependencies**
   ```bash
   flutter pub get
   ```

3. **Run Development**
   ```bash
   flutter run
   ```

4. **Build for Platforms**
   ```bash
   flutter build ios
   flutter build android
   flutter build windows
   flutter build linux
   flutter build macos
   flutter build web
   ```

## API Overview

### Authentication
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Login (returns access & refresh tokens)
- `POST /auth/refresh` - Refresh expired access token

### Media
- `GET /media` - List user's media
- `POST /media/upload` - Upload new photo/video
- `GET /media/<id>/file` - Download original file
- `GET /media/<id>/thumbnail` - Download thumbnail
- `PATCH /media/<id>` - Update media properties (favorite, trash)
- `DELETE /media/<id>` - Permanently delete media

### Albums
- `GET /albums` - List user's albums
- `POST /albums` - Create album
- `PATCH /albums/<id>` - Update album
- `DELETE /albums/<id>` - Delete album
- `POST /albums/<id>/items` - Add media to album
- `DELETE /albums/<id>/items/<media_id>` - Remove media from album

### Storage & Sync
- `GET /storage` - Get storage usage and quota
- `GET /sync` - Sync changes since last cursor (incremental sync)
- `GET /health` - Health check

## Database Models

### User
- Username, email, password (hashed)
- Storage quota (default 15GB)
- Relationship to media and albums

### Media
- Filename, original filename, mime type
- Media type (photo/video), dimensions, duration
- Checksums for deduplication
- EXIF timestamp extraction
- Soft-delete with trash timestamps
- Favorite flag

### Album
- User-owned collections
- Cover image reference
- Soft-delete support

### AlbumMedia
- Join table connecting media to albums

## Configuration

Key settings in `backend/config.py`:
- `MAX_CONTENT_LENGTH` - Maximum upload size (default 500MB)
- `JWT_ACCESS_TOKEN_EXPIRES` - Access token lifetime (default 1 hour)
- `JWT_REFRESH_TOKEN_EXPIRES` - Refresh token lifetime (default 90 days)
- `THUMBNAIL_SIZE` - Thumbnail dimensions (default 512×512)
- `DEFAULT_QUOTA_BYTES` - Default storage quota per user (default 15GB)

## File Organization

```
PIVA/
├── backend/              # Flask API
│   ├── routes/           # API blueprints
│   ├── models.py         # Database models
│   ├── config.py         # Configuration
│   ├── app.py            # Application entry point
│   └── requirements.txt   # Python dependencies
├── lib/                  # Flutter source code
├── android/              # Android native code
├── ios/                  # iOS native code
├── macos/                # macOS native code
├── linux/                # Linux implementation
├── windows/              # Windows implementation
├── web/                  # Web implementation
├── pubspec.yaml          # Flutter dependencies
└── README.md             # This file
```

## Security Notes

⚠️ **Development Only**: Default settings are NOT production-ready
- Change `SECRET_KEY` and `JWT_SECRET_KEY` in production
- Use HTTPS in production
- Configure CORS appropriately
- Use PostgreSQL instead of SQLite
- Run behind reverse proxy (nginx/Apache)
- Set secure cookie flags
- Implement rate limiting

## Troubleshooting

### Backend Issues
- Database errors: Check `DATABASE_URL` and ensure PostgreSQL is running
- Upload fails: Verify `UPLOAD_FOLDER` exists and has write permissions
- JWT errors: Ensure tokens haven't expired and client sends Authorization header

### Frontend Issues
- Connection refused: Ensure backend is running on `localhost:5009`
- Platform-specific builds: See Flutter documentation for platform requirements
- iOS builds: May require Cocoapods update (`cd ios && pod repo update`)

## Development

- Backend uses Flask with SQLAlchemy ORM
- Frontend uses Flutter with multi-platform support
- API follows REST conventions with JSON payloads
- Soft-delete pattern preserves data history for sync

## License

[Add license information]

## Contributing

[Add contribution guidelines]
