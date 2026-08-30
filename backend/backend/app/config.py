"""
Application configuration, populated from environment variables.

Nothing here is hard-coded: every secret / connection value comes from
the environment (typically loaded from a project-root .env file by
run.py via python-dotenv). Sensible local-development defaults are
provided so the prototype runs out of the box, but they should always
be overridden for anything beyond local development.
"""

import os

# Project root is two levels up from this file: backend/app/config.py -> project root
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- General ---
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"

    DATA_DIR = os.path.join(PROJECT_ROOT, os.environ.get("DATA_DIR", "data"))

    # --- Database ---
    # DATABASE_URL is expressed relative to the project root, e.g.
    # sqlite:///data/app.db
    _raw_database_url = os.environ.get("DATABASE_URL", "sqlite:///data/app.db")
    if _raw_database_url.startswith("sqlite:///") and not _raw_database_url.startswith("sqlite:////"):
        # Relative sqlite path -> make absolute against the project root so
        # the DB is found the same way regardless of the working directory
        # the Flask process was started from.
        _relative_path = _raw_database_url.replace("sqlite:///", "", 1)
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(PROJECT_ROOT, _relative_path)
    else:
        SQLALCHEMY_DATABASE_URI = _raw_database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth / JWT ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    JWT_TOKEN_LOCATION = ["headers"]

    # --- MinIO ---
    MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "photos")
    MINIO_SECURE = _env_bool("MINIO_SECURE", False)

    # --- Uploads ---
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "200")) * 1024 * 1024

    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "heic", "heif", "bmp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v", "3gp"}

    ALLOWED_IMAGE_MIME_TYPES = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "image/heic", "image/heif", "image/bmp",
    }
    ALLOWED_VIDEO_MIME_TYPES = {
        "video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska",
        "video/webm", "video/3gpp",
    }

    THUMBNAIL_MAX_SIZE = (512, 512)
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200
