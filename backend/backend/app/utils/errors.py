"""
Consistent JSON error responses for the whole API.

Every error returned by this API has the shape:

    {
      "error": {
        "code": "SOME_ERROR_CODE",
        "message": "Human readable message"
      }
    }

Routes/services raise APIError with a machine-readable code, a message,
and an HTTP status; register_error_handlers() wires this (plus a few
generic exception types) into Flask's error handling.
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def to_response(self):
        return jsonify({"error": {"code": self.code, "message": self.message}}), self.status_code


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err: APIError):
        return err.to_response()

    @app.errorhandler(413)
    def handle_too_large(_err):
        return jsonify({
            "error": {
                "code": "FILE_TOO_LARGE",
                "message": "Uploaded file exceeds the maximum allowed size.",
            }
        }), 413

    @app.errorhandler(404)
    def handle_not_found(_err):
        return jsonify({
            "error": {"code": "NOT_FOUND", "message": "The requested resource was not found."}
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_err):
        return jsonify({
            "error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed for this endpoint."}
        }), 405

    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        return jsonify({
            "error": {"code": "HTTP_ERROR", "message": err.description or str(err)}
        }), err.code or 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        app.logger.exception("Unhandled exception")
        return jsonify({
            "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}
        }), 500
