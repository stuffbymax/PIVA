from flask import Blueprint, jsonify, request, current_app, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import media_service, minio_service
from app.utils.errors import APIError

bp = Blueprint("media", __name__, url_prefix="/api/media")


def _current_user_id() -> int:
    # The user id is ALWAYS derived from the verified JWT, never from
    # any value the client might send in the request body/query string.
    return int(get_jwt_identity())


@bp.post("/upload")
@jwt_required()
def upload():
    user_id = _current_user_id()

    if "file" not in request.files:
        raise APIError("INVALID_FILE", "No file field found in multipart form data (expected 'file').", 400)

    file_storage = request.files["file"]

    def _float_or_none(val):
        try:
            return float(val) if val not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def _int_or_none(val):
        try:
            return int(val) if val not in (None, "") else None
        except (TypeError, ValueError):
            return None

    width = _int_or_none(request.form.get("width"))
    height = _int_or_none(request.form.get("height"))
    duration = _float_or_none(request.form.get("duration"))

    media = media_service.upload_media(
        user_id=user_id,
        file_storage=file_storage,
        width=width,
        height=height,
        duration=duration,
    )

    return jsonify({
        "id": media.id,
        "filename": media.filename,
        "status": "uploaded",
        "media": media.to_dict(),
    }), 201


@bp.get("")
@bp.get("/")
@jwt_required()
def list_media():
    user_id = _current_user_id()

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", current_app.config["DEFAULT_PAGE_SIZE"]))
    except ValueError:
        raise APIError("INVALID_QUERY_PARAM", "page and limit must be integers.", 400)

    items, total, page, limit = media_service.list_media(user_id, page, limit)

    return jsonify({
        "items": [m.to_dict() for m in items],
        "page": page,
        "limit": limit,
        "total": total,
    }), 200


@bp.get("/<int:media_id>")
@jwt_required()
def get_media(media_id: int):
    user_id = _current_user_id()
    media = media_service.get_media_or_404(user_id, media_id)
    return jsonify(media.to_dict()), 200


@bp.get("/<int:media_id>/download")
@jwt_required()
def download_media(media_id: int):
    user_id = _current_user_id()
    media = media_service.get_media_or_404(user_id, media_id)

    obj = minio_service.get_object_stream(media.object_key)

    def generate():
        try:
            for chunk in obj.stream(32 * 1024):
                yield chunk
        finally:
            obj.close()
            obj.release_conn()

    headers = {
        "Content-Disposition": f'attachment; filename="{media.filename}"',
        "Content-Length": str(media.size),
    }
    return Response(stream_with_context(generate()), mimetype=media.mime_type, headers=headers)


@bp.get("/<int:media_id>/thumbnail")
@jwt_required()
def get_thumbnail(media_id: int):
    user_id = _current_user_id()
    media = media_service.get_media_or_404(user_id, media_id)

    if not media.thumbnail_key:
        raise APIError("THUMBNAIL_NOT_AVAILABLE", "No thumbnail is available for this media item.", 404)

    obj = minio_service.get_object_stream(media.thumbnail_key)

    def generate():
        try:
            for chunk in obj.stream(32 * 1024):
                yield chunk
        finally:
            obj.close()
            obj.release_conn()

    return Response(stream_with_context(generate()), mimetype="image/jpeg")


@bp.delete("/<int:media_id>")
@jwt_required()
def delete_media(media_id: int):
    user_id = _current_user_id()
    media_service.delete_media(user_id, media_id)
    return jsonify({"message": "Media deleted."}), 200
