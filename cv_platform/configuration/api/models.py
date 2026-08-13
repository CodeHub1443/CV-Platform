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
from cv_platform.configuration.api._serializers import serialize_model
from cv_platform.configuration.services.model_service import (
    CreateModelInput,
    ModelService,
    UpdateModelInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_models_router(service: ModelService) -> Router:
    router = Router("models", "/api/v1/models")

    @router.route("/", methods=["GET"])
    def list_models():
        ai_application_id = parse_uuid(
            request.args.get("ai_application_id"), "ai_application_id"
        )
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(ai_application_id=ai_application_id, is_active=is_active)
        return json_ok([serialize_model(m) for m in items])

    @router.route("/", methods=["POST"])
    def create_model():
        body = get_json_body()
        inp = CreateModelInput(
            ai_application_id=require_uuid(
                body.get("ai_application_id"), "ai_application_id"
            ),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            model_type=body.get("model_type"),
            parameters=body.get("parameters"),
            status=body.get("status", "active"),
        )
        model = service.create(inp)
        return json_created(serialize_model(model))

    @router.route("/<model_id>", methods=["GET"])
    def get_model(model_id: str):
        uid = require_uuid(model_id, "model_id")
        model = service.get(uid)
        return json_ok(serialize_model(model))

    @router.route("/<model_id>", methods=["PUT"])
    def update_model(model_id: str):
        uid = require_uuid(model_id, "model_id")
        body = get_json_body()
        inp = UpdateModelInput(
            model_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            model_type=body.get("model_type"),
            parameters=body.get("parameters"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        model = service.update(inp)
        return json_ok(serialize_model(model))

    @router.route("/<model_id>", methods=["DELETE"])
    def delete_model(model_id: str):
        uid = require_uuid(model_id, "model_id")
        service.delete(uid)
        return json_no_content()

    return router
