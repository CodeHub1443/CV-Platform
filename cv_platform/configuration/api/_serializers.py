"""Serializers: domain models → ConfigurationObject contract dicts."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from cv_platform.configuration.domain.models import (
    AIApplication,
    CameraConfig,
    Deployment,
    FeatureFlag,
    Model,
    Project,
    ProjectUser,
    Rule,
    SceneConfig,
    Site,
    User,
)
from cv_platform.shared.api_core import configuration_object


def _uuid(v: UUID | None) -> str | None:
    return str(v) if v is not None else None


def _dt(v: datetime | None) -> str | None:
    return v.isoformat() if v is not None else None


def serialize_project(p: Project) -> dict[str, Any]:
    return configuration_object(
        object_type="Project",
        version=p.version,
        owner=p.owner,
        parameters={
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "created_at": _dt(p.created_at),
            "updated_at": _dt(p.updated_at),
        },
        validation={"is_active": p.is_active, "status": p.status},
        effective_date=p.effective_date,
    )


def serialize_site(s: Site) -> dict[str, Any]:
    return configuration_object(
        object_type="Site",
        version=s.version,
        owner=s.owner,
        parameters={
            "id": str(s.id),
            "project_id": str(s.project_id),
            "name": s.name,
            "location": s.location,
            "created_at": _dt(s.created_at),
            "updated_at": _dt(s.updated_at),
        },
        validation={"is_active": s.is_active, "status": s.status},
        effective_date=s.effective_date,
    )


def serialize_camera_config(cc: CameraConfig) -> dict[str, Any]:
    return configuration_object(
        object_type="CameraConfig",
        version=cc.version,
        owner=cc.owner,
        parameters={
            "id": str(cc.id),
            "site_id": str(cc.site_id),
            "name": cc.name,
            "rtsp_url": cc.rtsp_url,
            "credentials": cc.credentials,
            "resolution": cc.resolution,
            "capabilities": cc.capabilities,
            "created_at": _dt(cc.created_at),
            "updated_at": _dt(cc.updated_at),
        },
        validation={"is_active": cc.is_active, "status": cc.status},
        effective_date=cc.effective_date,
    )


def serialize_ai_application(a: AIApplication) -> dict[str, Any]:
    return configuration_object(
        object_type="AIApplication",
        version=a.version,
        owner=a.owner,
        parameters={
            "id": str(a.id),
            "project_id": str(a.project_id),
            "name": a.name,
            "description": a.description,
            "created_at": _dt(a.created_at),
            "updated_at": _dt(a.updated_at),
        },
        validation={"is_active": a.is_active, "status": a.status},
        effective_date=a.effective_date,
    )


def serialize_model(m: Model) -> dict[str, Any]:
    return configuration_object(
        object_type="Model",
        version=m.version,
        owner=m.owner,
        parameters={
            "id": str(m.id),
            "ai_application_id": str(m.ai_application_id),
            "name": m.name,
            "model_type": m.model_type,
            "parameters": m.parameters,
            "created_at": _dt(m.created_at),
            "updated_at": _dt(m.updated_at),
        },
        validation={"is_active": m.is_active, "status": m.status},
        effective_date=m.effective_date,
    )


def serialize_rule(r: Rule) -> dict[str, Any]:
    return configuration_object(
        object_type="Rule",
        version=r.version,
        owner=r.owner,
        parameters={
            "id": str(r.id),
            "ai_application_id": str(r.ai_application_id),
            "name": r.name,
            "rule_type": r.rule_type,
            "parameters": r.parameters,
            "created_at": _dt(r.created_at),
            "updated_at": _dt(r.updated_at),
        },
        validation={"is_active": r.is_active, "status": r.status},
        effective_date=r.effective_date,
    )


def serialize_scene_config(sc: SceneConfig) -> dict[str, Any]:
    return configuration_object(
        object_type="SceneConfig",
        version=sc.version,
        owner=sc.owner,
        parameters={
            "id": str(sc.id),
            "camera_config_id": str(sc.camera_config_id),
            "name": sc.name,
            "rois": sc.rois,
            "zones": sc.zones,
            "ground_plane": sc.ground_plane,
            "privacy_masks": sc.privacy_masks,
            "calibration": sc.calibration,
            "created_at": _dt(sc.created_at),
            "updated_at": _dt(sc.updated_at),
        },
        validation={"is_active": sc.is_active, "status": sc.status},
        effective_date=sc.effective_date,
    )


def serialize_user(u: User) -> dict[str, Any]:
    return configuration_object(
        object_type="User",
        version=u.version,
        owner=u.owner,
        parameters={
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "created_at": _dt(u.created_at),
            "updated_at": _dt(u.updated_at),
        },
        validation={"is_active": u.is_active, "status": u.status},
        effective_date=u.effective_date,
    )


def serialize_feature_flag(ff: FeatureFlag) -> dict[str, Any]:
    return configuration_object(
        object_type="FeatureFlag",
        version=ff.version,
        owner=ff.owner,
        parameters={
            "id": str(ff.id),
            "name": ff.name,
            "description": ff.description,
            "is_enabled": ff.is_enabled,
            "target_type": ff.target_type,
            "target_id": _uuid(ff.target_id),
            "created_at": _dt(ff.created_at),
            "updated_at": _dt(ff.updated_at),
        },
        validation={"is_active": ff.is_active, "status": ff.status},
        effective_date=ff.effective_date,
    )


def serialize_deployment(d: Deployment) -> dict[str, Any]:
    return configuration_object(
        object_type="Deployment",
        version=d.version,
        owner=d.owner,
        parameters={
            "id": str(d.id),
            "project_id": str(d.project_id),
            "ai_application_ref": _uuid(d.ai_application_ref),
            "site_ref": _uuid(d.site_ref),
            "ai_application_snapshot": d.ai_application_snapshot,
            "site_snapshot": d.site_snapshot,
            "created_at": _dt(d.created_at),
            "updated_at": _dt(d.updated_at),
        },
        validation={"is_active": d.is_active, "status": d.status},
        effective_date=d.effective_date,
    )


def serialize_project_user(pu: ProjectUser) -> dict[str, Any]:
    return {
        "object_type": "ProjectUser",
        "version": pu.version,
        "owner": pu.owner,
        "parameters": {
            "project_id": str(pu.project_id),
            "user_id": str(pu.user_id),
            "role": pu.role,
            "created_at": _dt(pu.created_at),
            "updated_at": _dt(pu.updated_at),
        },
        "validation": {},
        "effective_date": pu.effective_date.isoformat(),
    }
