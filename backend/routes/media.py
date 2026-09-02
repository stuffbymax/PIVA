import os
import time
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import Media, User, AlbumMedia
from utils import (
    sha256_of_file, classify_media, unique_storage_name,
    extract_image_metadata, generate_image_thumbnail
)

bp = Blueprint("media", __name__, url_prefix="/media")


def _uid():
    return int(get_jwt_identity())


# ---------------------------------------------------------------- upload --
@bp.route("/upload", methods=["POST"])
@jwt_required()
def upload():
    """
    Upload a single photo/video.

    Dedup: if this user already uploaded a file with the same content
    (checksum), we don't store it twice -- we just return the existing
    record. This is exactly how Google Photos backup avoids re-uploading
    the same photo after a phone restore or app reinstall.
    """
    user = User.query.get_or_404(_uid())
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify(error="No file provided."), 400

    checksum = sha256_of_file(file)

    existing = Media.query.filter_by(user_id=user.id, checksum=checksum, is_deleted=False).first()
    if existing:
        return jsonify(media=existing.to_dict(request.host_url.rstrip("/")), deduplicated=True), 200

    original_filename = secure_filename(file.filename)
    media_type, ext = classify_media(original_filename, file.mimetype)
    if media_type is None:
        return jsonify(error="Unsupported file type."), 415

    # Quota check happens before we touch disk.
    file.stream.seek(0, os.SEEK_END)
    incoming_size = file.stream.tell()
    file.stream.seek(0)
    if user.storage_used() + incoming_size > user.quota_bytes:
        return jsonify(error="Storage quota exceeded."), 413

    stored_name = unique_storage_name(ext)
    dest_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    file.save(dest_path)
    actual_size = os.path.getsize(dest_path)

    width = height = None
    taken_at = None
    thumb_name = None

    if media_type == "photo":
        width, height, taken_at = extract_image_metadata(dest_path)
        stem = os.path.splitext(stored_name)[0]
        thumb_name = f"thumb_{stem}.jpg"
        thumb_path = os.path.join(current_app.config["THUMBNAIL_FOLDER"], thumb_name)
        if not generate_image_thumbnail(dest_path, thumb_path, current_app.config["THUMBNAIL_SIZE"]):
            thumb_name = None
    # Video thumbnailing needs ffmpeg, which isn't wired up here -- see
    # README "Extending this backend" for where to hook it in.

    client_taken_at = request.form.get("taken_at", type=float)
    if client_taken_at:
        taken_at = client_taken_at

    media = Media(
        user_id=user.id,
        filename=stored_name,
        original_filename=original_filename,
        thumbnail_filename=thumb_name,
        media_type=media_type,
        mime_type=file.mimetype or "application/octet-stream",
        file_size=actual_size,
        width=width,
        height=height,
        checksum=checksum,
        taken_at=taken_at,
    )
    db.session.add(media)
    db.session.commit()

    return jsonify(media=media.to_dict(request.host_url.rstrip("/")), deduplicated=False), 201


@bp.route("/check", methods=["POST"])
@jwt_required()
def check_existing():
    """
    Given a list of checksums, tell the client which ones already exist
    on the server. Flutter calls this before uploading a whole camera
    roll so it only sends bytes for photos that are actually new.
    Body: {"checksums": ["abc...", "def..."]}
    """
    data = request.get_json(silent=True) or {}
    checksums = data.get("checksums") or []
    if not isinstance(checksums, list):
        return jsonify(error="checksums must be a list."), 400

    rows = Media.query.filter(
        Media.user_id == _uid(),
        Media.checksum.in_(checksums),
        Media.is_deleted.is_(False),
    ).all()
    found = {r.checksum: r.id for r in rows}
    return jsonify(existing=found), 200


# ------------------------------------------------------------------ list --
@bp.route("", methods=["GET"])
@jwt_required()
def list_media():
    """Paginated feed for the main grid. Use /sync for incremental updates
    instead of re-paging this on every app open."""
    trashed = request.args.get("trashed", "false").lower() == "true"
    favorites_only = request.args.get("favorites", "false").lower() == "true"
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 60, type=int), 200)

    q = Media.query.filter_by(user_id=_uid(), is_deleted=False, is_trashed=trashed)
    if favorites_only:
        q = q.filter_by(is_favorite=True)
    q = q.order_by(Media.taken_at.desc().nullslast(), Media.created_at.desc())

    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    host = request.host_url.rstrip("/")
    return jsonify(
        items=[m.to_dict(host) for m in pagination.items],
        page=page,
        per_page=per_page,
        total=pagination.total,
        has_next=pagination.has_next,
    ), 200


