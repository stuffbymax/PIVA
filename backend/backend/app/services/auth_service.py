"""
Auth business logic, kept separate from the route handlers in
app/routes/auth.py so the HTTP layer stays thin.
"""

import re

from app.extensions import db
from app.models.user import User
from app.utils.errors import APIError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def register_user(email: str, password: str) -> User:
    if not email or not EMAIL_RE.match(email):
        raise APIError("INVALID_EMAIL", "A valid email address is required.", 400)
    if not password or len(password) < 8:
        raise APIError("WEAK_PASSWORD", "Password must be at least 8 characters.", 400)

    email = email.strip().lower()

    existing = User.query.filter_by(email=email).first()
    if existing:
        raise APIError("EMAIL_TAKEN", "An account with this email already exists.", 409)

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User:
    if not email or not password:
        raise APIError("INVALID_CREDENTIALS", "Email and password are required.", 400)

    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise APIError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
    return user


def get_user_by_id(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if not user:
        raise APIError("USER_NOT_FOUND", "User not found.", 404)
    return user
