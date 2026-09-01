import hashlib
import os
import uuid
from PIL import Image, ExifTags
from flask import current_app


def sha256_of_file(file_storage):
    """Stream-hash an uploaded file without loading it fully into memory,
    then rewind so it can still be saved afterwards."""
    hasher = hashlib.sha256()
    file_storage.stream.seek(0)
    for chunk in iter(lambda: file_storage.stream.read(1024 * 1024), b""):
        hasher.update(chunk)
    file_storage.stream.seek(0)
    return hasher.hexdigest()


def classify_media(filename, mime_type):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in current_app.config["ALLOWED_VIDEO_EXT"] or (mime_type or "").startswith("video/"):
        return "video", ext
    if ext in current_app.config["ALLOWED_IMAGE_EXT"] or (mime_type or "").startswith("image/"):
        return "photo", ext
    return None, ext


def unique_storage_name(ext):
    """Filename actually used on disk -- decoupled from what the user
    called the file, so collisions/weird characters are never an issue."""
    token = uuid.uuid4().hex
    return f"{token}.{ext}" if ext else token


def extract_image_metadata(path):
    """Returns (width, height, taken_at_epoch_or_None)."""
    width = height = None
    taken_at = None
    try:
        with Image.open(path) as img:
            width, height = img.size
            exif = img._getexif() if hasattr(img, "_getexif") else None
            if exif:
                tag_map = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
                dt_str = tag_map.get("DateTimeOriginal") or tag_map.get("DateTime")
                if dt_str:
                    import datetime
                    try:
                        dt = datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                        taken_at = dt.timestamp()
                    except ValueError:
                        pass
    except Exception:
        pass
    return width, height, taken_at


def generate_image_thumbnail(source_path, thumb_path, size):
    try:
        with Image.open(source_path) as img:
            img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
            # Correct orientation using EXIF before cropping, so portrait
            # phone photos don't end up sideways in the thumbnail grid.
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            img.thumbnail(size)
            img.save(thumb_path, "JPEG", quality=85)
        return True
    except Exception:
        return False


def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}PB"
