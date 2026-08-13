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
from cv_platform.configuration.domain.models import Model
from cv_platform.configuration.repositories.interfaces import (
    AIApplicationRepository,
    ModelRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
)


@dataclass
class CreateModelInput:
    ai_application_id: UUID
    name: str
    owner: str
    effective_date: datetime
    model_type: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    status: str = "active"


@dataclass
class UpdateModelInput:
    model_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    model_type: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class ModelService:
    def __init__(
        self,
        model_repo: ModelRepository,
        ai_application_repo: AIApplicationRepository,
    ) -> None:
        self._models = model_repo
        self._ai_applications = ai_application_repo

    def create(self, inp: CreateModelInput) -> Model:
        if inp.ai_application_id is None:
            raise ValidationError("ai_application_id is required")
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_entity_status(inp.status)

        ai_app = self._ai_applications.get(inp.ai_application_id)
        if ai_app is None:
            raise NotFoundError(f"AIApplication {inp.ai_application_id} not found")

        model = Model(
            id=uuid4(),
            ai_application_id=inp.ai_application_id,
            name=name,
            owner=owner,
            effective_date=effective_date,
            model_type=inp.model_type,
            parameters=inp.parameters,
            status=inp.status,
        )
        return self._models.create(model)

    def get(self, model_id: UUID) -> Model:
        model = self._models.get(model_id)
        if model is None:
            raise NotFoundError(f"Model {model_id} not found")
        return model

    def list(
        self,
        *,
        ai_application_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Model]:
        return self._models.list(ai_application_id=ai_application_id, is_active=is_active)

    def update(self, inp: UpdateModelInput) -> Model:
        model = self._models.get(inp.model_id)
        if model is None:
            raise NotFoundError(f"Model {inp.model_id} not found")
        if model.version != inp.expected_version:
            raise OptimisticLockError(
                f"Model {inp.model_id}: expected version {inp.expected_version}, "
                f"current version is {model.version}"
            )
        if inp.name is not None:
            model.name = require_non_empty_string(inp.name, "name")
        if inp.owner is not None:
            model.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            model.effective_date = inp.effective_date
        if inp.model_type is not None:
            model.model_type = inp.model_type
        if inp.parameters is not None:
            model.parameters = inp.parameters
        if inp.status is not None:
            validate_entity_status(inp.status)
            model.status = inp.status
        if inp.is_active is not None:
            model.is_active = inp.is_active

        model.version += 1
        return self._models.update(model)

    def delete(self, model_id: UUID) -> None:
        model = self._models.get(model_id)
        if model is None:
            raise NotFoundError(f"Model {model_id} not found")
        self._models.delete(model_id)
