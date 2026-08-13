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
from cv_platform.configuration.domain.models import AIApplication
from cv_platform.configuration.repositories.interfaces import (
    AIApplicationRepository,
    DeploymentRepository,
    ProjectRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
)


@dataclass
class CreateAIApplicationInput:
    project_id: UUID
    name: str
    owner: str
    effective_date: datetime
    description: Optional[str] = None
    status: str = "active"


@dataclass
class UpdateAIApplicationInput:
    ai_application_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class AIApplicationService:
    def __init__(
        self,
        ai_application_repo: AIApplicationRepository,
        project_repo: ProjectRepository,
        deployment_repo: DeploymentRepository,
    ) -> None:
        self._ai_applications = ai_application_repo
        self._projects = project_repo
        self._deployments = deployment_repo

    def create(self, inp: CreateAIApplicationInput) -> AIApplication:
        if inp.project_id is None:
            raise ValidationError("project_id is required")
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_entity_status(inp.status)

        project = self._projects.get(inp.project_id)
        if project is None:
            raise NotFoundError(f"Project {inp.project_id} not found")

        ai_application = AIApplication(
            id=uuid4(),
            project_id=inp.project_id,
            name=name,
            owner=owner,
            effective_date=effective_date,
            description=inp.description,
            status=inp.status,
        )
        return self._ai_applications.create(ai_application)

    def get(self, ai_application_id: UUID) -> AIApplication:
        ai_app = self._ai_applications.get(ai_application_id)
        if ai_app is None:
            raise NotFoundError(f"AIApplication {ai_application_id} not found")
        return ai_app

    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[AIApplication]:
        return self._ai_applications.list(project_id=project_id, is_active=is_active)

    def update(self, inp: UpdateAIApplicationInput) -> AIApplication:
        ai_app = self._ai_applications.get(inp.ai_application_id)
        if ai_app is None:
            raise NotFoundError(f"AIApplication {inp.ai_application_id} not found")
        if ai_app.version != inp.expected_version:
            raise OptimisticLockError(
                f"AIApplication {inp.ai_application_id}: expected version "
                f"{inp.expected_version}, current version is {ai_app.version}"
            )
        if inp.name is not None:
            ai_app.name = require_non_empty_string(inp.name, "name")
        if inp.owner is not None:
            ai_app.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            ai_app.effective_date = inp.effective_date
        if inp.description is not None:
            ai_app.description = inp.description
        if inp.status is not None:
            validate_entity_status(inp.status)
            ai_app.status = inp.status
        if inp.is_active is not None:
            ai_app.is_active = inp.is_active

        ai_app.version += 1
        return self._ai_applications.update(ai_app)

    def delete(self, ai_application_id: UUID) -> None:
        ai_app = self._ai_applications.get(ai_application_id)
        if ai_app is None:
            raise NotFoundError(f"AIApplication {ai_application_id} not found")
        if self._deployments.has_active_by_ai_application(ai_application_id):
            raise ConflictError(
                f"Cannot delete AIApplication {ai_application_id}: it has active deployments. "
                "Deactivate all deployments before deleting the AI application."
            )
        self._ai_applications.delete(ai_application_id)
