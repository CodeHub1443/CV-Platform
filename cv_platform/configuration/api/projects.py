from __future__ import annotations

from flask import request

from cv_platform.configuration.api._parse import (
    parse_bool,
    parse_datetime,
    require_datetime,
    require_int,
    require_uuid,
)
from cv_platform.configuration.api._serializers import serialize_project
from cv_platform.configuration.services.project_service import (
    CreateProjectInput,
    ProjectService,
    UpdateProjectInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_projects_router(service: ProjectService) -> Router:
    router = Router("projects", "/api/v1/projects")

    @router.route("/", methods=["GET"])
    def list_projects():
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(is_active=is_active)
        return json_ok([serialize_project(p) for p in items])

    @router.route("/", methods=["POST"])
    def create_project():
        body = get_json_body()
        inp = CreateProjectInput(
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            description=body.get("description"),
            status=body.get("status", "active"),
        )
        project = service.create(inp)
        return json_created(serialize_project(project))

    @router.route("/<project_id>", methods=["GET"])
    def get_project(project_id: str):
        uid = require_uuid(project_id, "project_id")
        project = service.get(uid)
        return json_ok(serialize_project(project))

    @router.route("/<project_id>", methods=["PUT"])
    def update_project(project_id: str):
        uid = require_uuid(project_id, "project_id")
        body = get_json_body()
        inp = UpdateProjectInput(
            project_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            description=body.get("description"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        project = service.update(inp)
        return json_ok(serialize_project(project))

    @router.route("/<project_id>", methods=["DELETE"])
    def delete_project(project_id: str):
        uid = require_uuid(project_id, "project_id")
        service.delete(uid)
        return json_no_content()

    return router
