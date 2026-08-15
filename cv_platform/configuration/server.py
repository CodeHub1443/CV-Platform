"""Configuration Platform server bootstrap and composition root.

Reads DATABASE_URL from the environment, initialises the connection pool,
wires all repositories and services, and produces a WSGI application.

Gunicorn entry point: cv_platform.configuration.server:app
"""
from __future__ import annotations

import atexit
import os
from typing import Optional
from uuid import UUID

import psycopg2.extensions
from flask import Flask, g

from cv_platform.configuration.api.app import create_configuration_app
from cv_platform.configuration.api.health import make_health_blueprint
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
from cv_platform.configuration.repositories.interfaces import (
    AIApplicationRepository,
    CameraConfigRepository,
    DeploymentRepository,
    FeatureFlagRepository,
    ModelRepository,
    ProjectRepository,
    RuleRepository,
    SceneConfigRepository,
    SiteRepository,
    UserRepository,
)
from cv_platform.configuration.repositories.postgres import (
    PostgresAIApplicationRepository,
    PostgresCameraConfigRepository,
    PostgresDeploymentRepository,
    PostgresFeatureFlagRepository,
    PostgresModelRepository,
    PostgresProjectRepository,
    PostgresRuleRepository,
    PostgresSceneConfigRepository,
    PostgresSiteRepository,
    PostgresUserRepository,
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
from cv_platform.shared.db_core import init_db
from cv_platform.shared.db_core._pool import get_pool


# ---------------------------------------------------------------------------
# Per-request connection accessor
# ---------------------------------------------------------------------------

def _get_conn():
    """Return the psycopg2 connection bound to the current Flask request."""
    return g._db_conn


# ---------------------------------------------------------------------------
# Session-bound repository wrappers
# Each method delegates to the corresponding Postgres repository using the
# connection that was opened at the start of the current request.
# ---------------------------------------------------------------------------

class _ProjectRepo(ProjectRepository):
    def get(self, project_id: UUID) -> Optional[Project]:
        return PostgresProjectRepository(_get_conn()).get(project_id)

    def list(self, *, is_active: Optional[bool] = None) -> list[Project]:
        return PostgresProjectRepository(_get_conn()).list(is_active=is_active)

    def create(self, project: Project) -> Project:
        return PostgresProjectRepository(_get_conn()).create(project)

    def update(self, project: Project) -> Project:
        return PostgresProjectRepository(_get_conn()).update(project)

    def delete(self, project_id: UUID) -> None:
        PostgresProjectRepository(_get_conn()).delete(project_id)


class _SiteRepo(SiteRepository):
    def get(self, site_id: UUID) -> Optional[Site]:
        return PostgresSiteRepository(_get_conn()).get(site_id)

    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Site]:
        return PostgresSiteRepository(_get_conn()).list(
            project_id=project_id, is_active=is_active
        )

    def create(self, site: Site) -> Site:
        return PostgresSiteRepository(_get_conn()).create(site)

    def update(self, site: Site) -> Site:
        return PostgresSiteRepository(_get_conn()).update(site)

    def delete(self, site_id: UUID) -> None:
        PostgresSiteRepository(_get_conn()).delete(site_id)


