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
from cv_platform.configuration.api._serializers import serialize_site
from cv_platform.configuration.services.site_service import (
    CreateSiteInput,
    SiteService,
    UpdateSiteInput,
)
from cv_platform.shared.api_core import (
    Router,
    get_json_body,
    json_created,
    json_no_content,
    json_ok,
)


def make_sites_router(service: SiteService) -> Router:
    router = Router("sites", "/api/v1/sites")

    @router.route("/", methods=["GET"])
    def list_sites():
        project_id = parse_uuid(request.args.get("project_id"), "project_id")
        is_active = parse_bool(request.args.get("is_active"))
        items = service.list(project_id=project_id, is_active=is_active)
        return json_ok([serialize_site(s) for s in items])

    @router.route("/", methods=["POST"])
    def create_site():
        body = get_json_body()
        inp = CreateSiteInput(
            project_id=require_uuid(body.get("project_id"), "project_id"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=require_datetime(body.get("effective_date"), "effective_date"),
            location=body.get("location"),
            status=body.get("status", "active"),
        )
        site = service.create(inp)
        return json_created(serialize_site(site))

    @router.route("/<site_id>", methods=["GET"])
    def get_site(site_id: str):
        uid = require_uuid(site_id, "site_id")
        site = service.get(uid)
        return json_ok(serialize_site(site))

    @router.route("/<site_id>", methods=["PUT"])
    def update_site(site_id: str):
        uid = require_uuid(site_id, "site_id")
        body = get_json_body()
        inp = UpdateSiteInput(
            site_id=uid,
            expected_version=require_int(body.get("expected_version"), "expected_version"),
            name=body.get("name"),
            owner=body.get("owner"),
            effective_date=parse_datetime(body.get("effective_date"), "effective_date"),
            location=body.get("location"),
            status=body.get("status"),
            is_active=body.get("is_active"),
        )
        site = service.update(inp)
        return json_ok(serialize_site(site))

    @router.route("/<site_id>", methods=["DELETE"])
    def delete_site(site_id: str):
        uid = require_uuid(site_id, "site_id")
        service.delete(uid)
        return json_no_content()

    return router
