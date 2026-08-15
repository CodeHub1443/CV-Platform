"""Integration tests for PostgresDeploymentRepository — including boolean guard methods."""
from __future__ import annotations

from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import Deployment
from cv_platform.configuration.repositories.postgres.deployment_repo import PostgresDeploymentRepository
from tests.configuration.repositories.conftest import (
    make_ai_application_row,
    make_project_row,
    make_site_row,
    now,
)


@pytest.fixture
def repo(conn):
    return PostgresDeploymentRepository(conn)


def _make_deployment(project_id, ai_app_id=None, site_id=None, status="pending", **kwargs):
    return Deployment(
        id=uuid4(),
        project_id=project_id,
        ai_application_ref=ai_app_id,
        site_ref=site_id,
        ai_application_snapshot={"id": str(ai_app_id) if ai_app_id else ""},
        site_snapshot={"id": str(site_id) if site_id else ""},
        owner="test_owner",
        effective_date=now(),
        status=status,
        is_active=True,
        version=1,
        **kwargs,
    )


class TestDeploymentCreate:
    def test_create_persists_jsonb_snapshots(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        site = make_site_row(conn, project_id=project.id)
        d = _make_deployment(
            project.id,
            ai_app_id=ai_app.id,
            site_id=site.id,
        )
        d.ai_application_snapshot = {"name": "MyApp", "version": 1}
        d.site_snapshot = {"location": "Dhaka"}
        created = repo.create(d)
        fetched = repo.get(created.id)
        assert fetched.ai_application_snapshot == {"name": "MyApp", "version": 1}
        assert fetched.site_snapshot == {"location": "Dhaka"}


class TestDeploymentGet:
    def test_get_returns_deployment(self, conn, repo):
        project = make_project_row(conn)
        d = _make_deployment(project.id)
        created = repo.create(d)
        result = repo.get(created.id)
        assert result is not None
        assert result.id == created.id

    def test_get_returns_none_for_missing(self, repo):
        assert repo.get(uuid4()) is None


class TestDeploymentList:
    def test_list_filters_by_project_id(self, conn, repo):
        p1 = make_project_row(conn)
        p2 = make_project_row(conn)
        d1 = repo.create(_make_deployment(p1.id))
        d2 = repo.create(_make_deployment(p2.id))
        results = repo.list(project_id=p1.id)
        ids = [r.id for r in results]
        assert d1.id in ids
        assert d2.id not in ids

    def test_list_filters_by_status(self, conn, repo):
        project = make_project_row(conn)
        pending = repo.create(_make_deployment(project.id, status="pending"))
        active = repo.create(_make_deployment(project.id, status="active"))
        results = repo.list(status="active")
        ids = [r.id for r in results]
        assert active.id in ids
        assert pending.id not in ids


class TestDeploymentUpdate:
    def test_update_success(self, conn, repo):
        project = make_project_row(conn)
        d = repo.create(_make_deployment(project.id, version=1))
        d.status = "active"
        d.version = 2
        updated = repo.update(d)
        assert updated.status == "active"
        assert updated.version == 2

    def test_update_raises_on_stale_version(self, conn, repo):
        project = make_project_row(conn)
        d = repo.create(_make_deployment(project.id, version=1))
        d.version = 99
        with pytest.raises(OptimisticLockError):
            repo.update(d)


class TestDeploymentDelete:
    def test_delete_removes_deployment(self, conn, repo):
        project = make_project_row(conn)
        d = repo.create(_make_deployment(project.id))
        repo.delete(d.id)
        assert repo.get(d.id) is None


class TestDeploymentBooleanGuards:
    def test_has_active_by_project_returns_true(self, conn, repo):
        project = make_project_row(conn)
        repo.create(_make_deployment(project.id, status="active"))
        assert repo.has_active_by_project(project.id) is True

    def test_has_active_by_project_returns_false_when_no_active(self, conn, repo):
        project = make_project_row(conn)
        repo.create(_make_deployment(project.id, status="pending"))
        assert repo.has_active_by_project(project.id) is False

    def test_has_active_by_project_returns_false_for_unknown(self, repo):
        assert repo.has_active_by_project(uuid4()) is False

    def test_has_active_by_ai_application_returns_true(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        d = _make_deployment(project.id, ai_app_id=ai_app.id, status="active")
        repo.create(d)
        assert repo.has_active_by_ai_application(ai_app.id) is True

    def test_has_active_by_ai_application_returns_false_when_pending(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        repo.create(_make_deployment(project.id, ai_app_id=ai_app.id, status="pending"))
        assert repo.has_active_by_ai_application(ai_app.id) is False

    def test_has_active_by_site_returns_true(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        repo.create(_make_deployment(project.id, site_id=site.id, status="active"))
        assert repo.has_active_by_site(site.id) is True

    def test_has_active_by_site_returns_false_when_no_active(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        repo.create(_make_deployment(project.id, site_id=site.id, status="pending"))
        assert repo.has_active_by_site(site.id) is False

    def test_has_active_by_site_returns_false_for_unknown(self, repo):
        assert repo.has_active_by_site(uuid4()) is False
