from datetime import timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.models.media import TokenBlocklist
from app.services import auth_service

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    user = auth_service.register_user(email, password)
    return jsonify({"user": user.to_dict()}), 201


@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    user = auth_service.authenticate_user(email, password)

    from flask import current_app
    expires = timedelta(minutes=current_app.config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"])
    access_token = create_access_token(identity=str(user.id), expires_delta=expires)

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in_minutes": current_app.config["JWT_ACCESS_TOKEN_EXPIRES_MINUTES"],
        "user": user.to_dict(),
    }), 200


@bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = auth_service.get_user_by_id(user_id)
    return jsonify({"user": user.to_dict()}), 200


@bp.post("/logout")
@jwt_required()
def logout():
    """
    Real logout: record the current token's jti in the blocklist table
    so it's rejected by future requests even though it hasn't expired.
    See app/__init__.py for the @jwt.token_in_blocklist_loader hook.
    """
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti))
    db.session.commit()
    return jsonify({"message": "Logged out successfully."}), 200
