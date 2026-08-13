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
from cv_platform.configuration.domain.models import CameraConfig
from cv_platform.configuration.repositories.interfaces import (
    CameraConfigRepository,
    SceneConfigRepository,
    SiteRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
)


@dataclass
class CreateCameraConfigInput:
    site_id: UUID
    name: str
    owner: str
    effective_date: datetime
    rtsp_url: Optional[str] = None
    credentials: Optional[dict[str, Any]] = None
    resolution: Optional[dict[str, Any]] = None
    capabilities: Optional[dict[str, Any]] = None
    status: str = "active"


@dataclass
class UpdateCameraConfigInput:
    camera_config_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    rtsp_url: Optional[str] = None
    credentials: Optional[dict[str, Any]] = None
    resolution: Optional[dict[str, Any]] = None
    capabilities: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class CameraConfigService:
    def __init__(
        self,
        camera_config_repo: CameraConfigRepository,
        site_repo: SiteRepository,
        scene_config_repo: SceneConfigRepository,
    ) -> None:
        self._camera_configs = camera_config_repo
        self._sites = site_repo
        self._scene_configs = scene_config_repo

    def create(self, inp: CreateCameraConfigInput) -> CameraConfig:
        if inp.site_id is None:
            raise ValidationError("site_id is required")
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_entity_status(inp.status)

        site = self._sites.get(inp.site_id)
        if site is None:
            raise NotFoundError(f"Site {inp.site_id} not found")
        if not site.is_active:
            raise ConflictError(f"Site {inp.site_id} is not active")

        camera_config = CameraConfig(
            id=uuid4(),
            site_id=inp.site_id,
            name=name,
            owner=owner,
            effective_date=effective_date,
            rtsp_url=inp.rtsp_url,
            credentials=inp.credentials,
            resolution=inp.resolution,
            capabilities=inp.capabilities,
            status=inp.status,
        )
        return self._camera_configs.create(camera_config)

    def get(self, camera_config_id: UUID) -> CameraConfig:
        camera_config = self._camera_configs.get(camera_config_id)
        if camera_config is None:
            raise NotFoundError(f"CameraConfig {camera_config_id} not found")
        return camera_config

    def list(
        self,
        *,
        site_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[CameraConfig]:
        return self._camera_configs.list(site_id=site_id, is_active=is_active)

    def update(self, inp: UpdateCameraConfigInput) -> CameraConfig:
        camera_config = self._camera_configs.get(inp.camera_config_id)
        if camera_config is None:
            raise NotFoundError(f"CameraConfig {inp.camera_config_id} not found")
        if camera_config.version != inp.expected_version:
            raise OptimisticLockError(
                f"CameraConfig {inp.camera_config_id}: expected version "
                f"{inp.expected_version}, current version is {camera_config.version}"
            )
        if inp.name is not None:
            camera_config.name = require_non_empty_string(inp.name, "name")
        if inp.owner is not None:
            camera_config.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            camera_config.effective_date = inp.effective_date
        if inp.rtsp_url is not None:
            camera_config.rtsp_url = inp.rtsp_url
        if inp.credentials is not None:
            camera_config.credentials = inp.credentials
        if inp.resolution is not None:
            camera_config.resolution = inp.resolution
        if inp.capabilities is not None:
            camera_config.capabilities = inp.capabilities
        if inp.status is not None:
            validate_entity_status(inp.status)
            camera_config.status = inp.status
        if inp.is_active is not None:
            camera_config.is_active = inp.is_active

        camera_config.version += 1
        return self._camera_configs.update(camera_config)

    def delete(self, camera_config_id: UUID) -> None:
        camera_config = self._camera_configs.get(camera_config_id)
        if camera_config is None:
            raise NotFoundError(f"CameraConfig {camera_config_id} not found")
        if self._scene_configs.has_any_for_camera_config(camera_config_id):
            raise ConflictError(
                f"Cannot delete CameraConfig {camera_config_id}: it has scene configurations. "
                "Remove all scene configurations before deleting the camera configuration."
            )
        self._camera_configs.delete(camera_config_id)
