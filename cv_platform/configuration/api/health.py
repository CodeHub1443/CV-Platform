from __future__ import annotations

from flask import Blueprint, jsonify


def make_health_blueprint() -> Blueprint:
    bp = Blueprint("health", __name__)

    @bp.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    return bp
