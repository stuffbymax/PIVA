from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from extensions import db
from models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip() or None
    password = data.get("password") or ""

    if len(username) < 3 or not username.isalnum():
        return jsonify(error="Username must be 3+ alphanumeric characters."), 400
    if len(password) < 6:
        return jsonify(error="Password must be at least 6 characters."), 400

    if User.query.filter_by(username=username).first():
        return jsonify(error="Username already taken."), 409

    user = User(username=username, email=email,
                quota_bytes=current_app.config["DEFAULT_QUOTA_BYTES"],
                is_admin=User.query.count() == 0)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify(user=user.to_dict(), access_token=access, refresh_token=refresh), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify(error="Invalid username or password."), 401

    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify(user=user.to_dict(), access_token=access, refresh_token=refresh), 200


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Flutter app calls this with the refresh token once the short-lived
    access token expires, instead of asking the user to log in again."""
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)
    return jsonify(access_token=access), 200


@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify(user=user.to_dict()), 200
