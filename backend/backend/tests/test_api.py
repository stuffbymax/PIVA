"""
Basic end-to-end tests for the auth + media API.

These use a temporary SQLite DB and a fake in-process MinIO stand-in
(monkeypatched) so tests don't require a running MinIO server. For a
real integration test against MinIO, unset the monkeypatch and point
MINIO_ENDPOINT at a running instance.

Run with:
    cd backend
    pytest
"""

import io
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")


@pytest.fixture()
def app(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    from app import create_app
    from app.config import Config

    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    flask_app = create_app(TestConfig)

    # --- Fake MinIO backend (in-memory dict) so tests don't need a
    # real MinIO server running. ---
    store = {}

    def fake_upload_stream(object_key, data_stream, length, content_type):
        data_stream.seek(0)
        store[object_key] = data_stream.read()

    def fake_upload_bytes(object_key, data, content_type):
        store[object_key] = data

    class FakeObj:
        def __init__(self, data):
            self._data = data

        def stream(self, chunk_size):
            yield self._data

        def close(self):
            pass

        def release_conn(self):
            pass

    def fake_get_object_stream(object_key):
        if object_key not in store:
            from app.utils.errors import APIError
            raise APIError("STORAGE_OBJECT_NOT_FOUND", "not found", 404)
        return FakeObj(store[object_key])

    def fake_delete_object(object_key):
        store.pop(object_key, None)

    from app.services import minio_service
    monkeypatch.setattr(minio_service, "upload_stream", fake_upload_stream)
    monkeypatch.setattr(minio_service, "upload_bytes", fake_upload_bytes)
    monkeypatch.setattr(minio_service, "get_object_stream", fake_get_object_stream)
    monkeypatch.setattr(minio_service, "delete_object", fake_delete_object)

    with flask_app.app_context():
        from app.extensions import db
        db.create_all()

    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def register_and_login(client, email="user@example.com", password="password123"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.get_json()["access_token"]


def test_register_login_me(client):
    resp = client.post("/api/auth/register", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 201

    resp = client.post("/api/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 200
    token = resp.get_json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "a@example.com"


def test_duplicate_registration_rejected(client):
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert resp.status_code == 409
    assert resp.get_json()["error"]["code"] == "EMAIL_TAKEN"


def test_upload_list_get_download_delete(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    file_data = (io.BytesIO(b"\xff\xd8\xff\xe0fake-jpeg-bytes"), "test.jpg")
    resp = client.post(
        "/api/media/upload",
        data={"file": file_data, "width": "100", "height": "200"},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    media_id = resp.get_json()["id"]

    resp = client.get("/api/media?page=1&limit=10", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == media_id

    resp = client.get(f"/api/media/{media_id}", headers=headers)
    assert resp.status_code == 200

    resp = client.get(f"/api/media/{media_id}/download", headers=headers)
    assert resp.status_code == 200
    assert resp.data == b"\xff\xd8\xff\xe0fake-jpeg-bytes"

    resp = client.delete(f"/api/media/{media_id}", headers=headers)
    assert resp.status_code == 200

    resp = client.get(f"/api/media/{media_id}", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "MEDIA_NOT_FOUND"


def test_duplicate_upload_returns_existing_record(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    content = b"\xff\xd8\xff\xe0same-bytes-twice"

    resp1 = client.post(
        "/api/media/upload",
        data={"file": (io.BytesIO(content), "a.jpg")},
        headers=headers,
        content_type="multipart/form-data",
    )
    resp2 = client.post(
        "/api/media/upload",
        data={"file": (io.BytesIO(content), "b.jpg")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.get_json()["id"] == resp2.get_json()["id"]


def test_unauthenticated_requests_rejected(client):
    resp = client.get("/api/media")
    assert resp.status_code == 401


def test_users_cannot_access_others_media(client):
    token_a = register_and_login(client, email="usera@example.com")
    token_b = register_and_login(client, email="userb@example.com")

    resp = client.post(
        "/api/media/upload",
        data={"file": (io.BytesIO(b"\xff\xd8\xff\xe0abc"), "a.jpg")},
        headers={"Authorization": f"Bearer {token_a}"},
        content_type="multipart/form-data",
    )
    media_id = resp.get_json()["id"]

    resp = client.get(f"/api/media/{media_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404


def test_logout_revokes_token(client):
    token = register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "TOKEN_REVOKED"
