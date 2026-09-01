import os
from flask import Flask, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS
from config import Config
from extensions import db, jwt
from models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["THUMBNAIL_FOLDER"], exist_ok=True)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    from routes.auth import bp as auth_bp
    from routes.media import bp as media_bp
    from routes.albums import bp as albums_bp
    from routes.sync import bp as sync_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(albums_bp)
    app.register_blueprint(sync_bp)

    @app.route("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.route("/storage", methods=["GET"])
    @jwt_required()
    def storage():
        user = User.query.get_or_404(int(get_jwt_identity()))
        return jsonify(
            used_bytes=user.storage_used(),
            quota_bytes=user.quota_bytes,
        ), 200

    # --- JWT error handlers -> clean JSON instead of HTML error pages ---
    @jwt.unauthorized_loader
    def _missing_token(reason):
        return jsonify(error="Authorization token required.", detail=reason), 401

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return jsonify(error="Invalid token.", detail=reason), 422

    @jwt.expired_token_loader
    def _expired_token(header, payload):
        return jsonify(error="Token has expired."), 401

    with app.app_context():
        db.create_all()

    return app


app = create_app()

# debug stuff
# this displays everything in the db
@app.route("/debug/all")
def debug_all():
    users = User.query.all()
    
    return jsonify(
        users=[user.to_dict() for user in users],
        videos=sum(len(user.videos) for user in users),
        images=sum(len(user.images) for user in users),
        total_users=len(users),
        total_storage=sum(user.storage_used() for user in users),
        used_storage=sum(user.storage_used() for user in users),
        free_storage=sum(user.quota_bytes - user.storage_used() for user in users),
        total_quota=sum(user.quota_bytes for user in users),
        total_quota_gb=sum(user.quota_bytes for user in users) / (1024 ** 3),
        deleted_videos = sum(len(user.deleted_videos) for user in users),
        deleted_images = sum(len(user.deleted_images) for user in users),


    ), 200 


if __name__ == "__main__":
    # debug=False in production; use gunicorn/uwsgi behind nginx for real
    # deployments (see README).
    app.run(host="0.0.0.0", port=5009, debug=True)
