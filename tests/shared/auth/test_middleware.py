"""Unit tests for the require_auth decorator and get_current_user."""
from __future__ import annotations

import datetime

import jwt as pyjwt
import pytest
from flask import Flask, g, jsonify

from cv_platform.shared.auth._middleware import get_current_user, require_auth


@pytest.fixture(autouse=True)
def secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")


def _make_token(user_id: str = "u1", roles: list | None = None, expired: bool = False) -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    exp = now - datetime.timedelta(hours=1) if expired else now + datetime.timedelta(hours=1)
    payload = {"user_id": user_id, "roles": roles or [], "iat": now, "exp": exp}
    return pyjwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True

    @flask_app.route("/protected")
    @require_auth
    def protected():
        user = get_current_user()
        return jsonify({"user_id": user["user_id"]}), 200

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_valid_token_grants_access(client):
    token = _make_token("alice")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["user_id"] == "alice"


def test_missing_header_returns_401(client):
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_malformed_header_returns_401(client):
    resp = client.get("/protected", headers={"Authorization": "Token abc"})
    assert resp.status_code == 401


def test_expired_token_returns_401(client):
    token = _make_token(expired=True)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "expired" in resp.get_json()["error"].lower()


def test_invalid_token_returns_401(client):
    resp = client.get("/protected", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


def test_get_current_user_returns_payload(app):
    with app.test_request_context(
        "/protected",
        headers={"Authorization": f"Bearer {_make_token('bob', ['admin'])}"},
    ):
        from flask import request  # noqa: F401

        @require_auth
        def _view():
            return get_current_user()

        result = _view()
        assert result["user_id"] == "bob"
        assert result["roles"] == ["admin"]
