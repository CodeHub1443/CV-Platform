"""Integration tests for PostgresProjectRepository."""
from __future__ import annotations

from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import Project
from cv_platform.configuration.repositories.postgres.project_repo import PostgresProjectRepository
from tests.configuration.repositories.conftest import make_project_row, now


@pytest.fixture
def repo(conn):
    return PostgresProjectRepository(conn)


class TestProjectCreate:
    def test_create_returns_project_with_timestamps(self, repo):
        p = Project(id=uuid4(), name="Alpha", owner="admin", effective_date=now(), version=1)
        created = repo.create(p)
        assert created.id == p.id
        assert created.name == "Alpha"
        assert created.created_at is not None
        assert created.updated_at is not None

    def test_create_persists_optional_fields(self, repo):
        p = Project(id=uuid4(), name="Beta", owner="admin", effective_date=now(), description="desc", version=1)
        created = repo.create(p)
        assert created.description == "desc"


class TestProjectGet:
    def test_get_returns_project(self, conn, repo):
        p = make_project_row(conn, name="Gamma")
        result = repo.get(p.id)
        assert result is not None
        assert result.id == p.id
        assert result.name == "Gamma"

    def test_get_returns_none_for_missing(self, repo):
        assert repo.get(uuid4()) is None


class TestProjectList:
    def test_list_returns_created_project(self, conn, repo):
        p = make_project_row(conn)
        results = repo.list()
        ids = [r.id for r in results]
        assert p.id in ids

    def test_list_filters_by_is_active_true(self, conn, repo):
        active = make_project_row(conn, is_active=True)
        inactive = make_project_row(conn, is_active=False)
        results = repo.list(is_active=True)
        ids = [r.id for r in results]
        assert active.id in ids
        assert inactive.id not in ids

    def test_list_filters_by_is_active_false(self, conn, repo):
        inactive = make_project_row(conn, is_active=False)
        results = repo.list(is_active=False)
        ids = [r.id for r in results]
        assert inactive.id in ids


class TestProjectUpdate:
    def test_update_success_increments_version(self, conn, repo):
        p = make_project_row(conn, version=1)
        p.name = "Updated"
        p.version = 2
        updated = repo.update(p)
        assert updated.name == "Updated"
        assert updated.version == 2

    def test_update_raises_optimistic_lock_on_stale_version(self, conn, repo):
        p = make_project_row(conn, version=1)
        p.version = 5  # expected_version = 4, DB has version 1 → mismatch
        with pytest.raises(OptimisticLockError):
            repo.update(p)


class TestProjectDelete:
    def test_delete_removes_project(self, conn, repo):
        p = make_project_row(conn)
        repo.delete(p.id)
        assert repo.get(p.id) is None

    def test_delete_nonexistent_is_silent(self, repo):
        repo.delete(uuid4())  # should not raise
