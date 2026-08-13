"""Tests for SiteService — validates parent existence and child constraints."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import create_autospec
from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from cv_platform.configuration.domain.models import Project, Site
from cv_platform.configuration.repositories.interfaces import (
    CameraConfigRepository,
    ProjectRepository,
    SiteRepository,
)
from cv_platform.configuration.services.site_service import (
    CreateSiteInput,
    SiteService,
    UpdateSiteInput,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_project(**kwargs) -> Project:
    defaults = dict(
        id=uuid4(), name="Project", owner="sys", effective_date=_now(),
        status="active", is_active=True, version=1,
    )
    defaults.update(kwargs)
    return Project(**defaults)


def _make_site(**kwargs) -> Site:
    defaults = dict(
        id=uuid4(), project_id=uuid4(), name="Site A", owner="sys",
        effective_date=_now(), status="active", is_active=True, version=1,
    )
    defaults.update(kwargs)
    return Site(**defaults)


def _make_service():
    site_repo = create_autospec(SiteRepository)
    project_repo = create_autospec(ProjectRepository)
    camera_config_repo = create_autospec(CameraConfigRepository)
    service = SiteService(
        site_repo=site_repo,
        project_repo=project_repo,
        camera_config_repo=camera_config_repo,
    )
    return service, site_repo, project_repo, camera_config_repo


# ---------------------------------------------------------------------------
# create — parent validation
# ---------------------------------------------------------------------------


class TestSiteServiceCreate:
    def test_create_requires_existing_project(self):
        service, _, project_repo, _ = _make_service()
        project_repo.get.return_value = None
        inp = CreateSiteInput(
            project_id=uuid4(), name="S", owner="sys", effective_date=_now()
        )
        with pytest.raises(NotFoundError, match="Project"):
            service.create(inp)

    def test_create_raises_when_project_inactive(self):
        service, _, project_repo, _ = _make_service()
        project_repo.get.return_value = _make_project(is_active=False)
        inp = CreateSiteInput(
            project_id=uuid4(), name="S", owner="sys", effective_date=_now()
        )
        with pytest.raises(ConflictError, match="not active"):
            service.create(inp)

    def test_create_succeeds_with_active_project(self):
        service, site_repo, project_repo, _ = _make_service()
        project = _make_project(is_active=True)
        project_repo.get.return_value = project
        site = _make_site(project_id=project.id)
        site_repo.create.return_value = site
        inp = CreateSiteInput(
            project_id=project.id, name="S", owner="sys", effective_date=_now()
        )
        result = service.create(inp)
        assert result is site

    def test_create_raises_on_missing_name(self):
        service, _, project_repo, _ = _make_service()
        project_repo.get.return_value = _make_project()
        inp = CreateSiteInput(
            project_id=uuid4(), name="", owner="sys", effective_date=_now()
        )
        with pytest.raises(ValidationError, match="name"):
            service.create(inp)


# ---------------------------------------------------------------------------
# delete — child constraint
# ---------------------------------------------------------------------------


class TestSiteServiceDelete:
    def test_delete_raises_conflict_when_camera_configs_exist(self):
        service, site_repo, _, camera_config_repo = _make_service()
        site = _make_site()
        site_repo.get.return_value = site
        camera_config_repo.has_any_for_site.return_value = True

        with pytest.raises(ConflictError, match="camera configurations"):
            service.delete(site.id)

        site_repo.delete.assert_not_called()

    def test_delete_succeeds_when_no_camera_configs(self):
        service, site_repo, _, camera_config_repo = _make_service()
        site = _make_site()
        site_repo.get.return_value = site
        camera_config_repo.has_any_for_site.return_value = False

        service.delete(site.id)

        site_repo.delete.assert_called_once_with(site.id)

    def test_delete_raises_not_found(self):
        service, site_repo, _, _ = _make_service()
        site_repo.get.return_value = None

        with pytest.raises(NotFoundError):
            service.delete(uuid4())
