"""Shared fixtures for Configuration Platform API tests."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from cv_platform.configuration.api.app import create_configuration_app
from cv_platform.configuration.domain.models import (
    AIApplication,
    CameraConfig,
    Deployment,
    FeatureFlag,
    Model,
    Project,
    ProjectUser,
    Rule,
    SceneConfig,
    Site,
    User,
)
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

NOW = datetime(2026, 8, 12, tzinfo=timezone.utc)
PROJECT_ID = uuid4()
SITE_ID = uuid4()
CAMERA_CONFIG_ID = uuid4()
AI_APP_ID = uuid4()
MODEL_ID = uuid4()
RULE_ID = uuid4()
SCENE_CONFIG_ID = uuid4()
USER_ID = uuid4()
FEATURE_FLAG_ID = uuid4()
DEPLOYMENT_ID = uuid4()


def make_project(**kwargs) -> Project:
    defaults = dict(
        id=PROJECT_ID,
        name="Test Project",
        owner="test_owner",
        effective_date=NOW,
        description="desc",
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return Project(**defaults)


def make_site(**kwargs) -> Site:
    defaults = dict(
        id=SITE_ID,
        project_id=PROJECT_ID,
        name="Test Site",
        owner="test_owner",
        effective_date=NOW,
        location="Dhaka",
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return Site(**defaults)


def make_camera_config(**kwargs) -> CameraConfig:
    defaults = dict(
        id=CAMERA_CONFIG_ID,
        site_id=SITE_ID,
        name="Cam 1",
        owner="test_owner",
        effective_date=NOW,
        rtsp_url="rtsp://cam1",
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return CameraConfig(**defaults)


def make_ai_application(**kwargs) -> AIApplication:
    defaults = dict(
        id=AI_APP_ID,
        project_id=PROJECT_ID,
        name="Test App",
        owner="test_owner",
        effective_date=NOW,
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return AIApplication(**defaults)


def make_model(**kwargs) -> Model:
    defaults = dict(
        id=MODEL_ID,
        ai_application_id=AI_APP_ID,
        name="YOLO v8",
        owner="test_owner",
        effective_date=NOW,
        model_type="detection",
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return Model(**defaults)


def make_rule(**kwargs) -> Rule:
    defaults = dict(
        id=RULE_ID,
        ai_application_id=AI_APP_ID,
        name="Intrusion Rule",
        owner="test_owner",
        effective_date=NOW,
        rule_type="intrusion",
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return Rule(**defaults)


def make_scene_config(**kwargs) -> SceneConfig:
    defaults = dict(
        id=SCENE_CONFIG_ID,
        camera_config_id=CAMERA_CONFIG_ID,
        name="Scene 1",
        owner="test_owner",
        effective_date=NOW,
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return SceneConfig(**defaults)


def make_user(**kwargs) -> User:
    defaults = dict(
        id=USER_ID,
        username="john",
        email="john@example.com",
        owner="admin",
        effective_date=NOW,
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return User(**defaults)


def make_feature_flag(**kwargs) -> FeatureFlag:
    defaults = dict(
        id=FEATURE_FLAG_ID,
        name="beta_feature",
        owner="admin",
        effective_date=NOW,
        is_enabled=False,
        target_type="global",
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return FeatureFlag(**defaults)


def make_deployment(**kwargs) -> Deployment:
    defaults = dict(
        id=DEPLOYMENT_ID,
        project_id=PROJECT_ID,
        ai_application_ref=AI_APP_ID,
        site_ref=SITE_ID,
        ai_application_snapshot={"id": str(AI_APP_ID), "name": "Test App"},
        site_snapshot={"id": str(SITE_ID), "name": "Test Site"},
        owner="test_owner",
        effective_date=NOW,
        status="pending",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return Deployment(**defaults)


@pytest.fixture
def project_svc():
    return MagicMock(spec=ProjectService)


@pytest.fixture
def site_svc():
    return MagicMock(spec=SiteService)


@pytest.fixture
def camera_config_svc():
    return MagicMock(spec=CameraConfigService)


@pytest.fixture
def ai_application_svc():
    return MagicMock(spec=AIApplicationService)


@pytest.fixture
def model_svc():
    return MagicMock(spec=ModelService)


@pytest.fixture
def rule_svc():
    return MagicMock(spec=RuleService)


@pytest.fixture
def scene_config_svc():
    return MagicMock(spec=SceneConfigService)


@pytest.fixture
def user_svc():
    return MagicMock(spec=UserService)


@pytest.fixture
def feature_flag_svc():
    return MagicMock(spec=FeatureFlagService)


@pytest.fixture
def deployment_svc():
    return MagicMock(spec=DeploymentService)


@pytest.fixture
def app(
    project_svc,
    site_svc,
    camera_config_svc,
    ai_application_svc,
    model_svc,
    rule_svc,
    scene_config_svc,
    user_svc,
    feature_flag_svc,
    deployment_svc,
):
    flask_app = create_configuration_app(
        project_service=project_svc,
        site_service=site_svc,
        camera_config_service=camera_config_svc,
        ai_application_service=ai_application_svc,
        model_service=model_svc,
        rule_service=rule_svc,
        scene_config_service=scene_config_svc,
        user_service=user_svc,
        feature_flag_service=feature_flag_svc,
        deployment_service=deployment_svc,
        config={"TESTING": True, "PROPAGATE_EXCEPTIONS": False},
    )
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
