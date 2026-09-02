import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-too")

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- JWT ---
    # Short-lived access token + long-lived refresh token is the standard
    # pattern for mobile apps: the phone silently refreshes instead of
    # forcing the user to log in again every time the token expires.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=90)

    # --- Storage ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    THUMBNAIL_FOLDER = os.path.join(BASE_DIR, "thumbnails")
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB per upload (raise for 4K video)

    ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "heic", "webp", "gif", "bmp"}
    ALLOWED_VIDEO_EXT = {"mp4", "mov", "avi", "mkv", "3gp", "webm"}

    # Default storage quota per user, in bytes (15GB, same order of
    # magnitude as a free Google account). Override per-user in the DB.
    DEFAULT_QUOTA_BYTES = 15 * 1024 * 1024 * 1024

    THUMBNAIL_SIZE = (512, 512)
