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
from cv_platform.configuration.domain.models import Site
from cv_platform.configuration.repositories.interfaces import (
    CameraConfigRepository,
    ProjectRepository,
    SiteRepository,
)
from cv_platform.configuration.services._validation import (
    require_datetime,
    require_non_empty_string,
    validate_entity_status,
)


@dataclass
class CreateSiteInput:
    project_id: UUID
    name: str
    owner: str
    effective_date: datetime
    location: Optional[str] = None
    status: str = "active"


@dataclass
class UpdateSiteInput:
    site_id: UUID
    expected_version: int
    name: Optional[str] = None
    owner: Optional[str] = None
    effective_date: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class SiteService:
    def __init__(
        self,
        site_repo: SiteRepository,
        project_repo: ProjectRepository,
        camera_config_repo: CameraConfigRepository,
    ) -> None:
        self._sites = site_repo
        self._projects = project_repo
        self._camera_configs = camera_config_repo

    def create(self, inp: CreateSiteInput) -> Site:
        if inp.project_id is None:
            raise ValidationError("project_id is required")
        name = require_non_empty_string(inp.name, "name")
        owner = require_non_empty_string(inp.owner, "owner")
        effective_date = require_datetime(inp.effective_date, "effective_date")
        validate_entity_status(inp.status)

        project = self._projects.get(inp.project_id)
        if project is None:
            raise NotFoundError(f"Project {inp.project_id} not found")
        if not project.is_active:
            raise ConflictError(f"Project {inp.project_id} is not active")

        site = Site(
            id=uuid4(),
            project_id=inp.project_id,
            name=name,
            owner=owner,
            effective_date=effective_date,
            location=inp.location,
            status=inp.status,
        )
        return self._sites.create(site)

    def get(self, site_id: UUID) -> Site:
        site = self._sites.get(site_id)
        if site is None:
            raise NotFoundError(f"Site {site_id} not found")
        return site

    def list(
        self,
        *,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> list[Site]:
        return self._sites.list(project_id=project_id, is_active=is_active)

    def update(self, inp: UpdateSiteInput) -> Site:
        site = self._sites.get(inp.site_id)
        if site is None:
            raise NotFoundError(f"Site {inp.site_id} not found")
        if site.version != inp.expected_version:
            raise OptimisticLockError(
                f"Site {inp.site_id}: expected version {inp.expected_version}, "
                f"current version is {site.version}"
            )
        if inp.name is not None:
            site.name = require_non_empty_string(inp.name, "name")
        if inp.owner is not None:
            site.owner = require_non_empty_string(inp.owner, "owner")
        if inp.effective_date is not None:
            site.effective_date = inp.effective_date
        if inp.location is not None:
            site.location = inp.location
        if inp.status is not None:
            validate_entity_status(inp.status)
            site.status = inp.status
        if inp.is_active is not None:
            site.is_active = inp.is_active

        site.version += 1
        return self._sites.update(site)

    def delete(self, site_id: UUID) -> None:
        site = self._sites.get(site_id)
        if site is None:
            raise NotFoundError(f"Site {site_id} not found")
        if self._camera_configs.has_any_for_site(site_id):
            raise ConflictError(
                f"Cannot delete Site {site_id}: it has camera configurations. "
                "Remove all camera configurations before deleting the site."
            )
        self._sites.delete(site_id)
