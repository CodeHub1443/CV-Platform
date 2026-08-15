"""Shared fixtures for repository integration tests.

Requires DATABASE_URL env var pointing to a test PostgreSQL database.
Schema is applied via Alembic before the session starts and torn down afterwards.
Each test wraps its operations in a rolled-back transaction for isolation.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import psycopg2
import psycopg2.extras
import pytest

ROOT = Path(__file__).parents[3]


@pytest.fixture(scope="session")
def db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping repository integration tests")
    return url


@pytest.fixture(scope="session", autouse=True)
def apply_schema(db_url: str) -> None:
    psycopg2.extras.register_uuid()
    from alembic.config import Config
    from alembic import command

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")


@pytest.fixture
def conn(db_url: str):
    c = psycopg2.connect(db_url)
    c.autocommit = False
    yield c
    c.rollback()
    c.close()


def now() -> datetime:
    return datetime.now(timezone.utc)


def make_project_row(conn, **kwargs):
    from cv_platform.configuration.domain.models import Project
    from cv_platform.configuration.repositories.postgres.project_repo import PostgresProjectRepository

    defaults = dict(
        id=uuid4(),
        name="Test Project",
        owner="test_owner",
        effective_date=now(),
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    repo = PostgresProjectRepository(conn)
    return repo.create(Project(**defaults))


def make_site_row(conn, project_id, **kwargs):
    from cv_platform.configuration.domain.models import Site
    from cv_platform.configuration.repositories.postgres.site_repo import PostgresSiteRepository

    defaults = dict(
        id=uuid4(),
        project_id=project_id,
        name="Test Site",
        owner="test_owner",
        effective_date=now(),
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    repo = PostgresSiteRepository(conn)
    return repo.create(Site(**defaults))


def make_camera_config_row(conn, site_id, **kwargs):
    from cv_platform.configuration.domain.models import CameraConfig
    from cv_platform.configuration.repositories.postgres.camera_config_repo import PostgresCameraConfigRepository

    defaults = dict(
        id=uuid4(),
        site_id=site_id,
        name="Camera 1",
        owner="test_owner",
        effective_date=now(),
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    repo = PostgresCameraConfigRepository(conn)
    return repo.create(CameraConfig(**defaults))


def make_ai_application_row(conn, project_id, **kwargs):
    from cv_platform.configuration.domain.models import AIApplication
    from cv_platform.configuration.repositories.postgres.ai_application_repo import PostgresAIApplicationRepository

    defaults = dict(
        id=uuid4(),
        project_id=project_id,
        name="Test App",
        owner="test_owner",
        effective_date=now(),
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    repo = PostgresAIApplicationRepository(conn)
    return repo.create(AIApplication(**defaults))


def make_user_row(conn, **kwargs):
    from cv_platform.configuration.domain.models import User
    from cv_platform.configuration.repositories.postgres.user_repo import PostgresUserRepository

    uid = uuid4()
    defaults = dict(
        id=uid,
        username=f"user_{uid.hex[:8]}",
        email=f"user_{uid.hex[:8]}@example.com",
        owner="test_owner",
        effective_date=now(),
        status="active",
        is_active=True,
        version=1,
    )
    defaults.update(kwargs)
    repo = PostgresUserRepository(conn)
    return repo.create(User(**defaults))
