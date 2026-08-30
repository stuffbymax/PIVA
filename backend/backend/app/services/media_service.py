"""
Core media business logic: validating uploads, deduplicating by hash,
storing files in MinIO, generating thumbnails, and CRUD/listing backed
by SQLite via SQLAlchemy.
"""

from datetime import datetime, timezone

from flask import current_app

from app.extensions import db
from app.models.media import Media
from app.services import minio_service, thumbnail_service
from app.utils.errors import APIError
from app.utils.hashing import hash_file_stream, allowed_file, get_extension


def _validate_upload(file_storage) -> str:
    """Validate filename/extension/mimetype. Returns the resolved mime type."""
    filename = file_storage.filename
    if not filename:
        raise APIError("INVALID_FILE", "No filename provided.", 400)

    cfg = current_app.config
    ext = get_extension(filename)
    is_image_ext = ext in cfg["ALLOWED_IMAGE_EXTENSIONS"]
    is_video_ext = ext in cfg["ALLOWED_VIDEO_EXTENSIONS"]

    if not (is_image_ext or is_video_ext):
        raise APIError("UNSUPPORTED_FILE_TYPE", f"File extension '.{ext}' is not supported.", 415)

    mime_type = file_storage.mimetype or ""
    allowed_mimes = cfg["ALLOWED_IMAGE_MIME_TYPES"] | cfg["ALLOWED_VIDEO_MIME_TYPES"]
    if mime_type and mime_type not in allowed_mimes:
        raise APIError("UNSUPPORTED_FILE_TYPE", f"MIME type '{mime_type}' is not supported.", 415)

    if not mime_type:
        # Fall back to a best-guess mime from the extension so we always
        # store something sensible.
        mime_type = "image/jpeg" if is_image_ext else "video/mp4"

    return mime_type


def upload_media(user_id: int, file_storage, width=None, height=None, duration=None, modified_at=None) -> Media:
    mime_type = _validate_upload(file_storage)

    file_stream = file_storage.stream
    file_hash = hash_file_stream(file_stream)

    # Duplicate detection: same user + same content hash -> return existing.
    existing = Media.query.filter_by(user_id=user_id, file_hash=file_hash).first()
    if existing:
        return existing

    file_stream.seek(0, 2)  # seek to end
    size = file_stream.tell()
    file_stream.seek(0)

    if size <= 0:
        raise APIError("INVALID_FILE", "Uploaded file is empty.", 400)

    filename = file_storage.filename
    now = datetime.now(timezone.utc)

    # Insert a row first (without object_key) to obtain the auto-increment
    # media id, which is embedded in the MinIO object key.
    media = Media(
        user_id=user_id,
        filename=filename,
        object_key="",  # filled in below
        mime_type=mime_type,
        size=size,
        file_hash=file_hash,
        created_at=now,
        modified_at=modified_at,
        width=width,
        height=height,
        duration=duration,
        uploaded_at=now,
    )
    db.session.add(media)
    try:
        db.session.flush()  # assigns media.id without committing yet
    except Exception:
        db.session.rollback()
        # Most likely cause: a race on the (user_id, file_hash) unique
        # constraint from a concurrent duplicate upload.
        existing = Media.query.filter_by(user_id=user_id, file_hash=file_hash).first()
        if existing:
            return existing
        raise APIError("UPLOAD_FAILED", "Could not create media record.", 500)

    object_key = minio_service.build_object_key(user_id, media.id, filename, when=now)

    file_stream.seek(0)
    minio_service.upload_stream(object_key, file_stream, size, mime_type)

    thumbnail_key = None
    try:
        if mime_type.startswith("image/"):
            thumb_bytes = thumbnail_service.generate_image_thumbnail(file_stream)
        else:
            thumb_bytes = thumbnail_service.generate_video_placeholder_thumbnail()
        thumbnail_key = minio_service.build_thumbnail_key(object_key)
        minio_service.upload_bytes(thumbnail_key, thumb_bytes, "image/jpeg")
    except Exception:
        current_app.logger.warning(f"Thumbnail generation failed for media upload ({filename})", exc_info=True)
        thumbnail_key = None

    media.object_key = object_key
    media.thumbnail_key = thumbnail_key
    db.session.commit()

    return media


def list_media(user_id: int, page: int, limit: int):
    cfg = current_app.config
    page = max(page, 1)
    limit = max(1, min(limit, cfg["MAX_PAGE_SIZE"]))

    query = Media.query.filter_by(user_id=user_id).order_by(Media.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    return items, total, page, limit


def get_media_or_404(user_id: int, media_id: int) -> Media:
    media = db.session.get(Media, media_id)
    if not media:
        raise APIError("MEDIA_NOT_FOUND", "Media not found.", 404)
    if media.user_id != user_id:
        # Deliberately the same error as "not found" so we don't leak
        # the existence of other users' media ids.
        raise APIError("MEDIA_NOT_FOUND", "Media not found.", 404)
    return media


def delete_media(user_id: int, media_id: int) -> None:
    media = get_media_or_404(user_id, media_id)

    minio_service.delete_object(media.object_key)
    if media.thumbnail_key:
        try:
            minio_service.delete_object(media.thumbnail_key)
        except APIError:
            pass  # thumbnail cleanup is best-effort

    db.session.delete(media)
    db.session.commit()
