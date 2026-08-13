from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from cv_platform.configuration.domain.exceptions import (
    ConflictError,
    NotFoundError,
    OptimisticLockError,
    ValidationError,
)
from cv_platform.configuration.domain.models import Deployment
from cv_platform.configuration.repositories.interfaces import (
    AIApplicationRepository,
    CameraConfigRepository,
    DeploymentRepository,
    ModelRepository,
    ProjectRepository,
    RuleRepository,
    SceneConfigRepository,
    SiteRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_deployment_status,
)


def _entity_to_dict(obj: Any) -> dict[str, Any]:
    """Serialize a domain dataclass to a JSON-serializable dict for JSONB snapshots."""
    from dataclasses import fields as dc_fields

    result: dict[str, Any] = {}
    for f in dc_fields(obj):
        value = getattr(obj, f.name)
        if isinstance(value, UUID):
            result[f.name] = str(value)
        elif isinstance(value, datetime):
            result[f.name] = value.isoformat()
        else:
            result[f.name] = value
    return result


@dataclass
class CreateDeploymentInput:
    project_id: UUID
    ai_application_ref: UUID
    site_ref: UUID
    owner: str
    effective_date: datetime


@dataclass
class UpdateDeploymentInput:
    deployment_id: UUID
    expected_version: int
    status: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class DeploymentService:
    """
    Coordinates cross-entity rules for Deployment lifecycle.

    On creation it assembles immutable snapshots of the full AI application tree
    (models + rules) and the full site tree (camera configs + scene configs) so that
    active deployments are isolated from upstream configuration changes.
    """

    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        project_repo: ProjectRepository,
        ai_application_repo: AIApplicationRepository,
        model_repo: ModelRepository,
        rule_repo: RuleRepository,
        site_repo: SiteRepository,
        camera_config_repo: CameraConfigRepository,
        scene_config_repo: SceneConfigRepository,
    ) -> None:
        self._deployments = deployment_repo
        self._projects = project_repo
        self._ai_applications = ai_application_repo
        self._models = model_repo
        self._rules = rule_repo
        self._sites = site_repo
        self._camera_configs = camera_config_repo
        self._scene_configs = scene_config_repo

    # ------------------------------------------------------------------
    # Snapshot assembly
    # ------------------------------------------------------------------

    def _build_ai_application_snapshot(
        self, ai_application_id: UUID
    ) -> dict[str, Any]:
        ai_app = self._ai_applications.get(ai_application_id)
        if ai_app is None:
            raise NotFoundError(f"AIApplication {ai_application_id} not found")

        models = self._models.list(ai_application_id=ai_application_id, is_active=True)
        rules = self._rules.list(ai_application_id=ai_application_id, is_active=True)

        snapshot = _entity_to_dict(ai_app)
        snapshot["models"] = [_entity_to_dict(m) for m in models]
        snapshot["rules"] = [_entity_to_dict(r) for r in rules]
        return snapshot

    def _build_site_snapshot(self, site_id: UUID) -> dict[str, Any]:
        site = self._sites.get(site_id)
        if site is None:
            raise NotFoundError(f"Site {site_id} not found")

        camera_configs = self._camera_configs.list(site_id=site_id, is_active=True)
        cameras_data = []
        for cc in camera_configs:
            cc_dict = _entity_to_dict(cc)
            scene_configs = self._scene_configs.list(
                camera_config_id=cc.id, is_active=True
            )
            cc_dict["scene_configs"] = [_entity_to_dict(sc) for sc in scene_configs]
            cameras_data.append(cc_dict)

        snapshot = _entity_to_dict(site)
        snapshot["camera_configs"] = cameras_data
        return snapshot

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, inp: CreateDeploymentInput) -> Deployment:
        if inp.project_id is None:
            raise ValidationError("project_id is required")
        if inp.ai_application_ref is None:
            raise ValidationError("ai_application_ref is required")
        if inp.site_ref is None:
            raise ValidationError("site_ref is required")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")

        project = self._projects.get(inp.project_id)
        if project is None:
            raise NotFoundError(f"Project {inp.project_id} not found")

        ai_app_snapshot = self._build_ai_application_snapshot(inp.ai_application_ref)
        site_snapshot = self._build_site_snapshot(inp.site_ref)

        deployment = Deployment(
            id=uuid4(),
            project_id=inp.project_id,
            ai_application_ref=inp.ai_application_ref,
            site_ref=inp.site_ref,
            ai_application_snapshot=ai_app_snapshot,
            site_snapshot=site_snapshot,
            owner=owner,
            effective_date=effective_date,
            status="pending",
        )
        return self._deployments.create(deployment)

    def get(self, deployment_id: UUID) -> Deployment:
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            raise NotFoundError(f"Deployment {deployment_id} not found")
        return deployment

    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Deployment]:
        return self._deployments.list(
            project_id=project_id, status=status, is_active=is_active
        )

    def update(self, inp: UpdateDeploymentInput) -> Deployment:
        deployment = self._deployments.get(inp.deployment_id)
        if deployment is None:
            raise NotFoundError(f"Deployment {inp.deployment_id} not found")
        if deployment.version != inp.expected_version:
            raise OptimisticLockError(
                f"Deployment {inp.deployment_id}: expected version "
                f"{inp.expected_version}, current version is {deployment.version}"
            )
        if inp.status is not None:
            validate_deployment_status(inp.status)
            deployment.status = inp.status
        if inp.owner is not None:
            deployment.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            deployment.effective_date = inp.effective_date
        if inp.is_active is not None:
            deployment.is_active = inp.is_active

        deployment.version += 1
        return self._deployments.update(deployment)

    def activate(self, deployment_id: UUID, expected_version: int) -> Deployment:
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            raise NotFoundError(f"Deployment {deployment_id} not found")
        if deployment.version != expected_version:
            raise OptimisticLockError(
                f"Deployment {deployment_id}: expected version {expected_version}, "
                f"current version is {deployment.version}"
            )
        if deployment.status not in ("pending", "inactive"):
            raise ConflictError(
                f"Cannot activate Deployment {deployment_id}: "
                f"current status is {deployment.status!r}"
            )
        deployment.status = "active"
        deployment.is_active = True
        deployment.version += 1
        return self._deployments.update(deployment)

    def deactivate(self, deployment_id: UUID, expected_version: int) -> Deployment:
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            raise NotFoundError(f"Deployment {deployment_id} not found")
        if deployment.version != expected_version:
            raise OptimisticLockError(
                f"Deployment {deployment_id}: expected version {expected_version}, "
                f"current version is {deployment.version}"
            )
        if deployment.status != "active":
            raise ConflictError(
                f"Cannot deactivate Deployment {deployment_id}: "
                f"current status is {deployment.status!r}"
            )
        deployment.status = "inactive"
        deployment.is_active = False
        deployment.version += 1
        return self._deployments.update(deployment)

    def delete(self, deployment_id: UUID) -> None:
        deployment = self._deployments.get(deployment_id)
        if deployment is None:
            raise NotFoundError(f"Deployment {deployment_id} not found")
        if deployment.status == "active":
            raise ConflictError(
                f"Cannot delete Deployment {deployment_id}: it is active. "
                "Deactivate the deployment before deleting it."
            )
        self._deployments.delete(deployment_id)
