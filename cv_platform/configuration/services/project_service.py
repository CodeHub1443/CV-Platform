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
from cv_platform.configuration.domain.models import Project
from cv_platform.configuration.repositories.interfaces import (
    DeploymentRepository,
    ProjectRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
)


@dataclass
class CreateProjectInput:
    name: str
    owner: str
    effective_date: datetime
    description: Optional[str] = None
    status: str = "active"


@dataclass
class UpdateProjectInput:
    project_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        deployment_repo: DeploymentRepository,
    ) -> None:
        self._projects = project_repo
        self._deployments = deployment_repo

    def create(self, inp: CreateProjectInput) -> Project:
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_entity_status(inp.status)

        project = Project(
            id=uuid4(),
            name=name,
            owner=owner,
            effective_date=effective_date,
            description=inp.description,
            status=inp.status,
        )
        return self._projects.create(project)

    def get(self, project_id: UUID) -> Project:
        project = self._projects.get(project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        return project

    def list(self, *, is_active: Optional[bool] = None) -> list[Project]:
        return self._projects.list(is_active=is_active)

    def update(self, inp: UpdateProjectInput) -> Project:
        project = self._projects.get(inp.project_id)
        if project is None:
            raise NotFoundError(f"Project {inp.project_id} not found")
        if project.version != inp.expected_version:
            raise OptimisticLockError(
                f"Project {inp.project_id}: expected version {inp.expected_version}, "
                f"current version is {project.version}"
            )
        if inp.name is not None:
            project.name = require_non_empty_string(inp.name, "name")
        if inp.owner is not None:
            project.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            project.effective_date = inp.effective_date
        if inp.description is not None:
            project.description = inp.description
        if inp.status is not None:
            validate_entity_status(inp.status)
            project.status = inp.status
        if inp.is_active is not None:
            project.is_active = inp.is_active

        project.version += 1
        return self._projects.update(project)

    def delete(self, project_id: UUID) -> None:
        project = self._projects.get(project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        if self._deployments.has_active_by_project(project_id):
            raise ConflictError(
                f"Cannot delete Project {project_id}: it has active deployments. "
                "Deactivate all deployments before deleting the project."
            )
        self._projects.delete(project_id)
