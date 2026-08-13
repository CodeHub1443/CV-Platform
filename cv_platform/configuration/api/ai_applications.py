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
from cv_platform.configuration.api._serializers import serialize_ai_application
from cv_platform.configuration.services.ai_application_service import (
    AIApplicationService,
    CreateAIApplicationInput,
    UpdateAIApplicationInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_ai_applications_router(service: AIApplicationService) -> Router:
    router = Router("ai_applications", "/api/v1/ai-applications")

    @router.route("/", methods=["GET"])
    def list_ai_applications():
        project_id = parse_uuid(request.args.get("project_id"), "project_id")
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(project_id=project_id, is_active=is_active)
        return json_ok([serialize_ai_application(a) for a in items])

    @router.route("/", methods=["POST"])
    def create_ai_application():
        body = get_json_body()
        inp = CreateAIApplicationInput(
            project_id=require_uuid(body.get("project_id"), "project_id"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            description=body.get("description"),
            status=body.get("status", "active"),
        )
        ai_app = service.create(inp)
        return json_created(serialize_ai_application(ai_app))

    @router.route("/<ai_application_id>", methods=["GET"])
    def get_ai_application(ai_application_id: str):
        uid = require_uuid(ai_application_id, "ai_application_id")
        ai_app = service.get(uid)
        return json_ok(serialize_ai_application(ai_app))

    @router.route("/<ai_application_id>", methods=["PUT"])
    def update_ai_application(ai_application_id: str):
        uid = require_uuid(ai_application_id, "ai_application_id")
        body = get_json_body()
        inp = UpdateAIApplicationInput(
            ai_application_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            description=body.get("description"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        ai_app = service.update(inp)
        return json_ok(serialize_ai_application(ai_app))

    @router.route("/<ai_application_id>", methods=["DELETE"])
    def delete_ai_application(ai_application_id: str):
        uid = require_uuid(ai_application_id, "ai_application_id")
        service.delete(uid)
        return json_no_content()

    return router
