-- V001__create_configuration_platform_schema.sql
-- Configuration Platform — initial schema
-- Requires PostgreSQL 13+ (gen_random_uuid() is built-in; no pgcrypto needed)
--
-- All entity tables carry the ConfigurationObject contract columns:
--   version          INTEGER      NOT NULL DEFAULT 1   (increment atomically on each mutation)
--   owner            VARCHAR(255) NOT NULL             (platform or user identity)
--   effective_date   TIMESTAMPTZ  NOT NULL             (when this version becomes authoritative)
--   created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
--   updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
--
-- SECURITY (R-005): camera_configs.credentials must store only a reference token
-- or encrypted blob — never plaintext credentials. Use a secrets manager or
-- column-level encryption at the application layer.
--
-- CONCURRENCY (R-006): The repository layer must increment `version` atomically:
--   UPDATE ... SET version = version + 1 WHERE id = :id AND version = :expected_version
-- This enforces optimistic concurrency and prevents duplicate version numbers.
--
-- SNAPSHOTS (R-004): deployments.ai_application_snapshot and site_snapshot must
-- capture the full nested configuration tree (models, rules, scene_configs) at
-- deploy time. Active deployments are isolated from upstream configuration changes.

CREATE SCHEMA IF NOT EXISTS configuration;

-- ============================================================
-- projects
-- ============================================================
CREATE TABLE configuration.projects (
    id             UUID         NOT NULL DEFAULT gen_random_uuid(),
    name           VARCHAR(255) NOT NULL,
    description    TEXT,
    status         VARCHAR(50)  NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'archived')),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    version        INTEGER      NOT NULL DEFAULT 1,
    owner          VARCHAR(255) NOT NULL,
    effective_date TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT projects_pkey PRIMARY KEY (id)
);

-- ============================================================
-- sites
-- ============================================================
CREATE TABLE configuration.sites (
    id             UUID         NOT NULL DEFAULT gen_random_uuid(),
    project_id     UUID         NOT NULL,
    name           VARCHAR(255) NOT NULL,
    location       TEXT,
    status         VARCHAR(50)  NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'archived')),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    version        INTEGER      NOT NULL DEFAULT 1,
    owner          VARCHAR(255) NOT NULL,
    effective_date TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT sites_pkey PRIMARY KEY (id),
    CONSTRAINT sites_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES configuration.projects (id) ON DELETE RESTRICT
);

CREATE INDEX idx_sites_project_id ON configuration.sites (project_id);

-- ============================================================
-- camera_configs
-- ============================================================
-- SECURITY (R-005): credentials must store only a reference token or encrypted
-- blob — never plaintext credentials.
CREATE TABLE configuration.camera_configs (
    id             UUID         NOT NULL DEFAULT gen_random_uuid(),
    site_id        UUID         NOT NULL,
    name           VARCHAR(255) NOT NULL,
    rtsp_url       TEXT,
    credentials    JSONB,
    resolution     JSONB,
    capabilities   JSONB,
    status         VARCHAR(50)  NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'archived')),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    version        INTEGER      NOT NULL DEFAULT 1,
    owner          VARCHAR(255) NOT NULL,
    effective_date TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT camera_configs_pkey PRIMARY KEY (id),
    CONSTRAINT camera_configs_site_id_fkey
        FOREIGN KEY (site_id) REFERENCES configuration.sites (id) ON DELETE RESTRICT
);

CREATE INDEX idx_camera_configs_site_id ON configuration.camera_configs (site_id);

-- ============================================================
-- ai_applications
-- ============================================================
CREATE TABLE configuration.ai_applications (
    id             UUID         NOT NULL DEFAULT gen_random_uuid(),
    project_id     UUID         NOT NULL,
    name           VARCHAR(255) NOT NULL,
    description    TEXT,
    status         VARCHAR(50)  NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'archived')),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    version        INTEGER      NOT NULL DEFAULT 1,
    owner          VARCHAR(255) NOT NULL,
    effective_date TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT ai_applications_pkey PRIMARY KEY (id),
    CONSTRAINT ai_applications_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES configuration.projects (id) ON DELETE RESTRICT
);

CREATE INDEX idx_ai_applications_project_id ON configuration.ai_applications (project_id);

-- ============================================================
-- models
-- ============================================================
CREATE TABLE configuration.models (
    id                UUID         NOT NULL DEFAULT gen_random_uuid(),
    ai_application_id UUID         NOT NULL,
    name              VARCHAR(255) NOT NULL,
    model_type        VARCHAR(100),
    parameters        JSONB,
    status            VARCHAR(50)  NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active', 'inactive', 'archived')),
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    version           INTEGER      NOT NULL DEFAULT 1,
    owner             VARCHAR(255) NOT NULL,
    effective_date    TIMESTAMPTZ  NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT models_pkey PRIMARY KEY (id),
    CONSTRAINT models_ai_application_id_fkey
        FOREIGN KEY (ai_application_id) REFERENCES configuration.ai_applications (id) ON DELETE RESTRICT
);

CREATE INDEX idx_models_ai_application_id ON configuration.models (ai_application_id);

