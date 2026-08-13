"""Tests for /api/v1/projects endpoints."""
from __future__ import annotations

import json

from cv_platform.configuration.domain.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)

from tests.configuration.api.conftest import (
    NOW,
    PROJECT_ID,
    make_project,
)


class TestListProjects:
    def test_returns_200_with_array(self, client, project_svc):
        project_svc.list.return_value = [make_project()]

        resp = client.get("/api/v1/projects/")

        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_response_is_configuration_object(self, client, project_svc):
        project_svc.list.return_value = [make_project()]

        data = client.get("/api/v1/projects/").get_json()
        obj = data[0]

        assert obj["object_type"] == "Project"
        assert obj["version"] == 1
        assert obj["owner"] == "test_owner"
        assert isinstance(obj["parameters"], dict)
        assert obj["parameters"]["name"] == "Test Project"
        assert obj["parameters"]["id"] == str(PROJECT_ID)
        assert isinstance(obj["validation"], dict)
        assert obj["validation"]["status"] == "active"
        assert obj["validation"]["is_active"] is True
        assert "effective_date" in obj

    def test_empty_list(self, client, project_svc):
        project_svc.list.return_value = []

        data = client.get("/api/v1/projects/").get_json()

        assert data == []

    def test_passes_is_active_filter(self, client, project_svc):
        project_svc.list.return_value = []

        client.get("/api/v1/projects/?is_active=true")

        project_svc.list.assert_called_once_with(is_active=True)

    def test_is_active_false_filter(self, client, project_svc):
        project_svc.list.return_value = []

        client.get("/api/v1/projects/?is_active=false")

        project_svc.list.assert_called_once_with(is_active=False)

    def test_no_filter_passes_none(self, client, project_svc):
        project_svc.list.return_value = []

        client.get("/api/v1/projects/")

        project_svc.list.assert_called_once_with(is_active=None)


class TestGetProject:
    def test_returns_200_with_configuration_object(self, client, project_svc):
        project_svc.get.return_value = make_project()

        resp = client.get(f"/api/v1/projects/{PROJECT_ID}")

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["object_type"] == "Project"
        assert data["parameters"]["id"] == str(PROJECT_ID)

    def test_returns_404_when_not_found(self, client, project_svc):
        project_svc.get.side_effect = NotFoundError("not found")

        resp = client.get(f"/api/v1/projects/{PROJECT_ID}")

        assert resp.status_code == 404
        assert "error" in resp.get_json()

    def test_returns_400_for_invalid_uuid(self, client, project_svc):
        resp = client.get("/api/v1/projects/not-a-uuid")

        assert resp.status_code == 400


class TestCreateProject:
    def _body(self, **overrides):
        base = {
            "name": "New Project",
            "owner": "owner1",
            "effective_date": NOW.isoformat(),
            "description": "A project",
            "status": "active",
        }
        base.update(overrides)
        return base

    def test_returns_201_with_configuration_object(self, client, project_svc):
        project_svc.create.return_value = make_project(name="New Project")

        resp = client.post(
            "/api/v1/projects/",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["object_type"] == "Project"

    def test_service_receives_correct_input(self, client, project_svc):
        project_svc.create.return_value = make_project()

        client.post(
            "/api/v1/projects/",
            data=json.dumps(self._body(name="Proj X", owner="ownerX")),
            content_type="application/json",
        )

        call_inp = project_svc.create.call_args[0][0]
        assert call_inp.name == "Proj X"
        assert call_inp.owner == "ownerX"

    def test_returns_400_for_validation_error(self, client, project_svc):
        project_svc.create.side_effect = ValidationError("name required")

        resp = client.post(
            "/api/v1/projects/",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_returns_400_for_missing_effective_date(self, client, project_svc):
        body = {"name": "X", "owner": "Y"}
        resp = client.post(
            "/api/v1/projects/",
            data=json.dumps(body),
            content_type="application/json",
        )

        assert resp.status_code == 400

    def test_returns_400_for_non_json_body(self, client, project_svc):
        resp = client.post(
            "/api/v1/projects/",
            data="not json",
            content_type="text/plain",
        )

        assert resp.status_code == 400


class TestUpdateProject:
    def _body(self, **overrides):
        base = {"expected_version": 1, "name": "Updated"}
        base.update(overrides)
        return base

    def test_returns_200_with_updated_object(self, client, project_svc):
        project_svc.update.return_value = make_project(name="Updated", version=2)

        resp = client.put(
            f"/api/v1/projects/{PROJECT_ID}",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert resp.get_json()["object_type"] == "Project"

    def test_returns_409_on_conflict(self, client, project_svc):
        project_svc.update.side_effect = ConflictError("conflict")

        resp = client.put(
            f"/api/v1/projects/{PROJECT_ID}",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 409

    def test_returns_400_when_expected_version_missing(self, client, project_svc):
        resp = client.put(
            f"/api/v1/projects/{PROJECT_ID}",
            data=json.dumps({"name": "X"}),
            content_type="application/json",
        )

        assert resp.status_code == 400

    def test_returns_400_when_expected_version_not_int(self, client, project_svc):
        resp = client.put(
            f"/api/v1/projects/{PROJECT_ID}",
            data=json.dumps({"expected_version": "one"}),
            content_type="application/json",
        )

        assert resp.status_code == 400

    def test_returns_404_when_not_found(self, client, project_svc):
        project_svc.update.side_effect = NotFoundError("not found")

        resp = client.put(
            f"/api/v1/projects/{PROJECT_ID}",
            data=json.dumps(self._body()),
            content_type="application/json",
        )

        assert resp.status_code == 404


class TestDeleteProject:
    def test_returns_204_on_success(self, client, project_svc):
        project_svc.delete.return_value = None

        resp = client.delete(f"/api/v1/projects/{PROJECT_ID}")

        assert resp.status_code == 204

    def test_returns_404_when_not_found(self, client, project_svc):
        project_svc.delete.side_effect = NotFoundError("not found")

        resp = client.delete(f"/api/v1/projects/{PROJECT_ID}")

        assert resp.status_code == 404

    def test_returns_409_on_conflict(self, client, project_svc):
        project_svc.delete.side_effect = ConflictError("has active deployments")

        resp = client.delete(f"/api/v1/projects/{PROJECT_ID}")

        assert resp.status_code == 409
