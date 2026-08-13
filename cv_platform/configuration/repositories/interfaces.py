"""Abstract repository interfaces for the Configuration Platform.

Concrete implementations live in the repository layer and depend on db-core.
Services depend only on these interfaces, keeping them testable without a database.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

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


class ProjectRepository(ABC):
    @abstractmethod
    def get(self, project_id: UUID) -> Optional[Project]: ...

    @abstractmethod
    def list(self, *, is_active: Optional[bool] = None) -> list[Project]: ...

    @abstractmethod
    def create(self, project: Project) -> Project: ...

    @abstractmethod
    def update(self, project: Project) -> Project: ...

    @abstractmethod
    def delete(self, project_id: UUID) -> None: ...


class SiteRepository(ABC):
    @abstractmethod
    def get(self, site_id: UUID) -> Optional[Site]: ...

    @abstractmethod
    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Site]: ...

    @abstractmethod
    def create(self, site: Site) -> Site: ...

    @abstractmethod
    def update(self, site: Site) -> Site: ...

    @abstractmethod
    def delete(self, site_id: UUID) -> None: ...


class CameraConfigRepository(ABC):
    @abstractmethod
    def get(self, camera_config_id: UUID) -> Optional[CameraConfig]: ...

    @abstractmethod
    def list(
        self,
        *,
        site_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[CameraConfig]: ...

    @abstractmethod
    def create(self, camera_config: CameraConfig) -> CameraConfig: ...

    @abstractmethod
    def update(self, camera_config: CameraConfig) -> CameraConfig: ...

    @abstractmethod
    def delete(self, camera_config_id: UUID) -> None: ...

    @abstractmethod
    def has_any_for_site(self, site_id: UUID) -> bool: ...


class AIApplicationRepository(ABC):
    @abstractmethod
    def get(self, ai_application_id: UUID) -> Optional[AIApplication]: ...

    @abstractmethod
    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[AIApplication]: ...

    @abstractmethod
    def create(self, ai_application: AIApplication) -> AIApplication: ...

    @abstractmethod
    def update(self, ai_application: AIApplication) -> AIApplication: ...

    @abstractmethod
    def delete(self, ai_application_id: UUID) -> None: ...


class ModelRepository(ABC):
    @abstractmethod
    def get(self, model_id: UUID) -> Optional[Model]: ...

    @abstractmethod
    def list(
        self,
        *,
        ai_application_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Model]: ...

    @abstractmethod
    def create(self, model: Model) -> Model: ...

    @abstractmethod
    def update(self, model: Model) -> Model: ...

    @abstractmethod
    def delete(self, model_id: UUID) -> None: ...


class RuleRepository(ABC):
    @abstractmethod
    def get(self, rule_id: UUID) -> Optional[Rule]: ...

    @abstractmethod
    def list(
        self,
        *,
        ai_application_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Rule]: ...

    @abstractmethod
    def create(self, rule: Rule) -> Rule: ...

    @abstractmethod
    def update(self, rule: Rule) -> Rule: ...

    @abstractmethod
    def delete(self, rule_id: UUID) -> None: ...


class SceneConfigRepository(ABC):
    @abstractmethod
    def get(self, scene_config_id: UUID) -> Optional[SceneConfig]: ...

    @abstractmethod
    def list(
        self,
        *,
        camera_config_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[SceneConfig]: ...

    @abstractmethod
    def create(self, scene_config: SceneConfig) -> SceneConfig: ...

    @abstractmethod
    def update(self, scene_config: SceneConfig) -> SceneConfig: ...

    @abstractmethod
    def delete(self, scene_config_id: UUID) -> None: ...

    @abstractmethod
    def has_any_for_camera_config(self, camera_config_id: UUID) -> bool: ...


class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: UUID) -> Optional[User]: ...

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def list(self, *, is_active: Optional[bool] = None) -> list[User]: ...

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def update(self, user: User) -> User: ...

    @abstractmethod
    def delete(self, user_id: UUID) -> None: ...

    @abstractmethod
    def get_project_memberships(self, project_id: UUID) -> list[ProjectUser]: ...

    @abstractmethod
    def add_project_membership(self, project_user: ProjectUser) -> ProjectUser: ...

    @abstractmethod
    def remove_project_membership(self, project_id: UUID, user_id: UUID) -> None: ...


class FeatureFlagRepository(ABC):
    @abstractmethod
    def get(self, feature_flag_id: UUID) -> Optional[FeatureFlag]: ...

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[FeatureFlag]: ...

    @abstractmethod
    def list(
        self,
        *,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[FeatureFlag]: ...

    @abstractmethod
    def create(self, feature_flag: FeatureFlag) -> FeatureFlag: ...

    @abstractmethod
    def update(self, feature_flag: FeatureFlag) -> FeatureFlag: ...

    @abstractmethod
    def delete(self, feature_flag_id: UUID) -> None: ...


class DeploymentRepository(ABC):
    @abstractmethod
    def get(self, deployment_id: UUID) -> Optional[Deployment]: ...

    @abstractmethod
    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Deployment]: ...

    @abstractmethod
    def create(self, deployment: Deployment) -> Deployment: ...

    @abstractmethod
    def update(self, deployment: Deployment) -> Deployment: ...

    @abstractmethod
    def delete(self, deployment_id: UUID) -> None: ...

    @abstractmethod
    def has_active_by_project(self, project_id: UUID) -> bool: ...

    @abstractmethod
    def has_active_by_ai_application(self, ai_application_id: UUID) -> bool: ...

    @abstractmethod
    def has_active_by_site(self, site_id: UUID) -> bool: ...
