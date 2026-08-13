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
from cv_platform.configuration.api._serializers import serialize_deployment
from cv_platform.configuration.services.deployment_service import (
    CreateDeploymentInput,
    DeploymentService,
    UpdateDeploymentInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_deployments_router(service: DeploymentService) -> Router:
    router = Router("deployments", "/api/v1/deployments")

    @router.route("/", methods=["GET"])
    def list_deployments():
        project_id = parse_uuid(request.args.get("project_id"), "project_id")
        status = request.args.get("status")
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(project_id=project_id, status=status, is_active=is_active)
        return json_ok([serialize_deployment(d) for d in items])

    @router.route("/", methods=["POST"])
    def create_deployment():
        body = get_json_body()
        inp = CreateDeploymentInput(
            project_id=require_uuid(body.get("project_id"), "project_id"),
            ai_application_ref=require_uuid(
                body.get("ai_application_ref"), "ai_application_ref"
            ),
            site_ref=require_uuid(body.get("site_ref"), "site_ref"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
        )
        deployment = service.create(inp)
        return json_created(serialize_deployment(deployment))

    @router.route("/<deployment_id>", methods=["GET"])
    def get_deployment(deployment_id: str):
        uid = require_uuid(deployment_id, "deployment_id")
        deployment = service.get(uid)
        return json_ok(serialize_deployment(deployment))

    @router.route("/<deployment_id>", methods=["PUT"])
    def update_deployment(deployment_id: str):
        uid = require_uuid(deployment_id, "deployment_id")
        body = get_json_body()
        inp = UpdateDeploymentInput(
            deployment_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            status=body.get("status"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            is_active=body.get("is_active"),
        )
        deployment = service.update(inp)
        return json_ok(serialize_deployment(deployment))

    @router.route("/<deployment_id>", methods=["DELETE"])
    def delete_deployment(deployment_id: str):
        uid = require_uuid(deployment_id, "deployment_id")
        service.delete(uid)
        return json_no_content()

    @router.route("/<deployment_id>/activate", methods=["POST"])
    def activate_deployment(deployment_id: str):
        uid = require_uuid(deployment_id, "deployment_id")
        body = get_json_body()
        expected_version = require_int(body.get("expected_version"), "expected_version")
        deployment = service.activate(uid, expected_version)
        return json_ok(serialize_deployment(deployment))

    @router.route("/<deployment_id>/deactivate", methods=["POST"])
    def deactivate_deployment(deployment_id: str):
        uid = require_uuid(deployment_id, "deployment_id")
        body = get_json_body()
        expected_version = require_int(body.get("expected_version"), "expected_version")
        deployment = service.deactivate(uid, expected_version)
        return json_ok(serialize_deployment(deployment))

    return router
