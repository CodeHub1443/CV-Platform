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
from cv_platform.configuration.api._serializers import serialize_camera_config
from cv_platform.configuration.services.camera_config_service import (
    CameraConfigService,
    CreateCameraConfigInput,
    UpdateCameraConfigInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_camera_configs_router(service: CameraConfigService) -> Router:
    router = Router("camera_configs", "/api/v1/camera-configs")

    @router.route("/", methods=["GET"])
    def list_camera_configs():
        site_id = parse_uuid(request.args.get("site_id"), "site_id")
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(site_id=site_id, is_active=is_active)
        return json_ok([serialize_camera_config(cc) for cc in items])

    @router.route("/", methods=["POST"])
    def create_camera_config():
        body = get_json_body()
        inp = CreateCameraConfigInput(
            site_id=require_uuid(body.get("site_id"), "site_id"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            rtsp_url=body.get("rtsp_url"),
            credentials=body.get("credentials"),
            resolution=body.get("resolution"),
            capabilities=body.get("capabilities"),
            status=body.get("status", "active"),
        )
        cc = service.create(inp)
        return json_created(serialize_camera_config(cc))

    @router.route("/<camera_config_id>", methods=["GET"])
    def get_camera_config(camera_config_id: str):
        uid = require_uuid(camera_config_id, "camera_config_id")
        cc = service.get(uid)
        return json_ok(serialize_camera_config(cc))

    @router.route("/<camera_config_id>", methods=["PUT"])
    def update_camera_config(camera_config_id: str):
        uid = require_uuid(camera_config_id, "camera_config_id")
        body = get_json_body()
        inp = UpdateCameraConfigInput(
            camera_config_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            rtsp_url=body.get("rtsp_url"),
            credentials=body.get("credentials"),
            resolution=body.get("resolution"),
            capabilities=body.get("capabilities"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        cc = service.update(inp)
        return json_ok(serialize_camera_config(cc))

    @router.route("/<camera_config_id>", methods=["DELETE"])
    def delete_camera_config(camera_config_id: str):
        uid = require_uuid(camera_config_id, "camera_config_id")
        service.delete(uid)
        return json_no_content()

    return router
