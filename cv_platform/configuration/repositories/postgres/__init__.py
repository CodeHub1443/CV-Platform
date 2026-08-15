import psycopg2.extras

psycopg2.extras.register_uuid()

from cv_platform.configuration.repositories.postgres.ai_application_repo import PostgresAIApplicationRepository
from cv_platform.configuration.repositories.postgres.camera_config_repo import PostgresCameraConfigRepository
from cv_platform.configuration.repositories.postgres.deployment_repo import PostgresDeploymentRepository
from cv_platform.configuration.repositories.postgres.feature_flag_repo import PostgresFeatureFlagRepository
from cv_platform.configuration.repositories.postgres.model_repo import PostgresModelRepository
from cv_platform.configuration.repositories.postgres.project_repo import PostgresProjectRepository
from cv_platform.configuration.repositories.postgres.rule_repo import PostgresRuleRepository
from cv_platform.configuration.repositories.postgres.scene_config_repo import PostgresSceneConfigRepository
from cv_platform.configuration.repositories.postgres.site_repo import PostgresSiteRepository
from cv_platform.configuration.repositories.postgres.user_repo import PostgresUserRepository

__all__ = [
    "PostgresAIApplicationRepository",
    "PostgresCameraConfigRepository",
    "PostgresDeploymentRepository",
    "PostgresFeatureFlagRepository",
    "PostgresModelRepository",
    "PostgresProjectRepository",
    "PostgresRuleRepository",
    "PostgresSceneConfigRepository",
    "PostgresSiteRepository",
    "PostgresUserRepository",
]
