"""Tests for DeploymentService — snapshot assembly and cross-entity lifecycle rules."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import create_autospec
from uuid import uuid4

import pytest

from cv_platform.configuration.domain.exceptions import (
    ConflictError,
    NotFoundError,
    OptimisticLockError,
    ValidationError,
)
from cv_platform.configuration.domain.models import (
    AIApplication,
    CameraConfig,
    Deployment,
    Model,
    Project,
    Rule,
    SceneConfig,
    Site,
)
from cv_platform.configuration.repositories.interfaces import (
    AIApplicationRepository,
    CameraConfigRepository,
    DeploymentRepository,
    ModelRepository,
    ProjectRepository,
    RuleRepository,
    SceneConfigRepository,
    SiteRepository,
)
from cv_platform.configuration.services.deployment_service import (
    CreateDeploymentInput,
    DeploymentService,
    UpdateDeploymentInput,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_service():
    deployment_repo = create_autospec(DeploymentRepository)
    project_repo = create_autospec(ProjectRepository)
    ai_application_repo = create_autospec(AIApplicationRepository)
    model_repo = create_autospec(ModelRepository)
    rule_repo = create_autospec(RuleRepository)
    site_repo = create_autospec(SiteRepository)
    camera_config_repo = create_autospec(CameraConfigRepository)
    scene_config_repo = create_autospec(SceneConfigRepository)

    service = DeploymentService(
        deployment_repo=deployment_repo,
        project_repo=project_repo,
        ai_application_repo=ai_application_repo,
        model_repo=model_repo,
        rule_repo=rule_repo,
        site_repo=site_repo,
        camera_config_repo=camera_config_repo,
        scene_config_repo=scene_config_repo,
    )
    return (
        service,
        deployment_repo,
        project_repo,
        ai_application_repo,
        model_repo,
        rule_repo,
        site_repo,
        camera_config_repo,
        scene_config_repo,
    )


def _make_project(**kw) -> Project:
    return Project(
        id=kw.get("id", uuid4()),
        name="P",
        owner="sys",
        effective_date=_now(),
        is_active=True,
        version=1,
    )


def _make_ai_app(project_id=None, **kw) -> AIApplication:
    return AIApplication(
        id=kw.get("id", uuid4()),
        project_id=project_id or uuid4(),
        name="App",
        owner="sys",
        effective_date=_now(),
        version=1,
    )


def _make_model(ai_application_id=None, **kw) -> Model:
    return Model(
        id=kw.get("id", uuid4()),
        ai_application_id=ai_application_id or uuid4(),
        name="M",
        owner="sys",
        effective_date=_now(),
        version=1,
    )


def _make_rule(ai_application_id=None, **kw) -> Rule:
    return Rule(
        id=kw.get("id", uuid4()),
        ai_application_id=ai_application_id or uuid4(),
        name="R",
        owner="sys",
        effective_date=_now(),
        version=1,
    )


def _make_site(**kw) -> Site:
    return Site(
        id=kw.get("id", uuid4()),
        project_id=kw.get("project_id", uuid4()),
        name="Site",
        owner="sys",
        effective_date=_now(),
        version=1,
    )


def _make_camera_config(site_id=None, **kw) -> CameraConfig:
    return CameraConfig(
        id=kw.get("id", uuid4()),
        site_id=site_id or uuid4(),
        name="Cam",
        owner="sys",
        effective_date=_now(),
        version=1,
    )


def _make_scene_config(camera_config_id=None, **kw) -> SceneConfig:
    return SceneConfig(
        id=kw.get("id", uuid4()),
        camera_config_id=camera_config_id or uuid4(),
        name="Scene",
        owner="sys",
        effective_date=_now(),
        version=1,
    )


def _make_deployment(**kw) -> Deployment:
    return Deployment(
        id=kw.get("id", uuid4()),
        project_id=kw.get("project_id", uuid4()),
        ai_application_snapshot=kw.get("ai_application_snapshot", {"id": str(uuid4()), "models": [], "rules": []}),
        site_snapshot=kw.get("site_snapshot", {"id": str(uuid4()), "camera_configs": []}),
        owner="sys",
        effective_date=_now(),
        status=kw.get("status", "pending"),
        is_active=kw.get("is_active", True),
        version=kw.get("version", 1),
    )


def _setup_happy_path_mocks(
    service_repos,
    project,
    ai_app,
    models,
    rules,
    site,
    camera_configs,
    scene_configs_by_camera,
):
    (
        _,
        deployment_repo,
        project_repo,
        ai_application_repo,
        model_repo,
        rule_repo,
        site_repo,
        camera_config_repo,
        scene_config_repo,
    ) = service_repos

    project_repo.get.return_value = project
    ai_application_repo.get.return_value = ai_app
    model_repo.list.return_value = models
    rule_repo.list.return_value = rules
    site_repo.get.return_value = site
    camera_config_repo.list.return_value = camera_configs

    def scene_list_side_effect(camera_config_id=None, is_active=None):
        return scene_configs_by_camera.get(camera_config_id, [])

    scene_config_repo.list.side_effect = scene_list_side_effect


# ---------------------------------------------------------------------------
# create — snapshot assembly
# ---------------------------------------------------------------------------


class TestDeploymentServiceCreate:
    def test_create_assembles_full_snapshot(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        project = _make_project()
        ai_app = _make_ai_app()
        model = _make_model(ai_application_id=ai_app.id)
        rule = _make_rule(ai_application_id=ai_app.id)
        site = _make_site()
        cc = _make_camera_config(site_id=site.id)
        sc = _make_scene_config(camera_config_id=cc.id)

        _setup_happy_path_mocks(
            repos,
            project=project,
            ai_app=ai_app,
            models=[model],
            rules=[rule],
            site=site,
            camera_configs=[cc],
            scene_configs_by_camera={cc.id: [sc]},
        )

        created_deployment = _make_deployment(project_id=project.id)
        deployment_repo.create.return_value = created_deployment

        inp = CreateDeploymentInput(
            project_id=project.id,
            ai_application_ref=ai_app.id,
            site_ref=site.id,
            owner="sys",
            effective_date=_now(),
        )
        result = service.create(inp)

        assert result is created_deployment
        call_arg: Deployment = deployment_repo.create.call_args[0][0]

        ai_snap = call_arg.ai_application_snapshot
        assert "models" in ai_snap
        assert "rules" in ai_snap
        assert len(ai_snap["models"]) == 1
        assert len(ai_snap["rules"]) == 1
        assert ai_snap["models"][0]["name"] == model.name
        assert ai_snap["rules"][0]["name"] == rule.name

        site_snap = call_arg.site_snapshot
        assert "camera_configs" in site_snap
        assert len(site_snap["camera_configs"]) == 1
        cc_snap = site_snap["camera_configs"][0]
        assert "scene_configs" in cc_snap
        assert len(cc_snap["scene_configs"]) == 1

    def test_create_raises_when_project_not_found(self):
        repos = _make_service()
        service = repos[0]
        project_repo = repos[2]
        project_repo.get.return_value = None

        inp = CreateDeploymentInput(
            project_id=uuid4(),
            ai_application_ref=uuid4(),
            site_ref=uuid4(),
            owner="sys",
            effective_date=_now(),
        )
        with pytest.raises(NotFoundError, match="Project"):
            service.create(inp)

    def test_create_raises_when_ai_application_not_found(self):
        repos = _make_service()
        service = repos[0]
        project_repo = repos[2]
        ai_application_repo = repos[3]

        project_repo.get.return_value = _make_project()
        ai_application_repo.get.return_value = None

        inp = CreateDeploymentInput(
            project_id=uuid4(),
            ai_application_ref=uuid4(),
            site_ref=uuid4(),
            owner="sys",
            effective_date=_now(),
        )
        with pytest.raises(NotFoundError, match="AIApplication"):
            service.create(inp)

    def test_create_raises_when_site_not_found(self):
        repos = _make_service()
        service = repos[0]
        project_repo = repos[2]
        ai_application_repo = repos[3]
        model_repo = repos[4]
        rule_repo = repos[5]
        site_repo = repos[6]

        project_repo.get.return_value = _make_project()
        ai_app = _make_ai_app()
        ai_application_repo.get.return_value = ai_app
        model_repo.list.return_value = []
        rule_repo.list.return_value = []
        site_repo.get.return_value = None

        inp = CreateDeploymentInput(
            project_id=uuid4(),
            ai_application_ref=ai_app.id,
            site_ref=uuid4(),
            owner="sys",
            effective_date=_now(),
        )
        with pytest.raises(NotFoundError, match="Site"):
            service.create(inp)

    def test_create_raises_on_missing_owner(self):
        repos = _make_service()
        service = repos[0]
        inp = CreateDeploymentInput(
            project_id=uuid4(),
            ai_application_ref=uuid4(),
            site_ref=uuid4(),
            owner="",
            effective_date=_now(),
        )
        with pytest.raises(ValidationError, match="owner"):
            service.create(inp)

    def test_create_initial_status_is_pending(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]
        project_repo = repos[2]
        ai_application_repo = repos[3]
        model_repo = repos[4]
        rule_repo = repos[5]
        site_repo = repos[6]
        camera_config_repo = repos[7]

        project = _make_project()
        ai_app = _make_ai_app()
        site = _make_site()
        project_repo.get.return_value = project
        ai_application_repo.get.return_value = ai_app
        model_repo.list.return_value = []
        rule_repo.list.return_value = []
        site_repo.get.return_value = site
        camera_config_repo.list.return_value = []
        created = _make_deployment(status="pending")
        deployment_repo.create.return_value = created

        service.create(
            CreateDeploymentInput(
                project_id=project.id,
                ai_application_ref=ai_app.id,
                site_ref=site.id,
                owner="sys",
                effective_date=_now(),
            )
        )
        call_arg: Deployment = deployment_repo.create.call_args[0][0]
        assert call_arg.status == "pending"


# ---------------------------------------------------------------------------
# activate / deactivate
# ---------------------------------------------------------------------------


class TestDeploymentServiceLifecycle:
    def test_activate_pending_deployment(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="pending", version=1)
        deployment_repo.get.return_value = dep
        deployment_repo.update.return_value = dep

        service.activate(dep.id, expected_version=1)

        updated: Deployment = deployment_repo.update.call_args[0][0]
        assert updated.status == "active"
        assert updated.is_active is True
        assert updated.version == 2

    def test_activate_raises_on_version_mismatch(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="pending", version=3)
        deployment_repo.get.return_value = dep

        with pytest.raises(OptimisticLockError):
            service.activate(dep.id, expected_version=1)

    def test_activate_raises_on_wrong_status(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="archived", version=1)
        deployment_repo.get.return_value = dep

        with pytest.raises(ConflictError):
            service.activate(dep.id, expected_version=1)

    def test_deactivate_active_deployment(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="active", version=2)
        deployment_repo.get.return_value = dep
        deployment_repo.update.return_value = dep

        service.deactivate(dep.id, expected_version=2)

        updated: Deployment = deployment_repo.update.call_args[0][0]
        assert updated.status == "inactive"
        assert updated.is_active is False

    def test_deactivate_raises_on_non_active_deployment(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="pending", version=1)
        deployment_repo.get.return_value = dep

        with pytest.raises(ConflictError):
            service.deactivate(dep.id, expected_version=1)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDeploymentServiceDelete:
    def test_delete_raises_when_active(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="active")
        deployment_repo.get.return_value = dep

        with pytest.raises(ConflictError, match="active"):
            service.delete(dep.id)

        deployment_repo.delete.assert_not_called()

    def test_delete_succeeds_when_inactive(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="inactive")
        deployment_repo.get.return_value = dep

        service.delete(dep.id)

        deployment_repo.delete.assert_called_once_with(dep.id)

    def test_delete_succeeds_when_pending(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        dep = _make_deployment(status="pending")
        deployment_repo.get.return_value = dep

        service.delete(dep.id)

        deployment_repo.delete.assert_called_once_with(dep.id)

    def test_delete_raises_not_found(self):
        repos = _make_service()
        service = repos[0]
        deployment_repo = repos[1]

        deployment_repo.get.return_value = None

        with pytest.raises(NotFoundError):
            service.delete(uuid4())
