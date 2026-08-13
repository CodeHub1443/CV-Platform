from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import jsonify


def configuration_object(
    object_type: str,
    version: int,
    owner: str,
    parameters: dict[str, Any],
    validation: dict[str, Any],
    effective_date: datetime,
) -> dict[str, Any]:
    """Build a ConfigurationObject contract dict."""
    return {
        "object_type": object_type,
        "version": version,
        "owner": owner,
        "parameters": parameters,
        "validation": validation,
        "effective_date": (
            effective_date.isoformat()
            if isinstance(effective_date, datetime)
            else effective_date
        ),
    }


def json_ok(data: Any):
    return jsonify(data), 200


def json_created(data: Any):
    return jsonify(data), 201


def json_no_content():
    return "", 204