-- ============================================================
-- rules
-- ============================================================
CREATE TABLE configuration.rules (
    id                UUID         NOT NULL DEFAULT gen_random_uuid(),
    ai_application_id UUID         NOT NULL,
    name              VARCHAR(255) NOT NULL,
    rule_type         VARCHAR(100),
    parameters        JSONB,
    status            VARCHAR(50)  NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active', 'inactive', 'archived')),
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    version           INTEGER      NOT NULL DEFAULT 1,
    owner             VARCHAR(255) NOT NULL,
    effective_date    TIMESTAMPTZ  NOT NULL,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT rules_pkey PRIMARY KEY (id),
    CONSTRAINT rules_ai_application_id_fkey
        FOREIGN KEY (ai_application_id) REFERENCES configuration.ai_applications (id) ON DELETE RESTRICT
);

CREATE INDEX idx_rules_ai_application_id ON configuration.rules (ai_application_id);

-- ============================================================
-- scene_configs
-- ============================================================
CREATE TABLE configuration.scene_configs (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    camera_config_id UUID         NOT NULL,
    name             VARCHAR(255) NOT NULL,
    rois             JSONB,
    zones            JSONB,
    ground_plane     JSONB,
    privacy_masks    JSONB,
    calibration      JSONB,
    status           VARCHAR(50)  NOT NULL DEFAULT 'active'
                         CHECK (status IN ('active', 'inactive', 'archived')),
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    version          INTEGER      NOT NULL DEFAULT 1,
    owner            VARCHAR(255) NOT NULL,
    effective_date   TIMESTAMPTZ  NOT NULL,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT scene_configs_pkey PRIMARY KEY (id),
    CONSTRAINT scene_configs_camera_config_id_fkey
        FOREIGN KEY (camera_config_id) REFERENCES configuration.camera_configs (id) ON DELETE RESTRICT
);

CREATE INDEX idx_scene_configs_camera_config_id ON configuration.scene_configs (camera_config_id);

-- ============================================================
-- users
-- ============================================================
CREATE TABLE configuration.users (
    id             UUID         NOT NULL DEFAULT gen_random_uuid(),
    username       VARCHAR(255) NOT NULL,
    email          VARCHAR(255) NOT NULL,
    status         VARCHAR(50)  NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'suspended')),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    version        INTEGER      NOT NULL DEFAULT 1,
    owner          VARCHAR(255) NOT NULL,
    effective_date TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_username_key UNIQUE (username),
    CONSTRAINT users_email_key UNIQUE (email)
);

-- ============================================================
-- project_users (join table — composite PK, no separate UUID id)
-- ============================================================
CREATE TABLE configuration.project_users (
    project_id     UUID         NOT NULL,
    user_id        UUID         NOT NULL,
    role           VARCHAR(100) NOT NULL
                       CHECK (role IN ('owner', 'admin', 'operator', 'viewer')),
    version        INTEGER      NOT NULL DEFAULT 1,
    owner          VARCHAR(255) NOT NULL,
    effective_date TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT project_users_pkey PRIMARY KEY (project_id, user_id),
    CONSTRAINT project_users_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES configuration.projects (id) ON DELETE RESTRICT,
    CONSTRAINT project_users_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES configuration.users (id) ON DELETE RESTRICT
);

-- project_id is the leading key of the composite PK index — no separate index needed.
CREATE INDEX idx_project_users_user_id ON configuration.project_users (user_id);

-- ============================================================
-- feature_flags
-- ============================================================
CREATE TABLE configuration.feature_flags (
    id             UUID         NOT NULL DEFAULT gen_random_uuid(),
    name           VARCHAR(255) NOT NULL,
    description    TEXT,
    is_enabled     BOOLEAN      NOT NULL DEFAULT FALSE,
    target_type    VARCHAR(100) NOT NULL DEFAULT 'global'
                       CHECK (target_type IN ('global', 'project', 'user')),
    target_id      UUID,
    status         VARCHAR(50)  NOT NULL DEFAULT 'active'
                       CHECK (status IN ('active', 'inactive', 'archived')),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    version        INTEGER      NOT NULL DEFAULT 1,
    owner          VARCHAR(255) NOT NULL,
    effective_date TIMESTAMPTZ  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT feature_flags_pkey PRIMARY KEY (id),
    CONSTRAINT feature_flags_name_key UNIQUE (name)
);

-- ============================================================
-- deployments
-- ============================================================
-- ai_application_ref and site_ref are soft traceability references — no FK
-- constraints. Snapshot isolation (ai_application_snapshot, site_snapshot) is
-- the authoritative mechanism: active deployments are fully decoupled from
-- upstream configuration changes (R-004).
CREATE TABLE configuration.deployments (
    id                      UUID         NOT NULL DEFAULT gen_random_uuid(),
    project_id              UUID         NOT NULL,
    ai_application_ref      UUID,
    site_ref                UUID,
    ai_application_snapshot JSONB        NOT NULL,
    site_snapshot           JSONB        NOT NULL,
    status                  VARCHAR(50)  NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending', 'active', 'inactive', 'failed', 'archived')),
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    version                 INTEGER      NOT NULL DEFAULT 1,
    owner                   VARCHAR(255) NOT NULL,
    effective_date          TIMESTAMPTZ  NOT NULL,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT deployments_pkey PRIMARY KEY (id),
    CONSTRAINT deployments_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES configuration.projects (id) ON DELETE RESTRICT
);

CREATE INDEX idx_deployments_project_id ON configuration.deployments (project_id);
