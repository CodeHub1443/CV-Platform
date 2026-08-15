"""Initial schema for the Configuration Platform.

Revision ID: 001
Revises:
Create Date: 2026-08-15
"""
from __future__ import annotations

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id            UUID        PRIMARY KEY,
            name          TEXT        NOT NULL,
            owner         TEXT        NOT NULL,
            effective_date TIMESTAMPTZ NOT NULL,
            description   TEXT,
            status        TEXT        NOT NULL DEFAULT 'active',
            is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
            version       INTEGER     NOT NULL DEFAULT 1,
            created_at    TIMESTAMPTZ,
            updated_at    TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id            UUID        PRIMARY KEY,
            project_id    UUID        NOT NULL REFERENCES projects(id),
            name          TEXT        NOT NULL,
            owner         TEXT        NOT NULL,
            effective_date TIMESTAMPTZ NOT NULL,
            location      TEXT,
            status        TEXT        NOT NULL DEFAULT 'active',
            is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
            version       INTEGER     NOT NULL DEFAULT 1,
            created_at    TIMESTAMPTZ,
            updated_at    TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS camera_configs (
            id            UUID        PRIMARY KEY,
            site_id       UUID        NOT NULL REFERENCES sites(id),
            name          TEXT        NOT NULL,
            owner         TEXT        NOT NULL,
            effective_date TIMESTAMPTZ NOT NULL,
            rtsp_url      TEXT,
            credentials   JSONB,
            resolution    JSONB,
            capabilities  JSONB,
            status        TEXT        NOT NULL DEFAULT 'active',
            is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
            version       INTEGER     NOT NULL DEFAULT 1,
            created_at    TIMESTAMPTZ,
            updated_at    TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_applications (
            id            UUID        PRIMARY KEY,
            project_id    UUID        NOT NULL REFERENCES projects(id),
            name          TEXT        NOT NULL,
            owner         TEXT        NOT NULL,
            effective_date TIMESTAMPTZ NOT NULL,
            description   TEXT,
            status        TEXT        NOT NULL DEFAULT 'active',
            is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
            version       INTEGER     NOT NULL DEFAULT 1,
            created_at    TIMESTAMPTZ,
            updated_at    TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id                  UUID        PRIMARY KEY,
            ai_application_id   UUID        NOT NULL REFERENCES ai_applications(id),
            name                TEXT        NOT NULL,
            owner               TEXT        NOT NULL,
            effective_date      TIMESTAMPTZ NOT NULL,
            model_type          TEXT,
            parameters          JSONB,
            status              TEXT        NOT NULL DEFAULT 'active',
            is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
            version             INTEGER     NOT NULL DEFAULT 1,
            created_at          TIMESTAMPTZ,
            updated_at          TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id                  UUID        PRIMARY KEY,
            ai_application_id   UUID        NOT NULL REFERENCES ai_applications(id),
            name                TEXT        NOT NULL,
            owner               TEXT        NOT NULL,
            effective_date      TIMESTAMPTZ NOT NULL,
            rule_type           TEXT,
            parameters          JSONB,
            status              TEXT        NOT NULL DEFAULT 'active',
            is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
            version             INTEGER     NOT NULL DEFAULT 1,
            created_at          TIMESTAMPTZ,
            updated_at          TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS scene_configs (
            id                UUID        PRIMARY KEY,
            camera_config_id  UUID        NOT NULL REFERENCES camera_configs(id),
            name              TEXT        NOT NULL,
            owner             TEXT        NOT NULL,
            effective_date    TIMESTAMPTZ NOT NULL,
            rois              JSONB,
            zones             JSONB,
            ground_plane      JSONB,
            privacy_masks     JSONB,
            calibration       JSONB,
            status            TEXT        NOT NULL DEFAULT 'active',
            is_active         BOOLEAN     NOT NULL DEFAULT TRUE,
            version           INTEGER     NOT NULL DEFAULT 1,
            created_at        TIMESTAMPTZ,
            updated_at        TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              UUID        PRIMARY KEY,
            username        TEXT        NOT NULL UNIQUE,
            email           TEXT        NOT NULL UNIQUE,
            owner           TEXT        NOT NULL,
            effective_date  TIMESTAMPTZ NOT NULL,
            password_hash   TEXT,
            status          TEXT        NOT NULL DEFAULT 'active',
            is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
            version         INTEGER     NOT NULL DEFAULT 1,
            created_at      TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS project_users (
            project_id      UUID        NOT NULL REFERENCES projects(id),
            user_id         UUID        NOT NULL REFERENCES users(id),
            role            TEXT        NOT NULL,
            owner           TEXT        NOT NULL,
            effective_date  TIMESTAMPTZ NOT NULL,
            version         INTEGER     NOT NULL DEFAULT 1,
            created_at      TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ,
            PRIMARY KEY (project_id, user_id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS feature_flags (
            id              UUID        PRIMARY KEY,
            name            TEXT        NOT NULL UNIQUE,
            owner           TEXT        NOT NULL,
            effective_date  TIMESTAMPTZ NOT NULL,
            description     TEXT,
            is_enabled      BOOLEAN     NOT NULL DEFAULT FALSE,
            target_type     TEXT        NOT NULL DEFAULT 'global',
            target_id       UUID,
            status          TEXT        NOT NULL DEFAULT 'active',
            is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
            version         INTEGER     NOT NULL DEFAULT 1,
            created_at      TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS deployments (
            id                          UUID        PRIMARY KEY,
            project_id                  UUID        NOT NULL REFERENCES projects(id),
            ai_application_ref          UUID        REFERENCES ai_applications(id),
            site_ref                    UUID        REFERENCES sites(id),
            ai_application_snapshot     JSONB       NOT NULL,
            site_snapshot               JSONB       NOT NULL,
            owner                       TEXT        NOT NULL,
            effective_date              TIMESTAMPTZ NOT NULL,
            status                      TEXT        NOT NULL DEFAULT 'pending',
            is_active                   BOOLEAN     NOT NULL DEFAULT TRUE,
            version                     INTEGER     NOT NULL DEFAULT 1,
            created_at                  TIMESTAMPTZ,
            updated_at                  TIMESTAMPTZ
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS deployments")
    op.execute("DROP TABLE IF EXISTS feature_flags")
    op.execute("DROP TABLE IF EXISTS project_users")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS scene_configs")
    op.execute("DROP TABLE IF EXISTS rules")
    op.execute("DROP TABLE IF EXISTS models")
    op.execute("DROP TABLE IF EXISTS ai_applications")
    op.execute("DROP TABLE IF EXISTS camera_configs")
    op.execute("DROP TABLE IF EXISTS sites")
    op.execute("DROP TABLE IF EXISTS projects")