# -------------------------------------------------------------- get one --
@bp.route("/<int:media_id>", methods=["GET"])
@jwt_required()
def get_media(media_id):
    m = Media.query.filter_by(id=media_id, user_id=_uid(), is_deleted=False).first_or_404()
    return jsonify(media=m.to_dict(request.host_url.rstrip("/"))), 200


@bp.route("/<int:media_id>/file", methods=["GET"])
@jwt_required()
def get_file(media_id):
    m = Media.query.filter_by(id=media_id, user_id=_uid(), is_deleted=False).first_or_404()
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], m.filename,
                                as_attachment=False, download_name=m.original_filename)


@bp.route("/<int:media_id>/thumbnail", methods=["GET"])
@jwt_required()
def get_thumbnail(media_id):
    m = Media.query.filter_by(id=media_id, user_id=_uid(), is_deleted=False).first_or_404()
    if not m.thumbnail_filename:
        return jsonify(error="No thumbnail available."), 404
    return send_from_directory(current_app.config["THUMBNAIL_FOLDER"], m.thumbnail_filename)


# ------------------------------------------------------------- favorite --
@bp.route("/<int:media_id>/favorite", methods=["POST"])
@jwt_required()
def toggle_favorite(media_id):
    m = Media.query.filter_by(id=media_id, user_id=_uid(), is_deleted=False).first_or_404()
    body = request.get_json(silent=True) or {}
    m.is_favorite = bool(body["favorite"]) if "favorite" in body else (not m.is_favorite)
    m.touch()
    db.session.commit()
    return jsonify(media=m.to_dict(request.host_url.rstrip("/"))), 200


# ------------------------------------------------------ trash / delete --
@bp.route("/<int:media_id>", methods=["DELETE"])
@jwt_required()
def trash_media(media_id):
    """Soft-delete: moves to Trash, like pressing Delete in Google Photos.
    Use /media/<id>/permanent to actually free the storage."""
    m = Media.query.filter_by(id=media_id, user_id=_uid(), is_deleted=False).first_or_404()
    m.is_trashed = True
    m.trashed_at = time.time()
    m.touch()
    db.session.commit()
    return jsonify(media=m.to_dict(request.host_url.rstrip("/"))), 200


@bp.route("/<int:media_id>/restore", methods=["POST"])
@jwt_required()
def restore_media(media_id):
    m = Media.query.filter_by(id=media_id, user_id=_uid(), is_deleted=False).first_or_404()
    m.is_trashed = False
    m.trashed_at = None
    m.touch()
    db.session.commit()
    return jsonify(media=m.to_dict(request.host_url.rstrip("/"))), 200


@bp.route("/<int:media_id>/permanent", methods=["DELETE"])
@jwt_required()
def permanent_delete(media_id):
    """Actually removes the file bytes. The DB row is kept as a tombstone
    (is_deleted=True) so that /sync can tell other devices this id is gone
    instead of them just never hearing about it again."""
    m = Media.query.filter_by(id=media_id, user_id=_uid(), is_deleted=False).first_or_404()
    _remove_files(m)
    AlbumMedia.query.filter_by(media_id=m.id).delete()
    m.is_deleted = True
    m.filename = ""
    m.thumbnail_filename = None
    m.touch()
    db.session.commit()
    return jsonify(deleted=True, id=m.id), 200


@bp.route("/trash/empty", methods=["POST"])
@jwt_required()
def empty_trash():
    """Permanently deletes everything currently in the trash."""
    items = Media.query.filter_by(user_id=_uid(), is_trashed=True, is_deleted=False).all()
    for m in items:
        _remove_files(m)
        AlbumMedia.query.filter_by(media_id=m.id).delete()
        m.is_deleted = True
        m.filename = ""
        m.thumbnail_filename = None
        m.touch()
    db.session.commit()
    return jsonify(deleted_count=len(items)), 200


def _remove_files(media):
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    thumb_dir = current_app.config["THUMBNAIL_FOLDER"]
    if media.filename:
        try:
            os.remove(os.path.join(upload_dir, media.filename))
        except OSError:
            pass
    if media.thumbnail_filename:
        try:
            os.remove(os.path.join(thumb_dir, media.thumbnail_filename))
        except OSError:
            pass
