"""
Thin wrapper around the MinIO Python SDK.

The Flask API is the only thing that talks to MinIO directly - the
Flutter client never gets MinIO credentials or a direct connection.
All reads/writes go through this service and are exposed to clients
via Flask routes (app/routes/media.py).
"""

import io
from datetime import datetime, timezone

import urllib3
from minio import Minio
from minio.error import S3Error

from app.utils.errors import APIError

# A short, low-retry HTTP pool so that if MinIO isn't running yet
# (e.g. during local dev before `minio server` has been started),
# Flask still boots quickly instead of hanging for tens of seconds
# retrying the startup bucket-check.
_FAST_FAIL_HTTP_CLIENT = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=2, read=5),
    retries=urllib3.Retry(total=1, backoff_factor=0.1),
)

_client = None
_bucket_name = None


def init_minio(app) -> None:
    """Called once from create_app() to set up the shared MinIO client
    and make sure the configured bucket exists."""
    global _client, _bucket_name

    _bucket_name = app.config["MINIO_BUCKET"]

    # Use the fast-fail client just for the startup existence check so
    # a down MinIO doesn't block app boot; normal request-time clients
    # get standard (more resilient) retry behavior.
    startup_client = Minio(
        app.config["MINIO_ENDPOINT"],
        access_key=app.config["MINIO_ACCESS_KEY"],
        secret_key=app.config["MINIO_SECRET_KEY"],
        secure=app.config["MINIO_SECURE"],
        http_client=_FAST_FAIL_HTTP_CLIENT,
    )

    _client = Minio(
        app.config["MINIO_ENDPOINT"],
        access_key=app.config["MINIO_ACCESS_KEY"],
        secret_key=app.config["MINIO_SECRET_KEY"],
        secure=app.config["MINIO_SECURE"],
    )

    try:
        if not startup_client.bucket_exists(_bucket_name):
            startup_client.make_bucket(_bucket_name)
            app.logger.info(f"Created MinIO bucket '{_bucket_name}'")
    except Exception as e:
        # Don't crash app startup if MinIO isn't up yet (e.g. in dev
        # before `minio server` has been started, or in tests where
        # MinIO calls are monkeypatched); upload calls will raise a
        # clear STORAGE_UNAVAILABLE error instead if it's really down.
        app.logger.warning(f"Could not verify/create MinIO bucket at startup: {e}")


def _get_client() -> Minio:
    if _client is None:
        raise APIError("STORAGE_NOT_CONFIGURED", "Storage backend is not initialized.", 500)
    return _client


def build_object_key(user_id: int, media_id: int, filename: str, when: datetime = None) -> str:
    when = when or datetime.now(timezone.utc)
    return f"{user_id}/{when.year:04d}/{when.month:02d}/{media_id}_{filename}"


def build_thumbnail_key(object_key: str) -> str:
    return f"thumbnails/{object_key}.thumb.jpg"


def upload_stream(object_key: str, data_stream, length: int, content_type: str) -> None:
    client = _get_client()
    try:
        client.put_object(
            _bucket_name, object_key, data_stream, length=length, content_type=content_type
        )
    except S3Error as e:
        raise APIError("STORAGE_UNAVAILABLE", f"Failed to store file in MinIO: {e}", 503)
    except Exception as e:
        # Covers connection-level failures (MinIO not running, network
        # issues, etc.) which surface as urllib3/requests exceptions
        # rather than S3Error.
        raise APIError("STORAGE_UNAVAILABLE", f"Could not reach storage backend: {e}", 503)


def upload_bytes(object_key: str, data: bytes, content_type: str) -> None:
    upload_stream(object_key, io.BytesIO(data), len(data), content_type)


def get_object_stream(object_key: str):
    client = _get_client()
    try:
        return client.get_object(_bucket_name, object_key)
    except S3Error as e:
        raise APIError("STORAGE_OBJECT_NOT_FOUND", f"Object not found in storage: {e}", 404)
    except Exception as e:
        raise APIError("STORAGE_UNAVAILABLE", f"Could not reach storage backend: {e}", 503)


def delete_object(object_key: str) -> None:
    if not object_key:
        return
    client = _get_client()
    try:
        client.remove_object(_bucket_name, object_key)
    except S3Error as e:
        # Non-fatal: log-worthy but shouldn't block, e.g., a delete-media
        # request when the object was already gone.
        raise APIError("STORAGE_UNAVAILABLE", f"Failed to delete object from MinIO: {e}", 503)
    except Exception as e:
        raise APIError("STORAGE_UNAVAILABLE", f"Could not reach storage backend: {e}", 503)
