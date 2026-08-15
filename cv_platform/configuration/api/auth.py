from __future__ import annotations

import bcrypt
from flask import jsonify

from cv_platform.configuration.repositories.interfaces import UserRepository
from cv_platform.shared.api_core import Router, get_json_body
from cv_platform.shared.auth import issue_token


def make_auth_router(user_repo: UserRepository) -> Router:
    router = Router("auth", "/api/v1/auth")

    @router.route("/token", methods=["POST"])
    def token():
        body = get_json_body()
        username = body.get("username", "")
        password = body.get("password", "")
        if not username or not password:
            return jsonify({"error": "username and password required"}), 400
        user = user_repo.get_by_username(username)
        if user is None or not user.password_hash:
            return jsonify({"error": "Invalid credentials"}), 401
        if not bcrypt.checkpw(
            password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            return jsonify({"error": "Invalid credentials"}), 401
        return jsonify({"token": issue_token(str(user.id), [])}), 200

    return router
