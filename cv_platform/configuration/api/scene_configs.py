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
from cv_platform.configuration.api._serializers import serialize_scene_config
from cv_platform.configuration.services.scene_config_service import (
    CreateSceneConfigInput,
    SceneConfigService,
    UpdateSceneConfigInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_scene_configs_router(service: SceneConfigService) -> Router:
    router = Router("scene_configs", "/api/v1/scene-configs")

    @router.route("/", methods=["GET"])
    def list_scene_configs():
        camera_config_id = parse_uuid(
            request.args.get("camera_config_id"), "camera_config_id"
        )
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(camera_config_id=camera_config_id, is_active=is_active)
        return json_ok([serialize_scene_config(sc) for sc in items])

    @router.route("/", methods=["POST"])
    def create_scene_config():
        body = get_json_body()
        inp = CreateSceneConfigInput(
            camera_config_id=require_uuid(
                body.get("camera_config_id"), "camera_config_id"
            ),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            rois=body.get("rois"),
            zones=body.get("zones"),
            ground_plane=body.get("ground_plane"),
            privacy_masks=body.get("privacy_masks"),
            calibration=body.get("calibration"),
            status=body.get("status", "active"),
        )
        sc = service.create(inp)
        return json_created(serialize_scene_config(sc))

    @router.route("/<scene_config_id>", methods=["GET"])
    def get_scene_config(scene_config_id: str):
        uid = require_uuid(scene_config_id, "scene_config_id")
        sc = service.get(uid)
        return json_ok(serialize_scene_config(sc))

    @router.route("/<scene_config_id>", methods=["PUT"])
    def update_scene_config(scene_config_id: str):
        uid = require_uuid(scene_config_id, "scene_config_id")
        body = get_json_body()
        inp = UpdateSceneConfigInput(
            scene_config_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            rois=body.get("rois"),
            zones=body.get("zones"),
            ground_plane=body.get("ground_plane"),
            privacy_masks=body.get("privacy_masks"),
            calibration=body.get("calibration"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        sc = service.update(inp)
        return json_ok(serialize_scene_config(sc))

    @router.route("/<scene_config_id>", methods=["DELETE"])
    def delete_scene_config(scene_config_id: str):
        uid = require_uuid(scene_config_id, "scene_config_id")
        service.delete(uid)
        return json_no_content()

    return router
