import os
import json
import secrets
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRETS_PATH = os.path.join(BASE_DIR, "data", "secrets.json")


def _load_or_create_secrets():
    os.makedirs(os.path.dirname(SECRETS_PATH), exist_ok=True)
    try:
        with open(SECRETS_PATH, "r", encoding="utf-8") as handle:
            values = json.load(handle)
        if values.get("SECRET_KEY") and values.get("JWT_SECRET_KEY"):
            return values
    except (OSError, ValueError):
        pass
    values = {
        "SECRET_KEY": secrets.token_urlsafe(32),
        "JWT_SECRET_KEY": secrets.token_urlsafe(32),
    }
    with open(SECRETS_PATH, "w", encoding="utf-8") as handle:
        json.dump(values, handle, indent=2)
    try:
        os.chmod(SECRETS_PATH, 0o600)
    except OSError:
        pass
    return values


_generated_secrets = _load_or_create_secrets()


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", _generated_secrets["SECRET_KEY"])
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", _generated_secrets["JWT_SECRET_KEY"])

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
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "heic", "webp", "gif", "bmp"}
    ALLOWED_VIDEO_EXT = {"mp4", "mov", "avi", "mkv", "3gp", "webm"}

    # Default storage quota per user, in bytes (15GB, same order of
    # magnitude as a free Google account). Override per-user in the DB.
    DEFAULT_QUOTA_BYTES = 15 * 1024 * 1024 * 1024

    THUMBNAIL_SIZE = (512, 512)
