from datetime import datetime, timezone

from app.extensions import db


class Media(db.Model):
    __tablename__ = "media"
    __table_args__ = (
        db.UniqueConstraint("user_id", "file_hash", name="uq_media_user_file_hash"),
        db.Index("ix_media_user_created", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = db.Column(db.String(512), nullable=False)
    object_key = db.Column(db.String(1024), nullable=False)
    thumbnail_key = db.Column(db.String(1024), nullable=True)

    mime_type = db.Column(db.String(128), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    modified_at = db.Column(db.DateTime, nullable=True)

    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    duration = db.Column(db.Float, nullable=True)  # seconds, for videos

    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def is_video(self) -> bool:
        return self.mime_type.startswith("video/")

    def to_dict(self, include_urls: bool = True) -> dict:
        data = {
            "id": self.id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size": self.size,
            "file_hash": self.file_hash,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "modified_at": self.modified_at.isoformat() + "Z" if self.modified_at else None,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "uploaded_at": self.uploaded_at.isoformat() + "Z" if self.uploaded_at else None,
        }
        if include_urls:
            data["download_url"] = f"/api/media/{self.id}/download"
            data["thumbnail_url"] = f"/api/media/{self.id}/thumbnail" if self.thumbnail_key else None
        return data


class TokenBlocklist(db.Model):
    """
    Revoked JWTs. A row's presence means that jti is no longer valid,
    even if it hasn't expired yet. This is what makes /api/auth/logout
    actually work (rather than being a client-only no-op).
    """

    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(64), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
