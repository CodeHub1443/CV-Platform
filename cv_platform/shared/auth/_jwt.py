from __future__ import annotations

import datetime
import os

import jwt as pyjwt


def _get_secret() -> str:
    key = os.environ.get("SECRET_KEY")
    if not key:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Set it before starting the server."
        )
    return key


def issue_token(user_id: str, roles: list[str]) -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {
        "user_id": user_id,
        "roles": roles,
        "iat": now,
        "exp": now + datetime.timedelta(hours=1),
    }
    return pyjwt.encode(payload, _get_secret(), algorithm="HS256")


def decode_token(token: str) -> dict:
    return pyjwt.decode(token, _get_secret(), algorithms=["HS256"])
