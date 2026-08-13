"""Tests for /api/v1/deployments endpoints."""
from __future__ import annotations

import json

from cv_platform.configuration.domain.exceptions import ConflictError, NotFoundError

from tests.configuration.api.conftest import (
    AI_APP_ID,
    DEPLOYMENT_ID,
    NOW,
    PROJECT_ID,
    SITE_ID,
    make_deployment,
)


class TestListDeployments:
    def test_returns_200_with_array(self, client, deployment_svc):
        deployment_svc.list.return_value = [make_deployment()]

        resp = client.get("/api/v1/deployments/")

        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert data[0]["object_type"] == "Deployment"

    def test_filters_by_project_id(self, client, deployment_svc):
        deployment_svc.list.return_value = []

        client.get(f"/api/v1/deployments/?project_id={PROJECT_ID}")

        deployment_svc.list.assert_called_once_with(
            project_id=PROJECT_ID, status=None, is_active=None
        )

    def test_filters_by_status(self, client, deployment_svc):
        deployment_svc.list.return_value = []

        client.get("/api/v1/deployments/?status=active")

        deployment_svc.list.assert_called_once_with(
            project_id=None, status="active", is_active=None
        )

    def test_configuration_object_contains_snapshots(self, client, deployment_svc):
        deployment_svc.list.return_value = [make_deployment()]

        obj = client.get("/api/v1/deployments/").get_json()[0]

        assert "ai_application_snapshot" in obj["parameters"]
        assert "site_snapshot" in obj["parameters"]
        assert obj["validation"]["status"] == "pending"


class TestCreateDeployment:
    def _body(self):
        return {
            "project_id": str(PROJECT_ID),
            "ai_application_ref": str(AI_APP_ID),
            "site_ref": str(SITE_ID),
            "owner": "test_owner",
            "effective_date": NOW.isoformat(),
        }

    def test_returns_201(self, client, deployment_svc):
        deployment_svc.create.return_value = make_deployment()

        resp = client.post(
            "/api/v1/deployments/",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["object_type"] == "Deployment"
        assert data["validation"]["status"] == "pending"

    def test_returns_404_when_project_missing(self, client, deployment_svc):
        deployment_svc.create.side_effect = NotFoundError("Project not found")

        resp = client.post(
            "/api/v1/deployments/",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 404


class TestGetDeployment:
    def test_returns_200(self, client, deployment_svc):
        deployment_svc.get.return_value = make_deployment()

        resp = client.get(f"/api/v1/deployments/{DEPLOYMENT_ID}")

        assert resp.status_code == 200
        assert resp.get_json()["parameters"]["id"] == str(DEPLOYMENT_ID)

    def test_returns_404(self, client, deployment_svc):
        deployment_svc.get.side_effect = NotFoundError("not found")

        assert client.get(f"/api/v1/deployments/{DEPLOYMENT_ID}").status_code == 404


class TestDeleteDeployment:
    def test_returns_204(self, client, deployment_svc):
        deployment_svc.delete.return_value = None

        assert client.delete(f"/api/v1/deployments/{DEPLOYMENT_ID}").status_code == 204

    def test_returns_409_when_active(self, client, deployment_svc):
        deployment_svc.delete.side_effect = ConflictError("is active")

        assert client.delete(f"/api/v1/deployments/{DEPLOYMENT_ID}").status_code == 409


class TestActivateDeployment:
    def test_returns_200_with_active_status(self, client, deployment_svc):
        active = make_deployment(status="active", version=2)
        deployment_svc.activate.return_value = active

        resp = client.post(
            f"/api/v1/deployments/{DEPLOYMENT_ID}/activate",
            data=json.dumps({"expected_version": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert resp.get_json()["validation"]["status"] == "active"
        deployment_svc.activate.assert_called_once_with(DEPLOYMENT_ID, 1)

    def test_returns_409_when_already_active(self, client, deployment_svc):
        deployment_svc.activate.side_effect = ConflictError("already active")

        resp = client.post(
            f"/api/v1/deployments/{DEPLOYMENT_ID}/activate",
            data=json.dumps({"expected_version": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 409

    def test_returns_400_when_version_missing(self, client, deployment_svc):
        resp = client.post(
            f"/api/v1/deployments/{DEPLOYMENT_ID}/activate",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert resp.status_code == 400


class TestDeactivateDeployment:
    def test_returns_200_with_inactive_status(self, client, deployment_svc):
        inactive = make_deployment(status="inactive", is_active=False, version=2)
        deployment_svc.deactivate.return_value = inactive

        resp = client.post(
            f"/api/v1/deployments/{DEPLOYMENT_ID}/deactivate",
            data=json.dumps({"expected_version": 2}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert resp.get_json()["validation"]["status"] == "inactive"
        deployment_svc.deactivate.assert_called_once_with(DEPLOYMENT_ID, 2)

    def test_returns_409_when_not_active(self, client, deployment_svc):
        deployment_svc.deactivate.side_effect = ConflictError("not active")

        resp = client.post(
            f"/api/v1/deployments/{DEPLOYMENT_ID}/deactivate",
            data=json.dumps({"expected_version": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 409
