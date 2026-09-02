from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from extensions import db
from models import Media, User

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _admin_user():
    return User.query.get_or_404(int(get_jwt_identity()))


def _require_admin():
    user = _admin_user()
    if not user.is_admin:
        return jsonify(error="Administrator access required."), 403
    return None


@bp.route("/users", methods=["GET"])
@jwt_required()
def users():
    denied = _require_admin()
    if denied:
        return denied
    return jsonify(users=[user.to_dict() for user in User.query.order_by(User.created_at).all()]), 200


@bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    denied = _require_admin()
    if denied:
        return denied
    return jsonify(
        users=User.query.count(),
        media=Media.query.filter_by(is_deleted=False).count(),
        storage_bytes=db.session.query(db.func.coalesce(db.func.sum(Media.file_size), 0))
        .filter(Media.is_deleted.is_(False)).scalar(),
    ), 200


@bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    denied = _require_admin()
    if denied:
        return denied
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}
    if "quota_bytes" in data:
        try:
            quota = int(data["quota_bytes"])
        except (TypeError, ValueError):
            return jsonify(error="quota_bytes must be an integer."), 400
        if quota < user.storage_used():
            return jsonify(error="Quota cannot be below current storage usage."), 400
        user.quota_bytes = quota
    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])
    db.session.commit()
    return jsonify(user=user.to_dict()), 200
