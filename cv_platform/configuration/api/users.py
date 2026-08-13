from __future__ import annotations

from flask import request

from cv_platform.configuration.api._parse import (
    parse_bool,
    parse_datetime,
    require_datetime,
    require_int,
    require_uuid,
)
from cv_platform.configuration.api._serializers import serialize_project_user, serialize_user
from cv_platform.configuration.services.user_service import (
    AddProjectMembershipInput,
    CreateUserInput,
    UpdateUserInput,
    UserService,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_users_router(service: UserService) -> Router:
    router = Router("users", "/api/v1/users")

    @router.route("/", methods=["GET"])
    def list_users():
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(is_active=is_active)
        return json_ok([serialize_user(u) for u in items])

    @router.route("/", methods=["POST"])
    def create_user():
        body = get_json_body()
        inp = CreateUserInput(
            username=body.get("username"),
            email=body.get("email"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            status=body.get("status", "active"),
        )
        user = service.create(inp)
        return json_created(serialize_user(user))

    @router.route("/<user_id>", methods=["GET"])
    def get_user(user_id: str):
        uid = require_uuid(user_id, "user_id")
        user = service.get(uid)
        return json_ok(serialize_user(user))

    @router.route("/<user_id>", methods=["PUT"])
    def update_user(user_id: str):
        uid = require_uuid(user_id, "user_id")
        body = get_json_body()
        inp = UpdateUserInput(
            user_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            username=body.get("username"),
            email=body.get("email"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        user = service.update(inp)
        return json_ok(serialize_user(user))

    @router.route("/<user_id>", methods=["DELETE"])
    def delete_user(user_id: str):
        uid = require_uuid(user_id, "user_id")
        service.delete(uid)
        return json_no_content()

    @router.route("/memberships", methods=["GET"])
    def list_project_members():
        project_id = require_uuid(request.args.get("project_id"), "project_id")
        memberships = service.get_project_memberships(project_id)
        return json_ok([serialize_project_user(m) for m in memberships])

    @router.route("/<user_id>/memberships", methods=["POST"])
    def add_user_membership(user_id: str):
        uid = require_uuid(user_id, "user_id")
        body = get_json_body()
        inp = AddProjectMembershipInput(
            project_id=require_uuid(body.get("project_id"), "project_id"),
            user_id=uid,
            role=body.get("role"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
        )
        membership = service.add_project_membership(inp)
        return json_created(serialize_project_user(membership))

    @router.route("/<user_id>/memberships/<project_id>", methods=["DELETE"])
    def remove_user_membership(user_id: str, project_id: str):
        uid = require_uuid(user_id, "user_id")
        pid = require_uuid(project_id, "project_id")
        service.remove_project_membership(pid, uid)
        return json_no_content()

    return router
