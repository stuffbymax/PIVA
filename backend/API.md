# API Documentation

Base URL (local development): `http://localhost:5000`

All request/response bodies are JSON except file uploads, which are
`multipart/form-data`. All error responses share this shape:

```json
{
  "error": {
    "code": "SOME_ERROR_CODE",
    "message": "Human readable message"
  }
}
```

## Authentication

Except for `/api/auth/register` and `/api/auth/login` (and `/health`),
every endpoint requires a valid JWT access token in the `Authorization`
header:

```
Authorization: Bearer <token>
```

The user ID is always derived from the token server-side. The client
never sends (or needs to send) a `user_id` anywhere.

### Register

```
POST /api/auth/register
```

Body:

```json
{ "email": "user@example.com", "password": "at-least-8-chars" }
```

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

Response `201`:

```json
{ "user": { "id": 1, "email": "user@example.com", "created_at": "2026-08-30T12:00:00Z" } }
```

Errors: `INVALID_EMAIL` (400), `WEAK_PASSWORD` (400), `EMAIL_TAKEN` (409)

### Login

```
POST /api/auth/login
```

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

Response `200`:

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in_minutes": 60,
  "user": { "id": 1, "email": "user@example.com", "created_at": "2026-08-30T12:00:00Z" }
}
```

Errors: `INVALID_CREDENTIALS` (401)

### Current user

```
GET /api/auth/me
```

```bash
curl http://localhost:5000/api/auth/me -H "Authorization: Bearer TOKEN"
```

### Logout

```
POST /api/auth/logout
```

Revokes the current access token server-side (adds its `jti` to a
blocklist table), so it stops working immediately even before it
expires.

```bash
curl -X POST http://localhost:5000/api/auth/logout -H "Authorization: Bearer TOKEN"
```

---

## Media

### Upload

```
POST /api/media/upload
```

Multipart form fields:

| field      | required | notes                                   |
|------------|----------|------------------------------------------|
| `file`     | yes      | the photo or video file                  |
| `width`    | no       | pixel width, if known client-side        |
| `height`   | no       | pixel height, if known client-side       |
| `duration` | no       | seconds, for videos                      |

```bash
curl \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@photo.jpg" \
  -F "width=4032" \
  -F "height=3024" \
  http://localhost:5000/api/media/upload
```

Response `201`:

```json
{
  "id": 123,
  "filename": "IMG_1234.JPG",
  "status": "uploaded",
  "media": {
    "id": 123,
    "filename": "IMG_1234.JPG",
    "mime_type": "image/jpeg",
    "size": 4212345,
    "file_hash": "e3b0c4...",
    "created_at": "2026-08-30T12:00:00Z",
    "width": 4032,
    "height": 3024,
    "duration": null,
    "download_url": "/api/media/123/download",
    "thumbnail_url": "/api/media/123/thumbnail"
  }
}
```

If the same user uploads a file with the same SHA-256 hash again, the
existing record is returned (same `id`) instead of creating a
duplicate object in MinIO.

Errors: `INVALID_FILE` (400), `UNSUPPORTED_FILE_TYPE` (415),
`FILE_TOO_LARGE` (413), `STORAGE_UNAVAILABLE` (503)

### List media

```
GET /api/media?page=1&limit=50
```

```bash
curl "http://localhost:5000/api/media?page=1&limit=50" -H "Authorization: Bearer TOKEN"
```

Response `200`:

```json
{
  "items": [ { "id": 123, "filename": "IMG_1234.JPG", "...": "..." } ],
  "page": 1,
  "limit": 50,
  "total": 1234
}
```

### Get one

```
GET /api/media/:id
```

```bash
curl http://localhost:5000/api/media/123 -H "Authorization: Bearer TOKEN"
```

Errors: `MEDIA_NOT_FOUND` (404) — also returned if the media belongs to
another user, so ownership can't be probed.

### Download

```
GET /api/media/:id/download
```

Streams the original file through Flask (Flask is the only thing that
talks to MinIO directly).

```bash
curl -OJ http://localhost:5000/api/media/123/download -H "Authorization: Bearer TOKEN"
```

### Thumbnail

```
GET /api/media/:id/thumbnail
```

```bash
curl http://localhost:5000/api/media/123/thumbnail -H "Authorization: Bearer TOKEN" -o thumb.jpg
```

Errors: `THUMBNAIL_NOT_AVAILABLE` (404)

### Delete

```
DELETE /api/media/:id
```

```bash
curl -X DELETE http://localhost:5000/api/media/123 -H "Authorization: Bearer TOKEN"
```

Removes the database row and the original + thumbnail objects in
MinIO.

---

## Error codes reference

| Code                      | Status | Meaning                                           |
|---------------------------|--------|----------------------------------------------------|
| `INVALID_EMAIL`           | 400    | Registration email missing/malformed               |
| `WEAK_PASSWORD`           | 400    | Password shorter than 8 characters                  |
| `EMAIL_TAKEN`             | 409    | Account already exists for that email              |
| `INVALID_CREDENTIALS`     | 401    | Wrong email/password on login                       |
| `USER_NOT_FOUND`          | 404    | JWT valid but user no longer exists                 |
| `AUTHORIZATION_REQUIRED`  | 401    | Missing `Authorization` header                      |
| `INVALID_TOKEN`           | 401    | Malformed/invalid JWT                               |
| `TOKEN_EXPIRED`           | 401    | JWT has expired                                     |
| `TOKEN_REVOKED`           | 401    | JWT was logged out                                  |
| `INVALID_FILE`            | 400    | No file / empty file in upload                      |
| `UNSUPPORTED_FILE_TYPE`   | 415    | Extension or MIME type not allowed                  |
| `FILE_TOO_LARGE`          | 413    | Exceeds `MAX_CONTENT_LENGTH_MB`                     |
| `MEDIA_NOT_FOUND`         | 404    | No such media, or it belongs to another user        |
| `THUMBNAIL_NOT_AVAILABLE` | 404    | Media exists but has no thumbnail                   |
| `STORAGE_UNAVAILABLE`     | 503    | MinIO could not be reached                          |
| `STORAGE_OBJECT_NOT_FOUND`| 404    | Metadata exists in SQLite but object missing in MinIO|
| `INVALID_QUERY_PARAM`     | 400    | e.g. non-integer `page`/`limit`                     |
| `NOT_FOUND`               | 404    | Unknown route                                       |
| `METHOD_NOT_ALLOWED`      | 405    | Wrong HTTP method for a route                       |
| `INTERNAL_ERROR`          | 500    | Unexpected server error                             |

The Flutter client should treat `STORAGE_UNAVAILABLE` and network-level
failures as **retryable** (leave the item `pending`/`failed` and try
again later), and treat things like `UNSUPPORTED_FILE_TYPE` or
`INVALID_FILE` as **permanent** (don't retry the same file).
