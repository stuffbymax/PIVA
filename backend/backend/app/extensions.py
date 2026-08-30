"""
Shared Flask extension instances.

Kept in their own module (rather than inside __init__.py) so that
models, routes, and services can import them without creating
circular-import problems with create_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()
