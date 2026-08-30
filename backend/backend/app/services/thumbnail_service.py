"""
Simple thumbnail generation.

Images: resized with Pillow, preserving aspect ratio, re-encoded as JPEG.
Videos: no transcoding in the prototype - we generate a static
placeholder thumbnail (a neutral frame with a play icon) rather than
extracting a real video frame, per the prototype scope.
"""

import io

from PIL import Image, ImageDraw

from flask import current_app


def generate_image_thumbnail(file_stream) -> bytes:
    """Return JPEG bytes for a thumbnail of the given image file stream."""
    file_stream.seek(0)
    image = Image.open(file_stream)
    image = image.convert("RGB")  # normalize (handles PNG alpha, etc.)

    max_size = current_app.config["THUMBNAIL_MAX_SIZE"]
    image.thumbnail(max_size, Image.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    file_stream.seek(0)
    return buf.getvalue()


def generate_video_placeholder_thumbnail() -> bytes:
    """Return JPEG bytes for a generic 'video' placeholder thumbnail."""
    width, height = current_app.config["THUMBNAIL_MAX_SIZE"]
    image = Image.new("RGB", (width, height), color=(32, 32, 36))
    draw = ImageDraw.Draw(image)

    # Simple play-button triangle in the center.
    cx, cy = width // 2, height // 2
    size = min(width, height) // 6
    triangle = [
        (cx - size // 2, cy - size),
        (cx - size // 2, cy + size),
        (cx + size, cy),
    ]
    draw.polygon(triangle, fill=(230, 230, 230))

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return buf.getvalue()
