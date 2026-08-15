"""Integration tests for PostgresSiteRepository."""
from __future__ import annotations

from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.repositories.postgres.site_repo import PostgresSiteRepository
from tests.configuration.repositories.conftest import make_project_row, make_site_row, now


@pytest.fixture
def repo(conn):
    return PostgresSiteRepository(conn)


class TestSiteCreate:
    def test_create_returns_site_with_timestamps(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id, name="Site A")
        assert site.id is not None
        assert site.project_id == project.id
        assert site.created_at is not None


class TestSiteGet:
    def test_get_returns_site(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        result = repo.get(site.id)
        assert result is not None
        assert result.id == site.id

    def test_get_returns_none_for_missing(self, repo):
        assert repo.get(uuid4()) is None


class TestSiteList:
    def test_list_filters_by_project_id(self, conn, repo):
        p1 = make_project_row(conn)
        p2 = make_project_row(conn)
        s1 = make_site_row(conn, project_id=p1.id)
        s2 = make_site_row(conn, project_id=p2.id)
        results = repo.list(project_id=p1.id)
        ids = [r.id for r in results]
        assert s1.id in ids
        assert s2.id not in ids

    def test_list_filters_by_is_active(self, conn, repo):
        project = make_project_row(conn)
        active = make_site_row(conn, project_id=project.id, is_active=True)
        inactive = make_site_row(conn, project_id=project.id, is_active=False)
        active_results = repo.list(is_active=True)
        assert active.id in [r.id for r in active_results]
        assert inactive.id not in [r.id for r in active_results]


class TestSiteUpdate:
    def test_update_success(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id, version=1)
        site.name = "Updated Site"
        site.version = 2
        updated = repo.update(site)
        assert updated.name == "Updated Site"
        assert updated.version == 2

    def test_update_raises_on_stale_version(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id, version=1)
        site.version = 10
        with pytest.raises(OptimisticLockError):
            repo.update(site)


class TestSiteDelete:
    def test_delete_removes_site(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        repo.delete(site.id)
        assert repo.get(site.id) is None
