"""Integration tests for AIApplication, Model, Rule, SceneConfig, and FeatureFlag repos."""
from __future__ import annotations

from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import OptimisticLockError
from cv_platform.configuration.domain.models import FeatureFlag, Model, Rule, SceneConfig
from cv_platform.configuration.repositories.postgres.ai_application_repo import PostgresAIApplicationRepository
from cv_platform.configuration.repositories.postgres.feature_flag_repo import PostgresFeatureFlagRepository
from cv_platform.configuration.repositories.postgres.model_repo import PostgresModelRepository
from cv_platform.configuration.repositories.postgres.rule_repo import PostgresRuleRepository
from cv_platform.configuration.repositories.postgres.scene_config_repo import PostgresSceneConfigRepository
from tests.configuration.repositories.conftest import (
    make_ai_application_row,
    make_camera_config_row,
    make_project_row,
    make_site_row,
    now,
)


# ── AIApplication ─────────────────────────────────────────────────────────────

class TestAIApplicationRepo:
    @pytest.fixture
    def repo(self, conn):
        return PostgresAIApplicationRepository(conn)

    def test_create_and_get(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id, name="Vision App")
        result = repo.get(ai_app.id)
        assert result is not None
        assert result.name == "Vision App"

    def test_get_returns_none_for_missing(self, repo):
        assert repo.get(uuid4()) is None

    def test_list_filters_by_project_id(self, conn, repo):
        p1 = make_project_row(conn)
        p2 = make_project_row(conn)
        a1 = make_ai_application_row(conn, project_id=p1.id)
        a2 = make_ai_application_row(conn, project_id=p2.id)
        results = repo.list(project_id=p1.id)
        ids = [r.id for r in results]
        assert a1.id in ids
        assert a2.id not in ids

    def test_list_filters_by_is_active(self, conn, repo):
        project = make_project_row(conn)
        active = make_ai_application_row(conn, project_id=project.id, is_active=True)
        inactive = make_ai_application_row(conn, project_id=project.id, is_active=False)
        results = repo.list(is_active=True)
        ids = [r.id for r in results]
        assert active.id in ids
        assert inactive.id not in ids

    def test_update_success(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id, version=1)
        ai_app.name = "Renamed"
        ai_app.version = 2
        updated = repo.update(ai_app)
        assert updated.name == "Renamed"

    def test_update_raises_on_stale_version(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id, version=1)
        ai_app.version = 99
        with pytest.raises(OptimisticLockError):
            repo.update(ai_app)

    def test_delete(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        repo.delete(ai_app.id)
        assert repo.get(ai_app.id) is None


# ── Model ─────────────────────────────────────────────────────────────────────

def _make_model(ai_application_id, **kwargs):
    defaults = dict(
        id=uuid4(),
        ai_application_id=ai_application_id,
        name="YOLO v8",
        owner="admin",
        effective_date=now(),
        model_type="detection",
        parameters={"threshold": 0.5},
        version=1,
    )
    defaults.update(kwargs)
    return Model(**defaults)


class TestModelRepo:
    @pytest.fixture
    def repo(self, conn):
        return PostgresModelRepository(conn)

    def test_create_persists_jsonb_parameters(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        m = repo.create(_make_model(ai_app.id, parameters={"iou": 0.45, "conf": 0.5}))
        fetched = repo.get(m.id)
        assert fetched.parameters == {"iou": 0.45, "conf": 0.5}

    def test_list_filters_by_ai_application_id(self, conn, repo):
        project = make_project_row(conn)
        a1 = make_ai_application_row(conn, project_id=project.id)
        a2 = make_ai_application_row(conn, project_id=project.id)
        m1 = repo.create(_make_model(a1.id))
        m2 = repo.create(_make_model(a2.id))
        results = repo.list(ai_application_id=a1.id)
        ids = [r.id for r in results]
        assert m1.id in ids
        assert m2.id not in ids

    def test_update_success_and_stale(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        m = repo.create(_make_model(ai_app.id, version=1))
        m.name = "YOLOv9"
        m.version = 2
        updated = repo.update(m)
        assert updated.name == "YOLOv9"

        m.version = 99
        with pytest.raises(OptimisticLockError):
            repo.update(m)

    def test_delete(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        m = repo.create(_make_model(ai_app.id))
        repo.delete(m.id)
        assert repo.get(m.id) is None


# ── Rule ──────────────────────────────────────────────────────────────────────

def _make_rule(ai_application_id, **kwargs):
    defaults = dict(
        id=uuid4(),
        ai_application_id=ai_application_id,
        name="Intrusion Rule",
        owner="admin",
        effective_date=now(),
        rule_type="intrusion",
        parameters={"sensitivity": "high"},
        version=1,
    )
    defaults.update(kwargs)
    return Rule(**defaults)


class TestRuleRepo:
    @pytest.fixture
    def repo(self, conn):
        return PostgresRuleRepository(conn)

    def test_create_persists_jsonb_parameters(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        r = repo.create(_make_rule(ai_app.id, parameters={"zone": "A"}))
        fetched = repo.get(r.id)
        assert fetched.parameters == {"zone": "A"}

    def test_list_filters_by_ai_application_id(self, conn, repo):
        project = make_project_row(conn)
        a1 = make_ai_application_row(conn, project_id=project.id)
        a2 = make_ai_application_row(conn, project_id=project.id)
        r1 = repo.create(_make_rule(a1.id))
        r2 = repo.create(_make_rule(a2.id))
        results = repo.list(ai_application_id=a1.id)
        ids = [r.id for r in results]
        assert r1.id in ids
        assert r2.id not in ids

    def test_update_success_and_stale(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        r = repo.create(_make_rule(ai_app.id, version=1))
        r.name = "Updated Rule"
        r.version = 2
        updated = repo.update(r)
        assert updated.name == "Updated Rule"

        r.version = 50
        with pytest.raises(OptimisticLockError):
            repo.update(r)

    def test_delete(self, conn, repo):
        project = make_project_row(conn)
        ai_app = make_ai_application_row(conn, project_id=project.id)
        r = repo.create(_make_rule(ai_app.id))
        repo.delete(r.id)
        assert repo.get(r.id) is None


# ── SceneConfig ───────────────────────────────────────────────────────────────

def _make_scene_config(camera_config_id, **kwargs):
    defaults = dict(
        id=uuid4(),
        camera_config_id=camera_config_id,
        name="Scene A",
        owner="admin",
        effective_date=now(),
        version=1,
    )
    defaults.update(kwargs)
    return SceneConfig(**defaults)


class TestSceneConfigRepo:
    @pytest.fixture
    def repo(self, conn):
        return PostgresSceneConfigRepository(conn)

    def test_create_persists_all_jsonb_columns(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id)
        sc = repo.create(_make_scene_config(
            cc.id,
            rois={"points": [[0, 0], [100, 100]]},
            zones={"zone1": "region_a"},
            ground_plane={"height": 3.0},
            privacy_masks={"mask1": [1, 2, 3]},
            calibration={"fx": 1000},
        ))
        fetched = repo.get(sc.id)
        assert fetched.rois == {"points": [[0, 0], [100, 100]]}
        assert fetched.zones == {"zone1": "region_a"}
        assert fetched.ground_plane == {"height": 3.0}
        assert fetched.privacy_masks == {"mask1": [1, 2, 3]}
        assert fetched.calibration == {"fx": 1000}

    def test_list_filters_by_camera_config_id(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc1 = make_camera_config_row(conn, site_id=site.id)
        cc2 = make_camera_config_row(conn, site_id=site.id)
        sc1 = repo.create(_make_scene_config(cc1.id))
        sc2 = repo.create(_make_scene_config(cc2.id))
        results = repo.list(camera_config_id=cc1.id)
        ids = [r.id for r in results]
        assert sc1.id in ids
        assert sc2.id not in ids

    def test_update_success_and_stale(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id)
        sc = repo.create(_make_scene_config(cc.id, version=1))
        sc.name = "Updated Scene"
        sc.version = 2
        updated = repo.update(sc)
        assert updated.name == "Updated Scene"

        sc.version = 100
        with pytest.raises(OptimisticLockError):
            repo.update(sc)

    def test_has_any_for_camera_config_true(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id)
        repo.create(_make_scene_config(cc.id))
        assert repo.has_any_for_camera_config(cc.id) is True

    def test_has_any_for_camera_config_false(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id)
        assert repo.has_any_for_camera_config(cc.id) is False

    def test_delete(self, conn, repo):
        project = make_project_row(conn)
        site = make_site_row(conn, project_id=project.id)
        cc = make_camera_config_row(conn, site_id=site.id)
        sc = repo.create(_make_scene_config(cc.id))
        repo.delete(sc.id)
        assert repo.get(sc.id) is None


# ── FeatureFlag ───────────────────────────────────────────────────────────────

def _make_feature_flag(**kwargs):
    uid = uuid4()
    defaults = dict(
        id=uid,
        name=f"flag_{uid.hex[:8]}",
        owner="admin",
        effective_date=now(),
        is_enabled=False,
        target_type="global",
        version=1,
    )
    defaults.update(kwargs)
    return FeatureFlag(**defaults)


class TestFeatureFlagRepo:
    @pytest.fixture
    def repo(self, conn):
        return PostgresFeatureFlagRepository(conn)

    def test_create_and_get(self, conn, repo):
        ff = repo.create(_make_feature_flag(is_enabled=True))
        fetched = repo.get(ff.id)
        assert fetched is not None
        assert fetched.is_enabled is True

    def test_get_by_name(self, conn, repo):
        ff = repo.create(_make_feature_flag())
        result = repo.get_by_name(ff.name)
        assert result is not None
        assert result.id == ff.id

    def test_list_filters_by_target_type(self, conn, repo):
        ff_global = repo.create(_make_feature_flag(target_type="global"))
        ff_project = repo.create(_make_feature_flag(target_type="project"))
        results = repo.list(target_type="global")
        ids = [r.id for r in results]
        assert ff_global.id in ids
        assert ff_project.id not in ids

    def test_list_filters_by_is_active(self, conn, repo):
        active = repo.create(_make_feature_flag(is_active=True))
        inactive = repo.create(_make_feature_flag(is_active=False))
        results = repo.list(is_active=True)
        ids = [r.id for r in results]
        assert active.id in ids
        assert inactive.id not in ids

    def test_update_success_and_stale(self, conn, repo):
        ff = repo.create(_make_feature_flag(version=1))
        ff.is_enabled = True
        ff.version = 2
        updated = repo.update(ff)
        assert updated.is_enabled is True

        ff.version = 50
        with pytest.raises(OptimisticLockError):
            repo.update(ff)

    def test_delete(self, conn, repo):
        ff = repo.create(_make_feature_flag())
        repo.delete(ff.id)
        assert repo.get(ff.id) is None
