import time
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


def now_ts():
    """Server timestamp (float, seconds since epoch) used as the sync
    cursor. Using a plain float instead of DATETIME keeps '>' comparisons
    on the /sync endpoint unambiguous across SQLite/Postgres."""
    return time.time()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    quota_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    created_at = db.Column(db.Float, default=now_ts)

    media = db.relationship("Media", backref="owner", lazy="dynamic")
    albums = db.relationship("Album", backref="owner", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def storage_used(self):
        total = (
            db.session.query(db.func.coalesce(db.func.sum(Media.file_size), 0))
            .filter(Media.user_id == self.id, Media.is_deleted.is_(False))
            .scalar()
        )
        return int(total or 0)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "quota_bytes": self.quota_bytes,
            "storage_used_bytes": self.storage_used(),
        }


class Media(db.Model):
    """
    A single photo or video.

    Soft-delete model (mirrors Google Photos' Trash):
      is_trashed=True   -> in Trash, still occupies storage, restorable
      is_deleted=True   -> permanently gone; the DB row becomes a tombstone
                            (file bytes removed) so /sync can still tell
                            clients "this id no longer exists".
    """

    __tablename__ = "media"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    filename = db.Column(db.String(255), nullable=False)          # stored filename on disk
    original_filename = db.Column(db.String(255), nullable=False)  # what the user uploaded
    thumbnail_filename = db.Column(db.String(255), nullable=True)

    media_type = db.Column(db.String(10), nullable=False)  # 'photo' | 'video'
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False, default=0)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)  # videos only

    checksum = db.Column(db.String(64), nullable=False, index=True)  # sha256, for dedup

    taken_at = db.Column(db.Float, nullable=True)   # EXIF / client-reported capture time
    created_at = db.Column(db.Float, default=now_ts)  # server upload time
    updated_at = db.Column(db.Float, default=now_ts, onupdate=now_ts, index=True)

    is_favorite = db.Column(db.Boolean, default=False)
    is_trashed = db.Column(db.Boolean, default=False)
    trashed_at = db.Column(db.Float, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # tombstone

    __table_args__ = (
        db.UniqueConstraint("user_id", "checksum", name="uq_user_checksum"),
    )

    def touch(self):
        self.updated_at = now_ts()

    def to_dict(self, request_host=""):
        if self.is_deleted:
            return {"id": self.id, "deleted": True, "updated_at": self.updated_at}
        return {
            "id": self.id,
            "deleted": False,
            "original_filename": self.original_filename,
            "media_type": self.media_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "duration_ms": self.duration_ms,
            "checksum": self.checksum,
            "taken_at": self.taken_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_favorite": self.is_favorite,
            "is_trashed": self.is_trashed,
            "trashed_at": self.trashed_at,
            "download_url": f"{request_host}/media/{self.id}/file",
            "thumbnail_url": f"{request_host}/media/{self.id}/thumbnail" if self.thumbnail_filename else None,
        }


class Album(db.Model):
    __tablename__ = "albums"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    cover_media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=True)

    created_at = db.Column(db.Float, default=now_ts)
    updated_at = db.Column(db.Float, default=now_ts, onupdate=now_ts, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    items = db.relationship("AlbumMedia", backref="album", lazy="dynamic",
                             cascade="all, delete-orphan")

    def to_dict(self):
        if self.is_deleted:
            return {"id": self.id, "deleted": True, "updated_at": self.updated_at}
        return {
            "id": self.id,
            "deleted": False,
            "name": self.name,
            "cover_media_id": self.cover_media_id,
            "item_count": self.items.count(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class AlbumMedia(db.Model):
    """Join table: which media belong to which album."""
    __tablename__ = "album_media"

    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey("albums.id"), nullable=False, index=True)
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False, index=True)
    added_at = db.Column(db.Float, default=now_ts)

    media = db.relationship("Media")

    __table_args__ = (
        db.UniqueConstraint("album_id", "media_id", name="uq_album_media"),
    )
