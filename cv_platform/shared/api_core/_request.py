from __future__ import annotations

from flask import abort, request


def get_json_body() -> dict:
    """Parse and return the JSON request body as a dict."""
    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        abort(400, description="Request body must be a valid JSON object")
    return data
