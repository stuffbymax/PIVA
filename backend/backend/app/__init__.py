import os

from flask import Flask, jsonify

from app.config import Config
from app.extensions import db, jwt
from app.utils.errors import register_error_handlers
from app.services import minio_service


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Make sure the data directory exists (in case ini.py hasn't been
    # run yet - the app can still boot for basic non-DB routes).
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)

    register_error_handlers(app)

    # --- JWT blocklist (real logout support) ---
    from app.models.media import TokenBlocklist

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        with app.app_context():
            return db.session.query(TokenBlocklist.id).filter_by(jti=jti).first() is not None

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return jsonify({"error": {"code": "TOKEN_EXPIRED", "message": "The token has expired."}}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": {"code": "INVALID_TOKEN", "message": f"Invalid token: {reason}"}}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({"error": {"code": "AUTHORIZATION_REQUIRED", "message": reason}}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        return jsonify({"error": {"code": "TOKEN_REVOKED", "message": "The token has been revoked."}}), 401

    # --- MinIO (best-effort at startup; upload calls fail clearly if down) ---
    minio_service.init_minio(app)

    # --- Blueprints ---
    from app.routes.auth import bp as auth_bp
    from app.routes.media import bp as media_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(media_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
