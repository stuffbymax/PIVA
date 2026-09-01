from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Album, AlbumMedia, Media

bp = Blueprint("albums", __name__, url_prefix="/albums")


def _uid():
    return int(get_jwt_identity())


@bp.route("", methods=["GET"])
@jwt_required()
def list_albums():
    albums = Album.query.filter_by(user_id=_uid(), is_deleted=False).order_by(Album.updated_at.desc()).all()
    return jsonify(albums=[a.to_dict() for a in albums]), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_album():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(error="Album name is required."), 400
    album = Album(user_id=_uid(), name=name)
    db.session.add(album)
    db.session.commit()
    return jsonify(album=album.to_dict()), 201


@bp.route("/<int:album_id>", methods=["GET"])
@jwt_required()
def get_album(album_id):
    album = Album.query.filter_by(id=album_id, user_id=_uid(), is_deleted=False).first_or_404()
    host = request.host_url.rstrip("/")
    items = (
        Media.query.join(AlbumMedia, AlbumMedia.media_id == Media.id)
        .filter(AlbumMedia.album_id == album.id, Media.is_deleted.is_(False))
        .order_by(Media.taken_at.desc().nullslast())
        .all()
    )
    result = album.to_dict()
    result["items"] = [m.to_dict(host) for m in items]
    return jsonify(album=result), 200


@bp.route("/<int:album_id>", methods=["PATCH"])
@jwt_required()
def rename_album(album_id):
    album = Album.query.filter_by(id=album_id, user_id=_uid(), is_deleted=False).first_or_404()
    data = request.get_json(silent=True) or {}
    if "name" in data and data["name"].strip():
        album.name = data["name"].strip()
    if "cover_media_id" in data:
        album.cover_media_id = data["cover_media_id"]
    db.session.commit()  # updated_at auto-bumps via the column's onupdate
    return jsonify(album=album.to_dict()), 200


@bp.route("/<int:album_id>", methods=["DELETE"])
@jwt_required()
def delete_album(album_id):
    """Deletes the album itself. The media inside it are untouched --
    exactly like deleting an album in Google Photos doesn't delete photos."""
    album = Album.query.filter_by(id=album_id, user_id=_uid(), is_deleted=False).first_or_404()
    AlbumMedia.query.filter_by(album_id=album.id).delete()
    album.is_deleted = True
    db.session.commit()
    return jsonify(deleted=True, id=album.id), 200


@bp.route("/<int:album_id>/items", methods=["POST"])
@jwt_required()
def add_items(album_id):
    """Body: {"media_ids": [1,2,3]}"""
    album = Album.query.filter_by(id=album_id, user_id=_uid(), is_deleted=False).first_or_404()
    data = request.get_json(silent=True) or {}
    media_ids = data.get("media_ids") or []

    owned_ids = {
        m.id for m in Media.query.filter(
            Media.id.in_(media_ids), Media.user_id == _uid(), Media.is_deleted.is_(False)
        ).all()
    }
    added = 0
    for mid in owned_ids:
        if not AlbumMedia.query.filter_by(album_id=album.id, media_id=mid).first():
            db.session.add(AlbumMedia(album_id=album.id, media_id=mid))
            added += 1
    if added and not album.cover_media_id:
        album.cover_media_id = next(iter(owned_ids))
    db.session.commit()
    return jsonify(added=added), 200


@bp.route("/<int:album_id>/items/<int:media_id>", methods=["DELETE"])
@jwt_required()
def remove_item(album_id, media_id):
    album = Album.query.filter_by(id=album_id, user_id=_uid(), is_deleted=False).first_or_404()
    AlbumMedia.query.filter_by(album_id=album.id, media_id=media_id).delete()
    db.session.commit()
    return jsonify(removed=True), 200
