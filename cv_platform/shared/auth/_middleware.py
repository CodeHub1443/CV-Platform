from __future__ import annotations

import functools

import jwt as pyjwt
from flask import g, jsonify, request

from cv_platform.shared.auth._jwt import decode_token


def require_auth(f):
    @functools.wraps(f)
    def _wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]
        try:
            payload = decode_token(token)
        except pyjwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        g._auth_user = payload
        return f(*args, **kwargs)

    return _wrapper


def get_current_user() -> dict:
    return g._auth_user
