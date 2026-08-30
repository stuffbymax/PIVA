"""
Streaming SHA-256 hashing for uploaded files.

We hash in chunks rather than reading the whole file into memory so
this stays reasonable for large video files.
"""

import hashlib


CHUNK_SIZE = 1024 * 1024  # 1 MB


def hash_file_stream(file_stream) -> str:
    """
    Compute the SHA-256 hex digest of a file-like object, then reset
    its read position back to the start so it can be re-read (e.g. to
    upload it to MinIO afterwards).
    """
    sha256 = hashlib.sha256()
    file_stream.seek(0)
    while True:
        chunk = file_stream.read(CHUNK_SIZE)
        if not chunk:
            break
        sha256.update(chunk)
    file_stream.seek(0)
    return sha256.hexdigest()


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions


def get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()
