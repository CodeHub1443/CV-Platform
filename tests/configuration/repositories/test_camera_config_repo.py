"""Integration tests for PostgresCameraConfigRepository."""
from __future__ import annotations

from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.repositories.postgres.camera_config_repo import PostgresCameraConfigRepository
from tests.configuration.repositories.conftest import (
    make_camera_config_row,
    make_project_row,
    make_site_row,
    now,
)


@pytest.fixture
def repo(conn):
    return PostgresCameraConfigRepository(conn)


class TestCameraConfigCreate:
    def test_create_persists_jsonb_fields(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(
            conn,
            site_id=site.id,
            credentials={"user": "admin", "pass": "secret"},
            resolution={"width": 1920, "height": 1080},
            capabilities={"ptz": True},
        )
        fetched = repo.get(cc.id)
        assert fetched.credentials == {"user": "admin", "pass": "secret"}
        assert fetched.resolution == {"width": 1920, "height": 1080}
        assert fetched.capabilities == {"ptz": True}


class TestCameraConfigGet:
    def test_get_returns_camera_config(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id)
        result = repo.get(cc.id)
        assert result is not None
        assert result.id == cc.id

    def test_get_returns_none_for_missing(self, repo):
        assert repo.get(uuid4()) is None


class TestCameraConfigList:
    def test_list_filters_by_site_id(self, conn, repo):
        project = make_project_row(conn)
        s1 = make_site_row(conn, project_id=project.id)
        s2 = make_site_row(conn, project_id=project.id)
        cc1 = make_camera_config_row(conn, site_id=s1.id)
        cc2 = make_camera_config_row(conn, site_id=s2.id)
        results = repo.list(site_id=s1.id)
        ids = [r.id for r in results]
        assert cc1.id in ids
        assert cc2.id not in ids

    def test_list_filters_by_is_active(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        active = make_camera_config_row(conn, site_id=site.id, is_active=True)
        inactive = make_camera_config_row(conn, site_id=site.id, is_active=False)
        results = repo.list(is_active=True)
        ids = [r.id for r in results]
        assert active.id in ids
        assert inactive.id not in ids


class TestCameraConfigUpdate:
    def test_update_success(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id, version=1)
        cc.name = "Updated Cam"
        cc.version = 2
        updated = repo.update(cc)
        assert updated.name == "Updated Cam"
        assert updated.version == 2

    def test_update_raises_on_stale_version(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id, version=1)
        cc.version = 99
        with pytest.raises(OptimisticLockError):
            repo.update(cc)


class TestCameraConfigHasAnyForSite:
    def test_returns_true_when_camera_configs_exist(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        make_camera_config_row(conn, site_id=site.id)
        assert repo.has_any_for_site(site.id) is True

    def test_returns_false_when_no_camera_configs(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        assert repo.has_any_for_site(site.id) is False

    def test_returns_false_for_nonexistent_site(self, repo):
        assert repo.has_any_for_site(uuid4()) is False
