"""Smoke tests for camera configs, AI apps, models, rules, scene configs, users, feature flags."""
from __future__ import annotations

import json

from cv_platform.configuration.domain.exceptions import ConflictError, NotFoundError

from tests.configuration.api.conftest import (
    AI_APP_ID,
    CAMERA_CONFIG_ID,
    FEATURE_FLAG_ID,
    MODEL_ID,
    NOW,
    PROJECT_ID,
    RULE_ID,
    SCENE_CONFIG_ID,
    SITE_ID,
    USER_ID,
    make_ai_application,
    make_camera_config,
    make_feature_flag,
    make_model,
    make_rule,
    make_scene_config,
    make_user,
)


# ── CameraConfig ──────────────────────────────────────────────────────────────

class TestCameraConfigsApi:
    def test_list_returns_200(self, client, camera_config_svc):
        camera_config_svc.list.return_value = [make_camera_config()]
        resp = client.get("/api/v1/camera-configs/")
        assert resp.status_code == 200
        assert resp.get_json()[0]["object_type"] == "CameraConfig"

    def test_list_filters_by_site_id(self, client, camera_config_svc):
        camera_config_svc.list.return_value = []
        client.get(f"/api/v1/camera-configs/?site_id={SITE_ID}")
        camera_config_svc.list.assert_called_once_with(site_id=SITE_ID, is_active=None)

    def test_get_returns_200(self, client, camera_config_svc):
        camera_config_svc.get.return_value = make_camera_config()
        resp = client.get(f"/api/v1/camera-configs/{CAMERA_CONFIG_ID}")
        assert resp.status_code == 200
        assert resp.get_json()["parameters"]["site_id"] == str(SITE_ID)

    def test_get_returns_404(self, client, camera_config_svc):
        camera_config_svc.get.side_effect = NotFoundError("not found")
        assert client.get(f"/api/v1/camera-configs/{CAMERA_CONFIG_ID}").status_code == 404

    def test_create_returns_201(self, client, camera_config_svc):
        camera_config_svc.create.return_value = make_camera_config()
        resp = client.post(
            "/api/v1/camera-configs/",
            data=json.dumps({
                "site_id": str(SITE_ID),
                "name": "Cam 1",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["object_type"] == "CameraConfig"

    def test_delete_returns_409_when_has_scene_configs(self, client, camera_config_svc):
        camera_config_svc.delete.side_effect = ConflictError("has scene configs")
        assert client.delete(f"/api/v1/camera-configs/{CAMERA_CONFIG_ID}").status_code == 409


# ── AIApplication ─────────────────────────────────────────────────────────────

class TestAIApplicationsApi:
    def test_list_returns_200(self, client, ai_application_svc):
        ai_application_svc.list.return_value = [make_ai_application()]
        resp = client.get("/api/v1/ai-applications/")
        assert resp.status_code == 200
        assert resp.get_json()[0]["object_type"] == "AIApplication"

    def test_list_filters_by_project_id(self, client, ai_application_svc):
        ai_application_svc.list.return_value = []
        client.get(f"/api/v1/ai-applications/?project_id={PROJECT_ID}")
        ai_application_svc.list.assert_called_once_with(
            project_id=PROJECT_ID, is_active=None
        )

    def test_get_returns_200(self, client, ai_application_svc):
        ai_application_svc.get.return_value = make_ai_application()
        resp = client.get(f"/api/v1/ai-applications/{AI_APP_ID}")
        assert resp.status_code == 200
        assert resp.get_json()["parameters"]["project_id"] == str(PROJECT_ID)

    def test_create_returns_201(self, client, ai_application_svc):
        ai_application_svc.create.return_value = make_ai_application()
        resp = client.post(
            "/api/v1/ai-applications/",
            data=json.dumps({
                "project_id": str(PROJECT_ID),
                "name": "App",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201

    def test_delete_returns_409_when_has_active_deployments(
        self, client, ai_application_svc
    ):
        ai_application_svc.delete.side_effect = ConflictError("has active deployments")
        assert client.delete(f"/api/v1/ai-applications/{AI_APP_ID}").status_code == 409


# ── Model ─────────────────────────────────────────────────────────────────────

class TestModelsApi:
    def test_list_returns_200(self, client, model_svc):
        model_svc.list.return_value = [make_model()]
        resp = client.get("/api/v1/models/")
        assert resp.status_code == 200
        assert resp.get_json()[0]["object_type"] == "Model"

    def test_list_filters_by_ai_application_id(self, client, model_svc):
        model_svc.list.return_value = []
        client.get(f"/api/v1/models/?ai_application_id={AI_APP_ID}")
        model_svc.list.assert_called_once_with(
            ai_application_id=AI_APP_ID, is_active=None
        )

    def test_get_returns_200(self, client, model_svc):
        model_svc.get.return_value = make_model()
        resp = client.get(f"/api/v1/models/{MODEL_ID}")
        assert resp.status_code == 200
        assert resp.get_json()["parameters"]["ai_application_id"] == str(AI_APP_ID)

    def test_create_returns_201(self, client, model_svc):
        model_svc.create.return_value = make_model()
        resp = client.post(
            "/api/v1/models/",
            data=json.dumps({
                "ai_application_id": str(AI_APP_ID),
                "name": "YOLO v8",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
                "model_type": "detection",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201


# ── Rule ──────────────────────────────────────────────────────────────────────

class TestRulesApi:
    def test_list_returns_200(self, client, rule_svc):
        rule_svc.list.return_value = [make_rule()]
        resp = client.get("/api/v1/rules/")
        assert resp.status_code == 200
        assert resp.get_json()[0]["object_type"] == "Rule"

    def test_list_filters_by_ai_application_id(self, client, rule_svc):
        rule_svc.list.return_value = []
        client.get(f"/api/v1/rules/?ai_application_id={AI_APP_ID}")
        rule_svc.list.assert_called_once_with(
            ai_application_id=AI_APP_ID, is_active=None
        )

    def test_create_returns_201(self, client, rule_svc):
        rule_svc.create.return_value = make_rule()
        resp = client.post(
            "/api/v1/rules/",
            data=json.dumps({
                "ai_application_id": str(AI_APP_ID),
                "name": "Rule X",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201

    def test_get_returns_404(self, client, rule_svc):
        rule_svc.get.side_effect = NotFoundError("not found")
        assert client.get(f"/api/v1/rules/{RULE_ID}").status_code == 404


# ── SceneConfig ───────────────────────────────────────────────────────────────

class TestSceneConfigsApi:
    def test_list_returns_200(self, client, scene_config_svc):
        scene_config_svc.list.return_value = [make_scene_config()]
        resp = client.get("/api/v1/scene-configs/")
        assert resp.status_code == 200
        assert resp.get_json()[0]["object_type"] == "SceneConfig"

    def test_list_filters_by_camera_config_id(self, client, scene_config_svc):
        scene_config_svc.list.return_value = []
        client.get(f"/api/v1/scene-configs/?camera_config_id={CAMERA_CONFIG_ID}")
        scene_config_svc.list.assert_called_once_with(
            camera_config_id=CAMERA_CONFIG_ID, is_active=None
        )

    def test_create_returns_201(self, client, scene_config_svc):
        scene_config_svc.create.return_value = make_scene_config()
        resp = client.post(
            "/api/v1/scene-configs/",
            data=json.dumps({
                "camera_config_id": str(CAMERA_CONFIG_ID),
                "name": "Scene 1",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["parameters"]["camera_config_id"] == str(CAMERA_CONFIG_ID)


# ── User ──────────────────────────────────────────────────────────────────────

class TestUsersApi:
    def test_list_returns_200(self, client, user_svc):
        user_svc.list.return_value = [make_user()]
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 200
        assert resp.get_json()[0]["object_type"] == "User"

    def test_create_returns_201(self, client, user_svc):
        user_svc.create.return_value = make_user()
        resp = client.post(
            "/api/v1/users/",
            data=json.dumps({
                "username": "john",
                "email": "john@example.com",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["parameters"]["username"] == "john"

    def test_get_returns_404(self, client, user_svc):
        user_svc.get.side_effect = NotFoundError("not found")
        assert client.get(f"/api/v1/users/{USER_ID}").status_code == 404

    def test_create_returns_409_on_duplicate_username(self, client, user_svc):
        user_svc.create.side_effect = ConflictError("username taken")
        resp = client.post(
            "/api/v1/users/",
            data=json.dumps({
                "username": "john",
                "email": "john@example.com",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
            }),
            content_type="application/json",
        )
        assert resp.status_code == 409

    def test_user_response_excludes_internal_fields(self, client, user_svc):
        user_svc.get.return_value = make_user()
        data = client.get(f"/api/v1/users/{USER_ID}").get_json()
        # version and owner are at the root, not inside parameters
        assert "version" not in data["parameters"]
        assert "owner" not in data["parameters"]
        assert data["version"] == 1
        assert data["owner"] == "admin"

    def test_get_response_does_not_contain_password_hash(self, client, user_svc):
        user = make_user()
        user.password_hash = "bcrypt_hashed_value"
        user_svc.get.return_value = user
        resp = client.get(f"/api/v1/users/{USER_ID}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "password_hash" not in data
        assert "password_hash" not in data.get("parameters", {})


# ── FeatureFlag ───────────────────────────────────────────────────────────────

class TestFeatureFlagsApi:
    def test_list_returns_200(self, client, feature_flag_svc):
        feature_flag_svc.list.return_value = [make_feature_flag()]
        resp = client.get("/api/v1/feature-flags/")
        assert resp.status_code == 200
        assert resp.get_json()[0]["object_type"] == "FeatureFlag"

    def test_create_returns_201(self, client, feature_flag_svc):
        feature_flag_svc.create.return_value = make_feature_flag()
        resp = client.post(
            "/api/v1/feature-flags/",
            data=json.dumps({
                "name": "beta_feature",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
                "is_enabled": False,
                "target_type": "global",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201
        assert resp.get_json()["parameters"]["name"] == "beta_feature"

    def test_list_filters_by_target_type(self, client, feature_flag_svc):
        feature_flag_svc.list.return_value = []
        client.get("/api/v1/feature-flags/?target_type=project")
        feature_flag_svc.list.assert_called_once_with(
            target_type="project", target_id=None, is_active=None
        )

    def test_create_returns_409_on_duplicate(self, client, feature_flag_svc):
        feature_flag_svc.create.side_effect = ConflictError("already exists")
        resp = client.post(
            "/api/v1/feature-flags/",
            data=json.dumps({
                "name": "beta_feature",
                "owner": "admin",
                "effective_date": NOW.isoformat(),
            }),
            content_type="application/json",
        )
        assert resp.status_code == 409
