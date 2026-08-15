"""Integration tests for JWT authentication on the Configuration Platform."""
from __future__ import annotations

import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import bcrypt
import jwt as pyjwt
import pytest

from cv_platform.configuration.api.app import create_configuration_app
from cv_platform.configuration.domain.models import User
from cv_platform.configuration.repositories.interfaces import UserRepository
from cv_platform.configuration.services.ai_application_service import AIApplicationService
from cv_platform.configuration.services.camera_config_service import CameraConfigService
from cv_platform.configuration.services.deployment_service import DeploymentService
from cv_platform.configuration.services.feature_flag_service import FeatureFlagService
from cv_platform.configuration.services.model_service import ModelService
from cv_platform.configuration.services.project_service import ProjectService
from cv_platform.configuration.services.rule_service import RuleService
from cv_platform.configuration.services.scene_config_service import SceneConfigService
from cv_platform.configuration.services.site_service import SiteService
from cv_platform.configuration.services.user_service import UserService

TEST_SECRET = "integration-test-secret"
TEST_USER_ID = uuid4()
TEST_PASSWORD = "s3cr3tpassword"
TEST_PASSWORD_HASH = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()

NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def _make_test_user(**kwargs) -> User:
    defaults = dict(
        id=TEST_USER_ID,
        username="alice",
        email="alice@example.com",
        owner="admin",
        effective_date=NOW,
        password_hash=TEST_PASSWORD_HASH,
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return User(**defaults)


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)


@pytest.fixture
def user_repo():
    repo = MagicMock(spec=UserRepository)
    repo.get_by_username.return_value = _make_test_user()
    return repo


@pytest.fixture
def project_svc():
    svc = MagicMock(spec=ProjectService)
    svc.list.return_value = []
    return svc


@pytest.fixture
def auth_app(user_repo, project_svc):
    flask_app = create_configuration_app(
        project_service=project_svc,
        site_service=MagicMock(spec=SiteService),
        camera_config_service=MagicMock(spec=CameraConfigService),
        ai_application_service=MagicMock(spec=AIApplicationService),
        model_service=MagicMock(spec=ModelService),
        rule_service=MagicMock(spec=RuleService),
        scene_config_service=MagicMock(spec=SceneConfigService),
        user_service=MagicMock(spec=UserService),
        feature_flag_service=MagicMock(spec=FeatureFlagService),
        deployment_service=MagicMock(spec=DeploymentService),
        user_repo=user_repo,
        config={"TESTING": True, "PROPAGATE_EXCEPTIONS": False},
    )
    return flask_app


@pytest.fixture
def client(auth_app):
    return auth_app.test_client()


def _valid_token() -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {
        "user_id": str(TEST_USER_ID),
        "roles": [],
        "iat": now,
        "exp": now + datetime.timedelta(hours=1),
    }
    return pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")


def _expired_token() -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {
        "user_id": str(TEST_USER_ID),
        "roles": [],
        "iat": now - datetime.timedelta(hours=2),
        "exp": now - datetime.timedelta(hours=1),
    }
    return pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# POST /api/v1/auth/token
# ---------------------------------------------------------------------------


def test_token_valid_credentials_returns_200_with_token(client):
    resp = client.post(
        "/api/v1/auth/token",
        json={"username": "alice", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "token" in data
    payload = pyjwt.decode(data["token"], TEST_SECRET, algorithms=["HS256"])
    assert payload["user_id"] == str(TEST_USER_ID)
    assert "roles" in payload


def test_token_wrong_password_returns_401(client):
    resp = client.post(
        "/api/v1/auth/token",
        json={"username": "alice", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_token_unknown_user_returns_401(client, user_repo):
    user_repo.get_by_username.return_value = None
    resp = client.post(
        "/api/v1/auth/token",
        json={"username": "nobody", "password": "anything"},
    )
    assert resp.status_code == 401


def test_token_missing_fields_returns_400(client):
    resp = client.post("/api/v1/auth/token", json={"username": "alice"})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------


def test_protected_route_with_valid_token_returns_200(client):
    resp = client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {_valid_token()}"},
    )
    assert resp.status_code == 200


def test_protected_route_without_token_returns_401(client):
    resp = client.get("/api/v1/projects/")
    assert resp.status_code == 401


def test_protected_route_with_expired_token_returns_401(client):
    resp = client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {_expired_token()}"},
    )
    assert resp.status_code == 401


def test_protected_route_with_malformed_token_returns_401(client):
    resp = client.get(
        "/api/v1/projects/",
        headers={"Authorization": "Bearer totally-not-a-jwt"},
    )
    assert resp.status_code == 401


def test_auth_token_endpoint_exempt_from_bearer_requirement(client):
    resp = client.post(
        "/api/v1/auth/token",
        json={"username": "alice", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------


def test_missing_secret_key_raises_at_startup(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_configuration_app(
            project_service=MagicMock(spec=ProjectService),
            site_service=MagicMock(spec=SiteService),
            camera_config_service=MagicMock(spec=CameraConfigService),
            ai_application_service=MagicMock(spec=AIApplicationService),
            model_service=MagicMock(spec=ModelService),
            rule_service=MagicMock(spec=RuleService),
            scene_config_service=MagicMock(spec=SceneConfigService),
            user_service=MagicMock(spec=UserService),
            feature_flag_service=MagicMock(spec=FeatureFlagService),
            deployment_service=MagicMock(spec=DeploymentService),
            user_repo=MagicMock(spec=UserRepository),
        )
