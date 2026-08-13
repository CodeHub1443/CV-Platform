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
from cv_platform.configuration.api._serializers import serialize_feature_flag
from cv_platform.configuration.services.feature_flag_service import (
    CreateFeatureFlagInput,
    FeatureFlagService,
    UpdateFeatureFlagInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_feature_flags_router(service: FeatureFlagService) -> Router:
    router = Router("feature_flags", "/api/v1/feature-flags")

    @router.route("/", methods=["GET"])
    def list_feature_flags():
        target_type = request.args.get("target_type")
        target_id = parse_uuid(request.args.get("target_id"), "target_id")
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(
            target_type=target_type, target_id=target_id, is_active=is_active
        )
        return json_ok([serialize_feature_flag(ff) for ff in items])

    @router.route("/", methods=["POST"])
    def create_feature_flag():
        body = get_json_body()
        inp = CreateFeatureFlagInput(
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            description=body.get("description"),
            is_enabled=body.get("is_enabled", False),
            target_type=body.get("target_type", "global"),
            target_id=parse_uuid(body.get("target_id"), "target_id"),
            status=body.get("status", "active"),
        )
        ff = service.create(inp)
        return json_created(serialize_feature_flag(ff))

    @router.route("/<feature_flag_id>", methods=["GET"])
    def get_feature_flag(feature_flag_id: str):
        uid = require_uuid(feature_flag_id, "feature_flag_id")
        ff = service.get(uid)
        return json_ok(serialize_feature_flag(ff))

    @router.route("/<feature_flag_id>", methods=["PUT"])
    def update_feature_flag(feature_flag_id: str):
        uid = require_uuid(feature_flag_id, "feature_flag_id")
        body = get_json_body()
        inp = UpdateFeatureFlagInput(
            feature_flag_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            description=body.get("description"),
            is_enabled=body.get("is_enabled"),
            target_type=body.get("target_type"),
            target_id=parse_uuid(body.get("target_id"), "target_id"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        ff = service.update(inp)
        return json_ok(serialize_feature_flag(ff))

    @router.route("/<feature_flag_id>", methods=["DELETE"])
    def delete_feature_flag(feature_flag_id: str):
        uid = require_uuid(feature_flag_id, "feature_flag_id")
        service.delete(uid)
        return json_no_content()

    return router
