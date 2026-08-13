from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID


@dataclass
class Project:
    id: UUID
    name: str
    owner: str
    effective_date: datetime
    description: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Site:
    id: UUID
    project_id: UUID
    name: str
    owner: str
    effective_date: datetime
    location: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class CameraConfig:
    id: UUID
    site_id: UUID
    name: str
    owner: str
    effective_date: datetime
    rtsp_url: Optional[str] = None
    credentials: Optional[dict[str, Any]] = None
    resolution: Optional[dict[str, Any]] = None
    capabilities: Optional[dict[str, Any]] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AIApplication:
    id: UUID
    project_id: UUID
    name: str
    owner: str
    effective_date: datetime
    description: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Model:
    id: UUID
    ai_application_id: UUID
    name: str
    owner: str
    effective_date: datetime
    model_type: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Rule:
    id: UUID
    ai_application_id: UUID
    name: str
    owner: str
    effective_date: datetime
    rule_type: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SceneConfig:
    id: UUID
    camera_config_id: UUID
    name: str
    owner: str
    effective_date: datetime
    rois: Optional[dict[str, Any]] = None
    zones: Optional[dict[str, Any]] = None
    ground_plane: Optional[dict[str, Any]] = None
    privacy_masks: Optional[dict[str, Any]] = None
    calibration: Optional[dict[str, Any]] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class User:
    id: UUID
    username: str
    email: str
    owner: str
    effective_date: datetime
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ProjectUser:
    project_id: UUID
    user_id: UUID
    role: str
    owner: str
    effective_date: datetime
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FeatureFlag:
    id: UUID
    name: str
    owner: str
    effective_date: datetime
    description: Optional[str] = None
    is_enabled: bool = False
    target_type: str = "global"
    target_id: Optional[UUID] = None
    status: str = "active"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Deployment:
    id: UUID
    project_id: UUID
    ai_application_snapshot: dict[str, Any]
    site_snapshot: dict[str, Any]
    owner: str
    effective_date: datetime
    ai_application_ref: Optional[UUID] = None
    site_ref: Optional[UUID] = None
    status: str = "pending"
    is_active: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
