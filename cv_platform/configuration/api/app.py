from __future__ import annotations

from typing import Optional

from flask import Flask, request

from cv_platform.configuration.api.ai_applications import make_ai_applications_router
from cv_platform.configuration.api.camera_configs import make_camera_configs_router
from cv_platform.configuration.api.deployments import make_deployments_router
from cv_platform.configuration.api.feature_flags import make_feature_flags_router
from cv_platform.configuration.api.models import make_models_router
from cv_platform.configuration.api.projects import make_projects_router
from cv_platform.configuration.api.rules import make_rules_router
from cv_platform.configuration.api.scene_configs import make_scene_configs_router
from cv_platform.configuration.api.sites import make_sites_router
from cv_platform.configuration.api.users import make_users_router
from cv_platform.configuration.domain.exceptions import (
    ConflictError,
    NotFoundError,
    OptimisticLockError,
    ValidationError,
)
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
from cv_platform.shared.api_core import create_app

_ERROR_MAP: dict[type, int] = {
    ValidationError: 400,
    NotFoundError: 404,
    OptimisticLockError: 409,
    ConflictError: 409,
}

_AUTH_EXEMPT_PATHS = frozenset({"/health", "/api/v1/auth/token"})


def create_configuration_app(
    project_service: ProjectService,
    site_service: SiteService,
    camera_config_service: CameraConfigService,
    ai_application_service: AIApplicationService,
    model_service: ModelService,
    rule_service: RuleService,
    scene_config_service: SceneConfigService,
    user_service: UserService,
    feature_flag_service: FeatureFlagService,
    deployment_service: DeploymentService,
    user_repo: Optional[UserRepository] = None,
    config: dict | None = None,
) -> Flask:
    """Assemble the Configuration Platform Flask application."""
    routers = [
        make_projects_router(project_service),
        make_sites_router(site_service),
        make_camera_configs_router(camera_config_service),
        make_ai_applications_router(ai_application_service),
        make_models_router(model_service),
        make_rules_router(rule_service),
        make_scene_configs_router(scene_config_service),
        make_users_router(user_service),
        make_feature_flags_router(feature_flag_service),
        make_deployments_router(deployment_service),
    ]

    if user_repo is not None:
        from cv_platform.configuration.api.auth import make_auth_router
        from cv_platform.shared.auth._jwt import _get_secret
        from cv_platform.shared.auth._middleware import require_auth

        _get_secret()  # fail fast if SECRET_KEY is missing at startup
        routers.append(make_auth_router(user_repo))
        flask_app = create_app(routers, error_map=_ERROR_MAP, config=config)
        _auth_check = require_auth(lambda: None)

        @flask_app.before_request
        def _enforce_auth():
            if request.path in _AUTH_EXEMPT_PATHS:
                return
            return _auth_check()

        return flask_app

    return create_app(routers, error_map=_ERROR_MAP, config=config)
