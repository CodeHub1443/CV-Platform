"""Tests for ProjectService — validates inputs, enforces lifecycle rules."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, create_autospec
from uuid import UUID, uuid4

import pytest

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
from cv_platform.configuration.services.project_service import (
    CreateProjectInput,
    ProjectService,
    UpdateProjectInput,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_project(**kwargs) -> Project:
    defaults = dict(
        id=uuid4(),
        name="Test Project",
        owner="system",
        effective_date=_now(),
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    return Project(**defaults)


def _make_service() -> tuple[ProjectService, MagicMock, MagicMock]:
    project_repo = create_autospec(ProjectRepository)
    deployment_repo = create_autospec(DeploymentRepository)
    service = ProjectService(project_repo=project_repo, deployment_repo=deployment_repo)
    return service, project_repo, deployment_repo


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestProjectServiceCreate:
    def test_create_returns_project(self):
        service, project_repo, _ = _make_service()
        inp = CreateProjectInput(name="Alpha", owner="admin", effective_date=_now())
        expected = _make_project(name="Alpha")
        project_repo.create.return_value = expected

        result = service.create(inp)

        assert result is expected
        project_repo.create.assert_called_once()
        created_arg: Project = project_repo.create.call_args[0][0]
        assert created_arg.name == "Alpha"
        assert created_arg.owner == "admin"
        assert created_arg.status == "active"
        assert created_arg.version == 1

    def test_create_strips_whitespace_from_name(self):
        service, project_repo, _ = _make_service()
        inp = CreateProjectInput(name="  Beta  ", owner="admin", effective_date=_now())
        project_repo.create.return_value = _make_project(name="Beta")

        service.create(inp)

        created_arg: Project = project_repo.create.call_args[0][0]
        assert created_arg.name == "Beta"

    def test_create_raises_when_name_empty(self):
        service, _, _ = _make_service()
        inp = CreateProjectInput(name="", owner="admin", effective_date=_now())
        with pytest.raises(ValidationError, match="name"):
            service.create(inp)

    def test_create_raises_when_name_whitespace_only(self):
        service, _, _ = _make_service()
        inp = CreateProjectInput(name="   ", owner="admin", effective_date=_now())
        with pytest.raises(ValidationError, match="name"):
            service.create(inp)

    def test_create_raises_when_owner_empty(self):
        service, _, _ = _make_service()
        inp = CreateProjectInput(name="X", owner="", effective_date=_now())
        with pytest.raises(ValidationError, match="owner"):
            service.create(inp)

    def test_create_raises_when_effective_date_missing(self):
        service, _, _ = _make_service()
        inp = CreateProjectInput(name="X", owner="admin", effective_date=None)
        with pytest.raises(ValidationError, match="effective_date"):
            service.create(inp)

    def test_create_raises_on_invalid_status(self):
        service, _, _ = _make_service()
        inp = CreateProjectInput(
            name="X", owner="admin", effective_date=_now(), status="unknown"
        )
        with pytest.raises(ValidationError, match="status"):
            service.create(inp)

    @pytest.mark.parametrize("status", ["active", "inactive", "archived"])
    def test_create_accepts_valid_statuses(self, status):
        service, project_repo, _ = _make_service()
        inp = CreateProjectInput(name="X", owner="admin", effective_date=_now(), status=status)
        project_repo.create.return_value = _make_project(status=status)
        service.create(inp)  # should not raise


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestProjectServiceGet:
    def test_get_returns_project(self):
        service, project_repo, _ = _make_service()
        project = _make_project()
        project_repo.get.return_value = project

        result = service.get(project.id)

        assert result is project
        project_repo.get.assert_called_once_with(project.id)

    def test_get_raises_not_found(self):
        service, project_repo, _ = _make_service()
        project_repo.get.return_value = None
        pid = uuid4()

        with pytest.raises(NotFoundError, match=str(pid)):
            service.get(pid)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestProjectServiceUpdate:
    def test_update_increments_version(self):
        service, project_repo, _ = _make_service()
        project = _make_project(version=3)
        project_repo.get.return_value = project
        project_repo.update.return_value = project

        inp = UpdateProjectInput(
            project_id=project.id,
            expected_version=3,
            name="New Name",
        )
        service.update(inp)

        updated_arg: Project = project_repo.update.call_args[0][0]
        assert updated_arg.version == 4
        assert updated_arg.name == "New Name"

    def test_update_raises_optimistic_lock_on_version_mismatch(self):
        service, project_repo, _ = _make_service()
        project = _make_project(version=5)
        project_repo.get.return_value = project

        inp = UpdateProjectInput(
            project_id=project.id,
            expected_version=3,  # stale
        )
        with pytest.raises(OptimisticLockError):
            service.update(inp)

    def test_update_raises_not_found(self):
        service, project_repo, _ = _make_service()
        project_repo.get.return_value = None
        pid = uuid4()

        with pytest.raises(NotFoundError):
            service.update(UpdateProjectInput(project_id=pid, expected_version=1))

    def test_update_raises_on_invalid_status(self):
        service, project_repo, _ = _make_service()
        project = _make_project(version=1)
        project_repo.get.return_value = project

        inp = UpdateProjectInput(
            project_id=project.id, expected_version=1, status="bad_status"
        )
        with pytest.raises(ValidationError, match="status"):
            service.update(inp)

    def test_update_raises_on_empty_name(self):
        service, project_repo, _ = _make_service()
        project = _make_project(version=1)
        project_repo.get.return_value = project

        inp = UpdateProjectInput(project_id=project.id, expected_version=1, name="")
        with pytest.raises(ValidationError, match="name"):
            service.update(inp)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestProjectServiceDelete:
    def test_delete_succeeds_with_no_active_deployments(self):
        service, project_repo, deployment_repo = _make_service()
        project = _make_project()
        project_repo.get.return_value = project
        deployment_repo.has_active_by_project.return_value = False

        service.delete(project.id)

        project_repo.delete.assert_called_once_with(project.id)

    def test_delete_raises_conflict_when_active_deployments_exist(self):
        service, project_repo, deployment_repo = _make_service()
        project = _make_project()
        project_repo.get.return_value = project
        deployment_repo.has_active_by_project.return_value = True

        with pytest.raises(ConflictError, match="active deployments"):
            service.delete(project.id)

        project_repo.delete.assert_not_called()

    def test_delete_raises_not_found_when_project_missing(self):
        service, project_repo, _ = _make_service()
        project_repo.get.return_value = None
        pid = uuid4()

        with pytest.raises(NotFoundError):
            service.delete(pid)

        project_repo.delete.assert_not_called()
