"""Shared validation helpers used across Configuration Platform services."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from cv_platform.configuration.domain.exceptions import ValidationError

_ENTITY_STATUSES = frozenset({"active", "inactive", "archived"})
_USER_STATUSES = frozenset({"active", "inactive", "suspended"})
_DEPLOYMENT_STATUSES = frozenset({"pending", "active", "inactive", "failed", "archived"})
_FLAG_TARGET_TYPES = frozenset({"global", "project", "user"})
_PROJECT_USER_ROLES = frozenset({"owner", "admin", "operator", "viewer"})


def require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} is required and must be a non-empty string")
    return value.strip()


def require_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValidationError(f"{field} is required and must be a datetime")
    return value


def require_uuid(value: Any, field: str) -> UUID:
    if not isinstance(value, UUID):
        raise ValidationError(f"{field} is required and must be a UUID")
    return value


def validate_entity_status(status: str) -> None:
    if status not in _ENTITY_STATUSES:
        raise ValidationError(
            f"status must be one of {sorted(_ENTITY_STATUSES)}, got {status!r}"
        )


def validate_user_status(status: str) -> None:
    if status not in _USER_STATUSES:
        raise ValidationError(
            f"status must be one of {sorted(_USER_STATUSES)}, got {status!r}"
        )


def validate_deployment_status(status: str) -> None:
    if status not in _DEPLOYMENT_STATUSES:
        raise ValidationError(
            f"status must be one of {sorted(_DEPLOYMENT_STATUSES)}, got {status!r}"
        )


def validate_flag_target_type(target_type: str) -> None:
    if target_type not in _FLAG_TARGET_TYPES:
        raise ValidationError(
            f"target_type must be one of {sorted(_FLAG_TARGET_TYPES)}, got {target_type!r}"
        )


def validate_project_user_role(role: str) -> None:
    if role not in _PROJECT_USER_ROLES:
        raise ValidationError(
            f"role must be one of {sorted(_PROJECT_USER_ROLES)}, got {role!r}"
        )


def validate_email(email: str) -> None:
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValidationError(f"email {email!r} is not a valid email address")
