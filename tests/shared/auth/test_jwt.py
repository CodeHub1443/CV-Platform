"""Unit tests for the shared JWT module."""
from __future__ import annotations

import datetime

import jwt as pyjwt
import pytest

from cv_platform.shared.auth._jwt import decode_token, issue_token


@pytest.fixture(autouse=True)
def secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")


def test_issue_token_returns_string():
    token = issue_token("user-123", ["admin"])
    assert isinstance(token, str)
    assert len(token) > 0


def test_issued_token_contains_user_id_and_roles():
    token = issue_token("user-abc", ["viewer", "editor"])
    payload = decode_token(token)
    assert payload["user_id"] == "user-abc"
    assert payload["roles"] == ["viewer", "editor"]


def test_issued_token_has_exp_claim():
    token = issue_token("user-123", [])
    payload = decode_token(token)
    assert "exp" in payload


def test_decode_token_raises_on_expired():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {
        "user_id": "u1",
        "roles": [],
        "iat": now - datetime.timedelta(hours=2),
        "exp": now - datetime.timedelta(hours=1),
    }
    expired_token = pyjwt.encode(payload, "test-secret", algorithm="HS256")
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(expired_token)


def test_decode_token_raises_on_wrong_signature():
    token = issue_token("u1", [])
    wrong_key_token = pyjwt.encode({"user_id": "u1"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_token(wrong_key_token)


def test_decode_token_raises_on_malformed():
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_token("not.a.jwt")


def test_issue_token_raises_when_secret_key_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        issue_token("u1", [])
