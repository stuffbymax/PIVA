from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Media, Album

bp = Blueprint("sync", __name__, url_prefix="/sync")


@bp.route("", methods=["GET"])
@jwt_required()
def sync():
    """
    Delta sync, the way the Google Photos / Drive apps actually keep a
    phone in sync without re-downloading everything on every launch.

    Flow for the Flutter client:
      1. First run: call with no `since` -> get everything, store the
         `server_time` from the response.
      2. Every run after: call with `since=<last stored server_time>` ->
         get only what changed (created, edited, favorited, trashed,
         restored, or permanently deleted) since then, plus a new
         `server_time` to store for next time.

    A permanently-deleted item comes back as {"id": X, "deleted": true}
    instead of being silently omitted, so the client knows to remove it
    locally rather than assuming it just didn't change.
    """
    since = request.args.get("since", 0, type=float)
    uid = int(get_jwt_identity())
    server_time = _now()

    media_rows = (
        Media.query.filter(Media.user_id == uid, Media.updated_at > since)
        .order_by(Media.updated_at.asc())
        .limit(1000)
        .all()
    )
    album_rows = (
        Album.query.filter(Album.user_id == uid, Album.updated_at > since)
        .order_by(Album.updated_at.asc())
        .limit(500)
        .all()
    )

    host = request.host_url.rstrip("/")
    return jsonify(
        server_time=server_time,
        media=[m.to_dict(host) for m in media_rows],
        albums=[a.to_dict() for a in album_rows],
        more=len(media_rows) == 1000,  # client should call again immediately if true
    ), 200


def _now():
    import time
    return time.time()
