from __future__ import annotations

from flask import Blueprint


class Router:
    """Thin wrapper around a Flask Blueprint."""

    def __init__(self, name: str, url_prefix: str) -> None:
        self.blueprint = Blueprint(name, __name__, url_prefix=url_prefix)

    def route(self, rule: str, **options):
        return self.blueprint.route(rule, **options)
