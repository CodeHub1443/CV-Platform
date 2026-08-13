from __future__ import annotations

from typing import Any

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from cv_platform.shared.api_core._router import Router


def create_app(
    routers: list[Router],
    error_map: dict[type, int] | None = None,
    config: dict[str, Any] | None = None,
) -> Flask:
    """
    Create a Flask application from a list of Routers.

    error_map maps domain exception types to HTTP status codes so that
    callers do not need to embed HTTP knowledge in service or domain code.
    """
    app = Flask(__name__)

    if config:
        app.config.update(config)

    for router in routers:
        app.register_blueprint(router.blueprint)

    _register_error_handlers(app, error_map or {})
    return app


def _register_error_handlers(app: Flask, error_map: dict[type, int]) -> None:
    @app.errorhandler(HTTPException)
    def handle_http(exc: HTTPException):
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_exception(exc: Exception):
        for exc_type, status_code in error_map.items():
            if isinstance(exc, exc_type):
                return jsonify({"error": str(exc)}), status_code
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "Internal server error"}), 500
