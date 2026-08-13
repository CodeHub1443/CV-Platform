from __future__ import annotations

from flask import request

from cv_platform.configuration.api._parse import (
    parse_bool,
    parse_datetime,
    parse_uuid,
    require_datetime,
    require_int,
    require_uuid,
)
from cv_platform.configuration.api._serializers import serialize_rule
from cv_platform.configuration.services.rule_service import (
    CreateRuleInput,
    RuleService,
    UpdateRuleInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_rules_router(service: RuleService) -> Router:
    router = Router("rules", "/api/v1/rules")

    @router.route("/", methods=["GET"])
    def list_rules():
        ai_application_id = parse_uuid(
            request.args.get("ai_application_id"), "ai_application_id"
        )
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(ai_application_id=ai_application_id, is_active=is_active)
        return json_ok([serialize_rule(r) for r in items])

    @router.route("/", methods=["POST"])
    def create_rule():
        body = get_json_body()
        inp = CreateRuleInput(
            ai_application_id=require_uuid(
                body.get("ai_application_id"), "ai_application_id"
            ),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            rule_type=body.get("rule_type"),
            parameters=body.get("parameters"),
            status=body.get("status", "active"),
        )
        rule = service.create(inp)
        return json_created(serialize_rule(rule))

    @router.route("/<rule_id>", methods=["GET"])
    def get_rule(rule_id: str):
        uid = require_uuid(rule_id, "rule_id")
        rule = service.get(uid)
        return json_ok(serialize_rule(rule))

    @router.route("/<rule_id>", methods=["PUT"])
    def update_rule(rule_id: str):
        uid = require_uuid(rule_id, "rule_id")
        body = get_json_body()
        inp = UpdateRuleInput(
            rule_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            rule_type=body.get("rule_type"),
            parameters=body.get("parameters"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        rule = service.update(inp)
        return json_ok(serialize_rule(rule))

    @router.route("/<rule_id>", methods=["DELETE"])
    def delete_rule(rule_id: str):
        uid = require_uuid(rule_id, "rule_id")
        service.delete(uid)
        return json_no_content()

    return router
