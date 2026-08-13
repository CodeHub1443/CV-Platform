"""Tests for /api/v1/sites endpoints."""
from __future__ import annotations

import json

from cv_platform.configuration.domain.exceptions import ConflictError, NotFoundError

from tests.configuration.api.conftest import (
    NOW,
    PROJECT_ID,
    SITE_ID,
    make_site,
)


class TestListSites:
    def test_returns_200_with_array(self, client, site_svc):
        site_svc.list.return_value = [make_site()]

        resp = client.get("/api/v1/sites/")

        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_configuration_object_shape(self, client, site_svc):
        site_svc.list.return_value = [make_site()]

        obj = client.get("/api/v1/sites/").get_json()[0]

        assert obj["object_type"] == "Site"
        assert obj["parameters"]["project_id"] == str(PROJECT_ID)
        assert obj["parameters"]["name"] == "Test Site"
        assert obj["validation"]["status"] == "active"

    def test_filters_by_project_id(self, client, site_svc):
        site_svc.list.return_value = []

        client.get(f"/api/v1/sites/?project_id={PROJECT_ID}")

        site_svc.list.assert_called_once_with(project_id=PROJECT_ID, is_active=None)

    def test_no_filter_passes_none_project_id(self, client, site_svc):
        site_svc.list.return_value = []

        client.get("/api/v1/sites/")

        site_svc.list.assert_called_once_with(project_id=None, is_active=None)

    def test_invalid_project_id_returns_400(self, client, site_svc):
        resp = client.get("/api/v1/sites/?project_id=not-a-uuid")

        assert resp.status_code == 400


class TestCreateSite:
    def _body(self, **overrides):
        base = {
            "project_id": str(PROJECT_ID),
            "name": "Site A",
            "owner": "owner1",
            "effective_date": NOW.isoformat(),
            "status": "active",
        }
        base.update(overrides)
        return base

    def test_returns_201(self, client, site_svc):
        site_svc.create.return_value = make_site()

        resp = client.post(
            "/api/v1/sites/",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 201
        assert resp.get_json()["object_type"] == "Site"

    def test_returns_404_when_project_missing(self, client, site_svc):
        site_svc.create.side_effect = NotFoundError("Project not found")

        resp = client.post(
            "/api/v1/sites/",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 404

    def test_returns_409_when_project_inactive(self, client, site_svc):
        site_svc.create.side_effect = ConflictError("project not active")

        resp = client.post(
            "/api/v1/sites/",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 409


class TestGetSite:
    def test_returns_200(self, client, site_svc):
        site_svc.get.return_value = make_site()

        resp = client.get(f"/api/v1/sites/{SITE_ID}")

        assert resp.status_code == 200
        assert resp.get_json()["parameters"]["id"] == str(SITE_ID)

    def test_returns_404(self, client, site_svc):
        site_svc.get.side_effect = NotFoundError("not found")

        assert client.get(f"/api/v1/sites/{SITE_ID}").status_code == 404


class TestDeleteSite:
    def test_returns_204(self, client, site_svc):
        site_svc.delete.return_value = None

        assert client.delete(f"/api/v1/sites/{SITE_ID}").status_code == 204

    def test_returns_409_when_has_cameras(self, client, site_svc):
        site_svc.delete.side_effect = ConflictError("has camera configs")

        assert client.delete(f"/api/v1/sites/{SITE_ID}").status_code == 409