class _CameraConfigRepo(CameraConfigRepository):
    def get(self, camera_config_id: UUID) -> Optional[CameraConfig]:
        return PostgresCameraConfigRepository(_get_conn()).get(camera_config_id)

    def list(
        self,
        *,
        site_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[CameraConfig]:
        return PostgresCameraConfigRepository(_get_conn()).list(
            site_id=site_id, is_active=is_active
        )

    def create(self, camera_config: CameraConfig) -> CameraConfig:
        return PostgresCameraConfigRepository(_get_conn()).create(camera_config)

    def update(self, camera_config: CameraConfig) -> CameraConfig:
        return PostgresCameraConfigRepository(_get_conn()).update(camera_config)

    def delete(self, camera_config_id: UUID) -> None:
        PostgresCameraConfigRepository(_get_conn()).delete(camera_config_id)

    def has_any_for_site(self, site_id: UUID) -> bool:
        return PostgresCameraConfigRepository(_get_conn()).has_any_for_site(site_id)


class _AIApplicationRepo(AIApplicationRepository):
    def get(self, ai_application_id: UUID) -> Optional[AIApplication]:
        return PostgresAIApplicationRepository(_get_conn()).get(ai_application_id)

    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[AIApplication]:
        return PostgresAIApplicationRepository(_get_conn()).list(
            project_id=project_id, is_active=is_active
        )

    def create(self, ai_application: AIApplication) -> AIApplication:
        return PostgresAIApplicationRepository(_get_conn()).create(ai_application)

    def update(self, ai_application: AIApplication) -> AIApplication:
        return PostgresAIApplicationRepository(_get_conn()).update(ai_application)

    def delete(self, ai_application_id: UUID) -> None:
        PostgresAIApplicationRepository(_get_conn()).delete(ai_application_id)


class _ModelRepo(ModelRepository):
    def get(self, model_id: UUID) -> Optional[Model]:
        return PostgresModelRepository(_get_conn()).get(model_id)

    def list(
        self,
        *,
        ai_application_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Model]:
        return PostgresModelRepository(_get_conn()).list(
            ai_application_id=ai_application_id, is_active=is_active
        )

    def create(self, model: Model) -> Model:
        return PostgresModelRepository(_get_conn()).create(model)

    def update(self, model: Model) -> Model:
        return PostgresModelRepository(_get_conn()).update(model)

    def delete(self, model_id: UUID) -> None:
        PostgresModelRepository(_get_conn()).delete(model_id)


class _RuleRepo(RuleRepository):
    def get(self, rule_id: UUID) -> Optional[Rule]:
        return PostgresRuleRepository(_get_conn()).get(rule_id)

    def list(
        self,
        *,
        ai_application_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Rule]:
        return PostgresRuleRepository(_get_conn()).list(
            ai_application_id=ai_application_id, is_active=is_active
        )

    def create(self, rule: Rule) -> Rule:
        return PostgresRuleRepository(_get_conn()).create(rule)

    def update(self, rule: Rule) -> Rule:
        return PostgresRuleRepository(_get_conn()).update(rule)

    def delete(self, rule_id: UUID) -> None:
        PostgresRuleRepository(_get_conn()).delete(rule_id)


class _SceneConfigRepo(SceneConfigRepository):
    def get(self, scene_config_id: UUID) -> Optional[SceneConfig]:
        return PostgresSceneConfigRepository(_get_conn()).get(scene_config_id)

    def list(
        self,
        *,
        camera_config_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[SceneConfig]:
        return PostgresSceneConfigRepository(_get_conn()).list(
            camera_config_id=camera_config_id, is_active=is_active
        )

    def create(self, scene_config: SceneConfig) -> SceneConfig:
        return PostgresSceneConfigRepository(_get_conn()).create(scene_config)

    def update(self, scene_config: SceneConfig) -> SceneConfig:
        return PostgresSceneConfigRepository(_get_conn()).update(scene_config)

    def delete(self, scene_config_id: UUID) -> None:
        PostgresSceneConfigRepository(_get_conn()).delete(scene_config_id)

    def has_any_for_camera_config(self, camera_config_id: UUID) -> bool:
        return PostgresSceneConfigRepository(_get_conn()).has_any_for_camera_config(
            camera_config_id
        )


class _UserRepo(UserRepository):
    def get(self, user_id: UUID) -> Optional[User]:
        return PostgresUserRepository(_get_conn()).get(user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return PostgresUserRepository(_get_conn()).get_by_username(username)

    def get_by_email(self, email: str) -> Optional[User]:
        return PostgresUserRepository(_get_conn()).get_by_email(email)

    def list(self, *, is_active: Optional[bool] = None) -> list[User]:
        return PostgresUserRepository(_get_conn()).list(is_active=is_active)

    def create(self, user: User) -> User:
        return PostgresUserRepository(_get_conn()).create(user)

    def update(self, user: User) -> User:
        return PostgresUserRepository(_get_conn()).update(user)

    def delete(self, user_id: UUID) -> None:
        PostgresUserRepository(_get_conn()).delete(user_id)

    def get_project_memberships(self, project_id: UUID) -> list[ProjectUser]:
        return PostgresUserRepository(_get_conn()).get_project_memberships(project_id)

    def add_project_membership(self, project_user: ProjectUser) -> ProjectUser:
        return PostgresUserRepository(_get_conn()).add_project_membership(project_user)

    def remove_project_membership(self, project_id: UUID, user_id: UUID) -> None:
        PostgresUserRepository(_get_conn()).remove_project_membership(project_id, user_id)


class _FeatureFlagRepo(FeatureFlagRepository):
    def get(self, feature_flag_id: UUID) -> Optional[FeatureFlag]:
        return PostgresFeatureFlagRepository(_get_conn()).get(feature_flag_id)

    def get_by_name(self, name: str) -> Optional[FeatureFlag]:
        return PostgresFeatureFlagRepository(_get_conn()).get_by_name(name)

    def list(
        self,
        *,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[FeatureFlag]:
        return PostgresFeatureFlagRepository(_get_conn()).list(
            target_type=target_type, target_id=target_id, is_active=is_active
        )

    def create(self, feature_flag: FeatureFlag) -> FeatureFlag:
        return PostgresFeatureFlagRepository(_get_conn()).create(feature_flag)

    def update(self, feature_flag: FeatureFlag) -> FeatureFlag:
        return PostgresFeatureFlagRepository(_get_conn()).update(feature_flag)

    def delete(self, feature_flag_id: UUID) -> None:
        PostgresFeatureFlagRepository(_get_conn()).delete(feature_flag_id)


class _DeploymentRepo(DeploymentRepository):
    def get(self, deployment_id: UUID) -> Optional[Deployment]:
        return PostgresDeploymentRepository(_get_conn()).get(deployment_id)

    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Deployment]:
        return PostgresDeploymentRepository(_get_conn()).list(
            project_id=project_id, status=status, is_active=is_active
        )

    def create(self, deployment: Deployment) -> Deployment:
        return PostgresDeploymentRepository(_get_conn()).create(deployment)

    def update(self, deployment: Deployment) -> Deployment:
        return PostgresDeploymentRepository(_get_conn()).update(deployment)

    def delete(self, deployment_id: UUID) -> None:
        PostgresDeploymentRepository(_get_conn()).delete(deployment_id)

    def has_active_by_project(self, project_id: UUID) -> bool:
        return PostgresDeploymentRepository(_get_conn()).has_active_by_project(project_id)

    def has_active_by_ai_application(self, ai_application_id: UUID) -> bool:
        return PostgresDeploymentRepository(_get_conn()).has_active_by_ai_application(
            ai_application_id
        )

    def has_active_by_site(self, site_id: UUID) -> bool:
        return PostgresDeploymentRepository(_get_conn()).has_active_by_site(site_id)


# ---------------------------------------------------------------------------
# Pool teardown
# ---------------------------------------------------------------------------

def _close_pool() -> None:
    try:
        get_pool().closeall()
    except RuntimeError:
        pass  # pool was never initialised


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def _build_app() -> Flask:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Set it before starting the server."
        )

    init_db(db_url)

    # Instantiate singleton repository wrappers
    project_repo = _ProjectRepo()
    site_repo = _SiteRepo()
    camera_config_repo = _CameraConfigRepo()
    ai_application_repo = _AIApplicationRepo()
    model_repo = _ModelRepo()
    rule_repo = _RuleRepo()
    scene_config_repo = _SceneConfigRepo()
    user_repo = _UserRepo()
    feature_flag_repo = _FeatureFlagRepo()
    deployment_repo = _DeploymentRepo()

    # Wire up services
    project_service = ProjectService(project_repo, deployment_repo)
    site_service = SiteService(site_repo, project_repo, camera_config_repo)
    camera_config_service = CameraConfigService(
        camera_config_repo, site_repo, scene_config_repo
    )
    ai_application_service = AIApplicationService(
        ai_application_repo, project_repo, deployment_repo
    )
    model_service = ModelService(model_repo, ai_application_repo)
    rule_service = RuleService(rule_repo, ai_application_repo)
    scene_config_service = SceneConfigService(scene_config_repo, camera_config_repo)
    user_service = UserService(user_repo)
    feature_flag_service = FeatureFlagService(feature_flag_repo)
    deployment_service = DeploymentService(
        deployment_repo,
        project_repo,
        ai_application_repo,
        model_repo,
        rule_repo,
        site_repo,
        camera_config_repo,
        scene_config_repo,
    )

    flask_app = create_configuration_app(
        project_service=project_service,
        site_service=site_service,
        camera_config_service=camera_config_service,
        ai_application_service=ai_application_service,
        model_service=model_service,
        rule_service=rule_service,
        scene_config_service=scene_config_service,
        user_service=user_service,
        feature_flag_service=feature_flag_service,
        deployment_service=deployment_service,
    )

    flask_app.register_blueprint(make_health_blueprint())

    @flask_app.before_request
    def _open_db():
        from flask import request as _req
        if _req.path == "/health":
            return  # health endpoint does not need a DB connection
        conn = get_pool().getconn()
        conn.autocommit = False
        g._db_conn = conn

    @flask_app.teardown_request
    def _close_db(exc):
        conn = g.pop("_db_conn", None)
        if conn is None:
            return
        try:
            txn_status = conn.get_transaction_status()
            if txn_status == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                conn.rollback()
            elif txn_status == psycopg2.extensions.TRANSACTION_STATUS_INTRANS:
                conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            get_pool().putconn(conn)

    atexit.register(_close_pool)

    return flask_app


# ---------------------------------------------------------------------------
# WSGI entry point
# Gunicorn: gunicorn cv_platform.configuration.server:app
# ---------------------------------------------------------------------------

app: Flask = _build_app()
