from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from cv_platform.configuration.domain.exceptions import (
    ConflictError,
    NotFoundError,
    OptimisticLockError,
    ValidationError,
)
from cv_platform.configuration.domain.models import FeatureFlag
from cv_platform.configuration.repositories.interfaces import FeatureFlagRepository
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
    validate_flag_target_type,
)


@dataclass
class CreateFeatureFlagInput:
    name: str
    owner: str
    effective_date: datetime
    description: Optional[str] = None
    is_enabled: bool = False
    target_type: str = "global"
    target_id: Optional[UUID] = None
    status: str = "active"


@dataclass
class UpdateFeatureFlagInput:
    feature_flag_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class FeatureFlagService:
    def __init__(self, feature_flag_repo: FeatureFlagRepository) -> None:
        self._flags = feature_flag_repo

    def create(self, inp: CreateFeatureFlagInput) -> FeatureFlag:
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_flag_target_type(inp.target_type)
        validate_entity_status(inp.status)

        if inp.target_type != "global" and inp.target_id is None:
            raise ValidationError(
                f"target_id is required when target_type is {inp.target_type!r}"
            )

        if self._flags.get_by_name(name) is not None:
            raise ConflictError(f"Feature flag {name!r} already exists")

        flag = FeatureFlag(
            id=uuid4(),
            name=name,
            owner=owner,
            effective_date=effective_date,
            description=inp.description,
            is_enabled=inp.is_enabled,
            target_type=inp.target_type,
            target_id=inp.target_id,
            status=inp.status,
        )
        return self._flags.create(flag)

    def get(self, feature_flag_id: UUID) -> FeatureFlag:
        flag = self._flags.get(feature_flag_id)
        if flag is None:
            raise NotFoundError(f"FeatureFlag {feature_flag_id} not found")
        return flag

    def get_by_name(self, name: str) -> FeatureFlag:
        flag = self._flags.get_by_name(name)
        if flag is None:
            raise NotFoundError(f"FeatureFlag {name!r} not found")
        return flag

    def list(
        self,
        *,
        target_type: Optional[str] = None,
        target_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[FeatureFlag]:
        return self._flags.list(
            target_type=target_type, target_id=target_id, is_active=is_active
        )

    def update(self, inp: UpdateFeatureFlagInput) -> FeatureFlag:
        flag = self._flags.get(inp.feature_flag_id)
        if flag is None:
            raise NotFoundError(f"FeatureFlag {inp.feature_flag_id} not found")
        if flag.version != inp.expected_version:
            raise OptimisticLockError(
                f"FeatureFlag {inp.feature_flag_id}: expected version "
                f"{inp.expected_version}, current version is {flag.version}"
            )
        if inp.name is not None:
            new_name = require_non_empty_string(inp.name, "name")
            existing = self._flags.get_by_name(new_name)
            if existing is not None and existing.id != inp.feature_flag_id:
                raise ConflictError(f"Feature flag {new_name!r} already exists")
            flag.name = new_name
        if inp.owner is not None:
            flag.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            flag.effective_date = inp.effective_date
        if inp.description is not None:
            flag.description = inp.description
        if inp.is_enabled is not None:
            flag.is_enabled = inp.is_enabled
        if inp.target_type is not None:
            validate_flag_target_type(inp.target_type)
            flag.target_type = inp.target_type
        if inp.target_id is not None:
            flag.target_id = inp.target_id
        if inp.status is not None:
            validate_entity_status(inp.status)
            flag.status = inp.status
        if inp.is_active is not None:
            flag.is_active = inp.is_active

        flag.version += 1
        return self._flags.update(flag)

    def delete(self, feature_flag_id: UUID) -> None:
        flag = self._flags.get(feature_flag_id)
        if flag is None:
            raise NotFoundError(f"FeatureFlag {feature_flag_id} not found")
        self._flags.delete(feature_flag_id)
