from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from cv_platform.configuration.domain.exceptions import (
    NotFoundError,
    OptimisticLockError,
    ValidationError,
)
from cv_platform.configuration.domain.models import SceneConfig
from cv_platform.configuration.repositories.interfaces import (
    CameraConfigRepository,
    SceneConfigRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
)


@dataclass
class CreateSceneConfigInput:
    camera_config_id: UUID
    name: str
    owner: str
    effective_date: datetime
    rois: Optional[dict[str, Any]] = None
    zones: Optional[dict[str, Any]] = None
    ground_plane: Optional[dict[str, Any]] = None
    privacy_masks: Optional[dict[str, Any]] = None
    calibration: Optional[dict[str, Any]] = None
    status: str = "active"


@dataclass
class UpdateSceneConfigInput:
    scene_config_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    rois: Optional[dict[str, Any]] = None
    zones: Optional[dict[str, Any]] = None
    ground_plane: Optional[dict[str, Any]] = None
    privacy_masks: Optional[dict[str, Any]] = None
    calibration: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class SceneConfigService:
    def __init__(
        self,
        scene_config_repo: SceneConfigRepository,
        camera_config_repo: CameraConfigRepository,
    ) -> None:
        self._scene_configs = scene_config_repo
        self._camera_configs = camera_config_repo

    def create(self, inp: CreateSceneConfigInput) -> SceneConfig:
        if inp.camera_config_id is None:
            raise ValidationError("camera_config_id is required")
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_entity_status(inp.status)

        camera_config = self._camera_configs.get(inp.camera_config_id)
        if camera_config is None:
            raise NotFoundError(f"CameraConfig {inp.camera_config_id} not found")

        scene_config = SceneConfig(
            id=uuid4(),
            camera_config_id=inp.camera_config_id,
            name=name,
            owner=owner,
            effective_date=effective_date,
            rois=inp.rois,
            zones=inp.zones,
            ground_plane=inp.ground_plane,
            privacy_masks=inp.privacy_masks,
            calibration=inp.calibration,
            status=inp.status,
        )
        return self._scene_configs.create(scene_config)

    def get(self, scene_config_id: UUID) -> SceneConfig:
        scene_config = self._scene_configs.get(scene_config_id)
        if scene_config is None:
            raise NotFoundError(f"SceneConfig {scene_config_id} not found")
        return scene_config

    def list(
        self,
        *,
        camera_config_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[SceneConfig]:
        return self._scene_configs.list(
            camera_config_id=camera_config_id, is_active=is_active
        )

    def update(self, inp: UpdateSceneConfigInput) -> SceneConfig:
        scene_config = self._scene_configs.get(inp.scene_config_id)
        if scene_config is None:
            raise NotFoundError(f"SceneConfig {inp.scene_config_id} not found")
        if scene_config.version != inp.expected_version:
            raise OptimisticLockError(
                f"SceneConfig {inp.scene_config_id}: expected version "
                f"{inp.expected_version}, current version is {scene_config.version}"
            )
        if inp.name is not None:
            scene_config.name = require_non_empty_string(inp.name, "name")
        if inp.owner is not None:
            scene_config.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            scene_config.effective_date = inp.effective_date
        if inp.rois is not None:
            scene_config.rois = inp.rois
        if inp.zones is not None:
            scene_config.zones = inp.zones
        if inp.ground_plane is not None:
            scene_config.ground_plane = inp.ground_plane
        if inp.privacy_masks is not None:
            scene_config.privacy_masks = inp.privacy_masks
        if inp.calibration is not None:
            scene_config.calibration = inp.calibration
        if inp.status is not None:
            validate_entity_status(inp.status)
            scene_config.status = inp.status
        if inp.is_active is not None:
            scene_config.is_active = inp.is_active

        scene_config.version += 1
        return self._scene_configs.update(scene_config)

    def delete(self, scene_config_id: UUID) -> None:
        scene_config = self._scene_configs.get(scene_config_id)
        if scene_config is None:
            raise NotFoundError(f"SceneConfig {scene_config_id} not found")
        self._scene_configs.delete(scene_config_id)
