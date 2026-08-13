"""Request-parsing helpers for the Configuration Platform API."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from flask import abort


def parse_uuid(value: str | None, field: str) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        abort(400, description=f"{field} must be a valid UUID")


def require_uuid(value: str | None, field: str) -> UUID:
    if value is None:
        abort(400, description=f"{field} is required")
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        abort(400, description=f"{field} must be a valid UUID")


def parse_datetime(value: str | None, field: str) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, AttributeError):
        abort(400, description=f"{field} must be a valid ISO 8601 datetime")


def require_datetime(value: str | None, field: str) -> datetime:
    if value is None:
        abort(400, description=f"{field} is required")
    try:
        return datetime.fromisoformat(value)
    except (ValueError, AttributeError):
        abort(400, description=f"{field} must be a valid ISO 8601 datetime")


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.lower() in ("true", "1", "yes")


def require_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        abort(400, description=f"{field} must be an integer")
    return value
